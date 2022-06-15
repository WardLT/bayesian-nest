"""Connection to the Nest API for extracting HVAC status information"""
from datetime import datetime
from threading import Thread
from pathlib import Path
from enum import Enum
import logging
import json

from google.cloud.pubsub_v1.subscriber.message import Message
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth import jwt
from google.cloud import pubsub_v1
from pydantic import BaseModel, Field

from bayesnest.base import BaseMonitor

logger = logging.getLogger(__name__)

# Configuration from the Device Access Console
project_id = 'TBD'

# Configuration for the subscription thread
sub_name = 'TBD'

# Verify the locations of the credentials paths
_my_path = Path(__file__).parent
user_creds_path = _my_path / 'creds' / 'google-sdm-user.json'
assert user_creds_path.is_file(), 'Follow https://developers.google.com/nest/device-access/get-started to get keys ' \
                                  ' for the account associated with your Nest device,' \
                                  ' store them in a file named creds/google-sdm-user.json'
app_creds_path = _my_path / 'creds' / 'google-sdm-service.json'
assert user_creds_path.is_file(), 'Follow https://developers.google.com/nest/device-access/get-started to get keys' \
                                  ' for your Google API project, and store them in a file named google-sdm-service.json'
pubsub_creds_path = _my_path / 'creds' / 'google-service-acct.json'
assert user_creds_path.is_file(), 'Follow https://developers.google.com/nest/device-access/' \
                                  'api/events#google-cloud-pubsub to create a service account. Save keys to' \
                                  ' a file named google-service-acct.json'


# Create a Google credential object
def _make_creds() -> Credentials:
    """Create a credentials object given the files stored on disk"""
    user_keys = json.loads(user_creds_path.read_text())
    app_keys = json.loads(app_creds_path.read_text())['web']
    return Credentials(None, refresh_token=user_keys['refresh_token'],
                       token_uri=app_keys['token_uri'],
                       client_id=app_keys['client_id'],
                       client_secret=app_keys['client_secret'])


class ThermostatMode(str, Enum):
    """State of the thermostat"""

    OFF = "OFF"
    COOLING = "COOLING"
    HEATING = "HEATING"


class ThermostatSetMode(str, Enum):
    """What mode the thermostat is set to"""

    # TODO (wardlt): Support HEATCOOL, which will require knowing which set point to grab from the Setpoint trait
    OFF = "OFF"
    COOL = "COOL"
    HEAT = "HEAT"


class ThermostatStatus(BaseModel):
    """Description of the state of the thermostat"""

    time: datetime = Field(default_factory=lambda: datetime.utcnow(), description='Time this reading was taken')

    # What the user specified for the thermostat to do
    set_temp: float = Field(..., description='Set point of the thermostat (degC)')
    set_mode: str = Field(..., description='Set mode for the thermostat')

    # What the thermostat is doing
    mode: ThermostatMode = Field(..., description='Set point of the thermostat (degC)')
    fan: bool = Field(..., description='Whether the fan is on')

    # State of the house, as measured by the thermostat
    temp: float = Field(..., description='Ambient temperature of the home (degC)')
    humid: float = Field(..., description='Humidity of the home (%)')

    @classmethod
    def from_nest_status(cls, nest_data: dict) -> 'ThermostatStatus':
        """Create an object from the status returned by the Nest API

        Args:
            nest_data: Data provided by NEST
        """
        nest_data = nest_data['traits']
        return cls(
            set_temp=tuple(nest_data["sdm.devices.traits.ThermostatTemperatureSetpoint"].values())[0],
            set_mode=nest_data["sdm.devices.traits.ThermostatMode"]["mode"],
            mode=nest_data["sdm.devices.traits.ThermostatHvac"]["status"],
            fan=nest_data["sdm.devices.traits.Fan"]["timerMode"] == "ON",
            temp=nest_data["sdm.devices.traits.Temperature"]["ambientTemperatureCelsius"],
            humid=nest_data["sdm.devices.traits.Humidity"]["ambientHumidityPercent"]
        )


class ThermostatMonitor(BaseMonitor):
    """Periodically pull the thermostat state and record it in a CSV file"""

    def __init__(self):
        super().__init__(name='nest', write_frequency=900)

        # Create the service endpoint
        creds = _make_creds()
        self.service = build('smartdevicemanagement', 'v1', credentials=creds)

        # If needed, determine the device information
        self.device_name = self._find_device()
        logger.info('Connected to service and found the desired device')

        # Create a thread that watches the pubsub channel for events
        pubsub_creds = jwt.Credentials.from_service_account_file(
            pubsub_creds_path,
            audience="https://pubsub.googleapis.com/google.pubsub.v1.Subscriber"
        )
        subscriber_client = pubsub_v1.SubscriberClient(credentials=pubsub_creds)

        def callback(message: Message):
            """Check if it is a thermostate event change, then trigger an update"""
            # Load the data as JSON
            data = json.loads(message.data)

            # Get the trait that was updated
            traits = [t.split('.')[-1] for t in data['resourceUpdate']['traits']]
            logger.debug(f'Received a update on the following traits: {traits}')
            allowed_traits = ['ThermostatHvac', 'ThermostatMode', 'ThermostatTemperatureSetpoint']
            if any(t in allowed_traits for t in traits):
                logger.info('Received a update the HVAC status.')
                status = self.get_log_record()
                self.write_log_line(status)

            # Acknowledge that we created it
            message.ack()

        def _infinite_watch():
            """Process events until"""
            logger.info(f'Started subscription thread to {sub_name}')
            while True:
                future = subscriber_client.subscribe(
                    subscription=sub_name,
                    callback=callback
                )
                try:
                    future.result()
                except KeyboardInterrupt:
                    future.cancel()
                    break

        thr = Thread(target=_infinite_watch, daemon=True, name='nestevents')
        thr.start()

    def _find_device(self) -> str:
        """Find the device associated with the provided credentials

        Returns:
            Name of the thermostat
        """
        result = self.service.enterprises().devices().list(parent=f'enterprises/{project_id}').execute()
        assert len(result['devices']) == 1, 'We only support exactly one device in your account, for now'
        return result['devices'][0]['name']

    def get_log_record(self) -> ThermostatStatus:
        """Get the status of the thermostat

        Returns:
            Current status of the thermostat
        """
        result = self.service.enterprises().devices().get(name=self.device_name).execute()
        logger.debug('Received a result from the service')

        # Convert it to the desired format
        return ThermostatStatus.from_nest_status(result)
