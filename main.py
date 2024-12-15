from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import requests

ACCUWEATHER_API_KEY = 'wKEpFgKjDiwCabovgjHBQmrqpxH3mHAr'
GEOCODING_API_KEY = '48bb8cb44b814a34a2d4228089dd4369'

app = Dash(__name__)


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
        print(temperature, precipitation_type, wind_speed, relative_humidity, precipitation_probability)
        # считаем погоду хорошей только при данных значениях параметров
        is_good_temperature = -5 <= temperature <= 35
        is_good_precipitation_type = precipitation_type is None
        is_good_wind_speed = wind_speed < 15
        is_good_humidity = relative_humidity is None or 20 <= relative_humidity <= 90
        is_good_precipitation_probability = precipitation_probability is None or precipitation_probability < 40
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


app.layout = html.Div([
    html.H1('Прогноз погоды'),
    dcc.Input(id='start_city', type='text', placeholder='Начальный город'),
    dcc.Input(id='city_on_route', type='text', placeholder='Промежуточная точка'),
    html.Button('Добавить промежуточную точку маршрута', id='add_city_button', n_clicks=0),
    html.Div(id='waypoints-container', children=[]),
    dcc.Input(id='end_city', type='text', placeholder='Конечный город'),
    dcc.Dropdown(
        id='days_number_dropdown',
        options=[
            {'label': '1 день', 'value': 1},
            {'label': '5 дней', 'value': 5},
        ],
        value=1,
        multi=False
    ),
    html.Button('Показать прогноз погоды', id='show_button', n_clicks=0),

    dcc.Graph(id='temperature_graph'),
    dcc.Graph(id='wind_speed_graph'),
    dcc.Graph(id='relative_humidity_graph'),
    dcc.Graph(id='precipitation_probability_graph'),
    html.Div(id='forecast_spreadsheet', children=[])
])

if __name__ == '__main__':
    app.run_server(debug=True)
