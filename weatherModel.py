import requests

#GET CITY COORDINATES
def ow_getgeo(key, city):
    app_key = key
    city = city
    ow_geobase = 'http://api.openweathermap.org/geo/1.0/direct'
    ow_params = {'q':city, 'limit': 1, 'appid': app_key}
    data_req = requests.get(ow_geobase, params=ow_params)
    if data_req.status_code == 200:
        try:
            data = data_req.json()
            coordinates = [data[0]['lat'], data[0]['lon']]
            return coordinates
        except:
            return None
    else: 
        return None

#GET WEATHER DATA
def ow_data(key, coordinates):
    ow_params = {'lat':coordinates[0], 'lon': coordinates[1],'units':'imperial','appid': key}
    ow_currbase = f'https://api.openweathermap.org/data/2.5/weather'
    data_req = requests.get(ow_currbase, params=ow_params)
    if data_req.status_code == 200:
        try:
            data = data_req.json()
            w_desc = data['weather'][0]['description']
            w_temp = data['main']['temp']
            return {'clouds': w_desc,'temp': w_temp}
        except:
            return None
    else:
        return 'None'

def get_weather(location, key):
    coordinates = ow_getgeo(key, location)
    if coordinates == None:
        return 'No Data Found'
    else:
        current_data  = ow_data(key, coordinates)
        return current_data