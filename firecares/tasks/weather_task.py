from firecares.celery import app
from firecares.weather.models import WeatherWarnings


@app.task(queue='weather-task', rate_limit='15/m')
def collect_weather_noaa_warnings():
    """
    Adds data to the Weather warning table every 15 minutes because it tends to go down every once in a while
    This harvest can take up to 10 minutes to iterate through all warnings
    """
    WeatherWarnings.load_warning_data()
