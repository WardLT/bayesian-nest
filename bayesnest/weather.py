"""Connection to OpenWeather for accessing weather information"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
import requests

from bayesnest.base import BaseMonitor

# API key for OpenWeather API
_api_key = 'TBD'

# Lat-lon of the structure of interest
lat, lon = (0, 0)


class WeatherRecord(BaseModel):
    """Record for the weather status"""

    time: datetime = Field(..., description='Time this reading was taken (UTC)')

    # Basic information
    condition_id: int = Field(..., description='Weather condition summary.'
                                               ' See https://openweathermap.org/weather-conditions')
    condition: str = Field(..., description='Human language description of weather')

    # Temperature-related fields
    temp: float = Field(..., description='Temperature (degC)')
    feels_like: float = Field(..., description='Temperature accounting for human perception (degC)')

    # Atmosphere-related fields
    humidity: float = Field(..., description='Humidity (%)')
    pressure: float = Field(..., description='Atmospheric pressure (hPa)')

    # Wind-related
    wind_speed: float = Field(..., description='Wind speed (m/s)')
    wind_dir: float = Field(..., description='Wind direction (degrees, meteorological)')
    wind_gust: Optional[float] = Field(..., description='Wind gust (m/s)')

    # Cloud and precipitation
    clouds: float = Field(..., description='Cloudiness')
    rain_1h: float = Field(..., description='Rain in last 1h (mm)')
    rain_3h: float = Field(..., description='Rain in last 3h (mm)')
    snow_1h: float = Field(..., description='Snow in last 1h (mm)')
    snow_3h: float = Field(..., description='Snow in last 3h (mm)')

    # Solar-related
    sunrise: datetime = Field(..., description='Sunset time (UTC)')
    sunset: datetime = Field(..., description='Sunset time (UTC)')

    @classmethod
    def from_openweather_record(cls, data: dict) -> 'WeatherRecord':
        """Create a data object from a JSON response of OpenWeather

        Args:
            data: Response from OpenWeather
        Returns:
            Record parsed into our format
        """

        return cls(
            time=data['dt'],
            condition_id=data['weather'][0]['id'],
            condition=data['weather'][0]['description'],
            temp=data['main']['temp'],
            feels_like=data['main']['feels_like'],
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            wind_speed=data['wind']['speed'],
            wind_dir=data['wind']['deg'],
            wind_gust=data['wind'].get('gust', None),
            clouds=data['clouds']['all'],
            rain_1h=data.get('rain', {}).get('1h', 0),
            rain_3h=data.get('rain', {}).get('3h', 0),
            snow_1h=data.get('snow', {}).get('1h', 0),
            snow_3h=data.get('snow', {}).get('3h', 0),
            sunrise=data['sys']['sunrise'],
            sunset=data['sys']['sunset'],
        )


class WeatherMonitor(BaseMonitor):
    """Monitor that records the weather near your home"""

    def __init__(self):
        super().__init__(daemon=True, name='weather', write_frequency=600)

    def get_log_record(self) -> BaseModel:
        """Get the weather data"""
        record = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={_api_key}&units=metric'
        ).json()

        return WeatherRecord.from_openweather_record(record)

