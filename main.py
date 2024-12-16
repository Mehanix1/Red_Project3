from dash import Dash, dcc, html
import plotly.express as px
from dash.dependencies import Input, Output, State
import requests

ACCUWEATHER_API_KEY = 'A3XmBdWeP6NsGSHzUs4NBDuU1W9YeA4j'
GEOCODING_API_KEY = '48bb8cb44b814a34a2d4228089dd4369'

app = Dash(__name__)

cached_city_weather_data = dict()


# функция для получения погоды на 5 дней
def get_5_day_forecast(lat, lon):
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
            url_for_weather = f'https://dataservice.accuweather.com/forecasts/v1/daily/5day/{location}?apikey={ACCUWEATHER_API_KEY}&details=true'
            weather_params = {
                'apikey': ACCUWEATHER_API_KEY,
                'details': 'true'
            }

            weather_response = requests.get(url_for_weather, weather_params)
            if weather_response.status_code == 200:
                weather_data = weather_response.json()
                return weather_data

            return f'Ошибка {response.status_code}'
        return f'Ошибка {response.status_code}'
    except Exception as e:
        return f'Ошибка: {e}'


def get_weather_by_day(weather_data, day):
    try:
        # ключевые параметры прогноза погоды
        temperature = (weather_data['DailyForecasts'][day]['Day']['WetBulbGlobeTemperature']['Average'][
                           'Value'] - 32) / 1.8
        wind_speed = weather_data['DailyForecasts'][day]['Day']['Wind']['Speed']['Value'] / 2.237
        relative_humidity = weather_data['DailyForecasts'][day]['Day']['RelativeHumidity']['Average']
        precipitation_probability = weather_data['DailyForecasts'][day]['Day']['PrecipitationProbability']
        return temperature, wind_speed, relative_humidity, precipitation_probability
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
    html.H1('Прогноз погоды для городов на вашем маршруте'),
    dcc.Input(id='start_city', type='text', placeholder='Начальный город'),
    dcc.Input(id='city_on_route', type='text', placeholder='Промежуточная точка'),
    html.Button('Добавить промежуточную точку маршрута', id='add_city_button', n_clicks=0),
    html.Div(id='cities_list', children=[]),
    dcc.Input(id='end_city', type='text', placeholder='Конечный город'),
    dcc.Dropdown(
        id='days_number_dropdown',
        options=[
            {'label': '1 день', 'value': 0},
            {'label': '2 дня', 'value': 1},
            {'label': '3 дня', 'value': 2},
            {'label': '4 дня', 'value': 3},
            {'label': '5 дней', 'value': 4},
        ],
        value=0,
        multi=False
    ),
    html.Button('Показать прогноз погоды', id='show_button', n_clicks=0),

    dcc.Graph(id='temperature_graph'),
    dcc.Graph(id='wind_speed_graph'),
    dcc.Graph(id='relative_humidity_graph'),
    dcc.Graph(id='precipitation_probability_graph'),
    dcc.Graph(id='temperature_map'),
    dcc.Graph(id='wind_speed_map'),
    dcc.Graph(id='relative_humidity_map'),
    dcc.Graph(id='precipitation_map'),
    html.Div(id='forecast_spreadsheet', children=[])
])


# функция для добавления промежуточной точки маршрута
@app.callback(
    Output('cities_list', 'children'),
    Input('add_city_button', 'n_clicks'),
    State('city_on_route', 'value'),
    State('cities_list', 'children')
)
def add_city(n_clicks, city, cities):
    if n_clicks and city:
        cities.append(html.Div(city))
    return cities


