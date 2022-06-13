from logging.handlers import RotatingFileHandler
import logging
import sys

from bayesnest.thermostat import ThermostatMonitor
from bayesnest.weather import WeatherMonitor


def main():
    """Launch the bot to gather the data and store it to disk"""

    # Define the logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
                        handlers=[RotatingFileHandler('bayesnest.log', mode='a',
                                                      maxBytes=1024 * 1024 * 2,
                                                      backupCount=1),
                                  logging.StreamHandler(sys.stdout)])

    # Launch the threads
    thermo_mon = ThermostatMonitor()
    thermo_mon.start()

    weather_mon = WeatherMonitor()
    weather_mon.start()

    # Wait until they complete
    thermo_mon.join()
