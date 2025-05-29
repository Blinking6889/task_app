from dotenv import load_dotenv
import weatherModel
import os

load_dotenv()

def get_weather_status(location):
    return weatherModel.get_weather(location, os.getenv("OW_KEY"))