@app.callback(
    Output('temperature_graph', 'figure'),
    Output('wind_speed_graph', 'figure'),
    Output('relative_humidity_graph', 'figure'),
    Output('precipitation_probability_graph', 'figure'),
    Output('temperature_map', 'figure'),
    Output('wind_speed_map', 'figure'),
    Output('relative_humidity_map', 'figure'),
    Output('precipitation_map', 'figure'),
    Input('show_button', 'n_clicks'),
    State('start_city', 'value'),
    State('end_city', 'value'),
    State('cities_list', 'children'),
    State('days_number_dropdown', 'value')
)
def update_weather_forecast(n_clicks, start_city, end_city, cities_list, days):
    try:
        cities_list = [city['props']['children'] for city in cities_list]
        if n_clicks > 0:
            all_cities_on_route = cities_list
            all_cities_on_route.insert(0, start_city)
            all_cities_on_route.append(end_city)

            # Словарь для хранения данных о погоде
            cities_weather_data = {
                'city': [],
                'temperature': [],
                'wind speed': [],
                'relative humidity': [],
                'precipitation probability': [],
                'lat': [],
                'lon': []
            }

            for city in all_cities_on_route:
                if city not in cached_city_weather_data.keys():
                    lat, lon = get_coordinates_by_city(city)
                    weather_data = get_5_day_forecast(lat, lon)
                    cached_city_weather_data[city] = weather_data, lat, lon
                else:
                    weather_data, lat, lon = cached_city_weather_data[city]
                day_weather_data = get_weather_by_day(weather_data, days)
                if isinstance(day_weather_data, tuple):
                    temperature, wind_speed, relative_humidity, precipitation_probability = day_weather_data[0:4]
                    cities_weather_data['city'].append(city)
                    cities_weather_data['temperature'].append(temperature)
                    cities_weather_data['wind speed'].append(wind_speed)
                    cities_weather_data['relative humidity'].append(relative_humidity)
                    cities_weather_data['precipitation probability'].append(precipitation_probability)
                    cities_weather_data['lat'].append(lat)
                    cities_weather_data['lon'].append(lon)

                else:
                    print(day_weather_data)

            temperature_fig = px.line(cities_weather_data, x='city', y='temperature', title='Температура по городам')
            wind_speed_fig = px.bar(cities_weather_data, x='city', y='wind speed', title='Скорость ветра по городам')
            humidity_fig = px.bar(cities_weather_data, x='city', y='relative humidity',
                                  title='Относительная влажность по городам')
            precipitation_fig = px.bar(cities_weather_data, x='city', y='precipitation probability',
                                       title='Вероятность осадков')
            temperature_map = px.scatter_mapbox(
                cities_weather_data,
                lat='lat',
                lon='lon',
                hover_name='city',
                color='temperature',
                size=[t + 100 for t in cities_weather_data['temperature']],
                color_continuous_scale=px.colors.sequential.Plasma,
                size_max=25,
                zoom=3,
                mapbox_style='open-street-map'
            )
            wind_speed_map = px.scatter_mapbox(
                cities_weather_data,
                lat='lat',
                lon='lon',
                hover_name='city',
                color='wind speed',
                size='wind speed',
                color_continuous_scale=px.colors.sequential.Plasma,
                size_max=25,
                zoom=3,
                mapbox_style='open-street-map'
            )
            humidity_map = px.scatter_mapbox(
                cities_weather_data,
                lat='lat',
                lon='lon',
                hover_name='city',
                color='relative humidity',
                size='relative humidity',
                color_continuous_scale=px.colors.sequential.Plasma,
                size_max=25,
                zoom=3,
                mapbox_style='open-street-map'
            )
            precipitation_map = px.scatter_mapbox(
                cities_weather_data,
                lat='lat',
                lon='lon',
                hover_name='city',
                color='precipitation probability',
                size='precipitation probability',
                color_continuous_scale=px.colors.sequential.Plasma,
                size_max=25,
                zoom=3,
                mapbox_style='open-street-map'
            )

            return (temperature_fig, wind_speed_fig, humidity_fig, precipitation_fig, temperature_map, wind_speed_map,
                    humidity_map, precipitation_map)

        return {}, {}, {}, {}, {}, {}, {}, {}
    except Exception as e:
        return f'Ошибка: {e}'


if __name__ == '__main__':
    app.run_server(debug=True)
