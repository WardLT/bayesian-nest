from pathlib import Path
from time import sleep

from bayesnest.thermostat import ThermostatMonitor, ThermostatStatus

thermo = ThermostatMonitor()


def test_init():
    assert thermo.service is not None
    assert thermo.device_name.startswith('enterprise')


def test_get():
    status = thermo.get_log_record()  # Just make sure it completes
    assert isinstance(status, ThermostatStatus)


def test_logging(tmpdir):
    # Get the status for the thermostat
    status = thermo.get_log_record()

    # Write it to a log file
    thermo.log_path = Path(tmpdir / 'log.csv')
    thermo.write_log_line(status)
    assert thermo.log_path.exists()
    assert thermo.log_path.read_text(encoding='utf-8').startswith('time,')

    # Test it in a loop
    thermo.start()
    sleep(10)  # Enough time for it to register
    assert thermo.log_path.read_text(encoding='utf-8').count('\n') == 3
