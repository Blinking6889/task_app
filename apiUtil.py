import weatherModel
import os

def get_weather_status(location):
    return weatherModel.get_weather(location, os.getenv("OW_KEY"))