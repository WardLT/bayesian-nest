from bayesnest.weather import WeatherMonitor

monitor = WeatherMonitor()


def test_retrieve():
    result = monitor.get_log_record()
    print(result)
