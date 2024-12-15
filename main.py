from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import requests

ACCUWEATHER_API_KEY = 'wKEpFgKjDiwCabovgjHBQmrqpxH3mHAr'
GEOCODING_API_KEY = '48bb8cb44b814a34a2d4228089dd4369'


def get_weather(lat, lon):
    try:
        # url для запроса для получения локации по координатам
        url_for_location = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
        location_params = {
            'apikey': ACCUWEATHER_API_KEY,
            'q': f'{lat},{lon}'
        }
        response = requests.get(url_for_location, location_params)
        if response.status_code == 200:
            location = response.json()['Key']
            # url для запроса для получения данных о погоде
            url_for_weather = f'http://dataservice.accuweather.com/currentconditions/v1/{location}'
            weather_params = {
                'apikey': ACCUWEATHER_API_KEY,
                'details': 'true'
            }

            weather_response = requests.get(url_for_weather, weather_params)
            if weather_response.status_code == 200:
                weather_data = weather_response.json()

                # ключевые параметры прогноза погоды
                temperature = weather_data[0]['Temperature']['Metric']['Value']
                precipitation_type = weather_data[0]['PrecipitationType']
                wind_speed = weather_data[0]['Wind']['Speed']['Metric']['Value']

                # эти параметры не всегда существуют, поэтому используем get
                relative_humidity = weather_data[0].get('RelativeHumidity', None)
                precipitation_probability = weather_data[0].get('PrecipitationProbability', None)
                return temperature, precipitation_type, wind_speed, relative_humidity, precipitation_probability
            return f'Ошибка {response.status_code}'
        return f'Ошибка {response.status_code}'
    except Exception as e:
        return f'Ошибка: {e}'


# функция для получения типа погоды
def check_bad_weather(temperature, precipitation_type, wind_speed, relative_humidity, precipitation_probability):
    try:
        # считаем погоду хорошей только при данных значениях параметров
        is_good_temperature = 0 <= temperature <= 35
        is_good_precipitation_type = precipitation_type is None
        is_good_wind_speed = wind_speed < 10
        is_good_humidity = relative_humidity is None or 30 <= relative_humidity <= 70
        is_good_precipitation_probability = precipitation_probability is None or precipitation_probability < 30
        # если все показатели погоды хорошие (либо отсутствует информация о них), то возвращаем "Хорошая погода"
        if (is_good_temperature and is_good_precipitation_type and is_good_wind_speed
                and is_good_humidity and is_good_precipitation_probability):
            return 'Хорошая погода'
        return 'Плохая погода'
    except Exception as e:
        return f'Ошибка: {e}'


# функция для получения координат по названию города
def get_coordinates_by_city(city):
    try:
        city_location_url = 'https://api.opencagedata.com/geocode/v1/json'
        params = {
            'q': city,
            'key': GEOCODING_API_KEY,
            'language': 'ru',
            'pretty': 1
        }

        response = requests.get(city_location_url, params)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                lat = data['results'][0]['geometry']['lat']
                lng = data['results'][0]['geometry']['lng']
                return lat, lng
            else:
                return 'Ошибка: город не найден'
        else:
            return 'Ошибка:', response.status_code
    except Exception as e:
        return f'Ошибка {e}'