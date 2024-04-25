from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import happybase

connection = happybase.Connection('172.20.0.2', port=9090)  # Connexion à HBase


app = Flask(__name__)


############ Helpers ############
def format_weather_data(weather_data):
    """ Formate les données météorologiques."""
    formatted_data = []
    for data in weather_data:
        key = data[0].decode('utf-8')  # Convertir la clé en UTF-8
        value = data[1]  # Récupérer la valeur
        formatted_data.append({
            'id': key,
            'city_name': value.get(b'weather_data:name').decode('utf-8'),  # Utiliser get() pour éviter les erreurs si la clé est absente
            'insertion_time': value.get(b'weather_data:insertion_time').decode('utf-8'),
            'temperature_max': value.get(b'weather_data:temp_max').decode('utf-8'),
            'temperature_min': value.get(b'weather_data:temp_min').decode('utf-8'),
            'humidity': value.get(b'weather_data:humidity').decode('utf-8'),
            'wind_speed': value.get(b'weather_data:wind_speed').decode('utf-8'),

            # Utiliser get() pour éviter les erreurs si la clé est absente
        })
    return formatted_data









def parse_date(date_str):
    """ Analyse une chaîne de caractères représentant une date au format 'jour/mois/année'. """
    try:
        day, month, year = map(int, date_str.split('/'))
        return datetime(year, month, day)
    except ValueError:
        return None






############ Routes ############
@app.route('/api/weather/all', methods=['GET'])
def get_all_weather():
    try:
        table = connection.table('weather_data_table')
        app.logger.info(table)
        weather_data = table.scan()
        app.logger.info(weather_data)
        formatted_data = format_weather_data(weather_data)
        app.logger.info(formatted_data)
        return jsonify(formatted_data) if formatted_data else jsonify({"error": "Aucune donnée météorologique disponible"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather/humidity', methods=['GET'])
def get_weather_by_humidity():
    humidity = request.args.get('humidity', type=int)
    try:
        table = connection.table('weather_data_table')
        weather_data = table.scan(filter="SingleColumnValueFilter('%s', 'humidity', >=, 'binary:%d')" % (column_family, humidity))
        formatted_data = format_weather_data(weather_data)
        return jsonify(formatted_data) if formatted_data else jsonify({"error": "Aucune donnée météorologique disponible pour l'humidité spécifiée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather/humidityBetween', methods=['GET'])
def get_weather_by_humidity_range():
    hum_min = request.args.get('hum_min', type=float)
    hum_max = request.args.get('hum_max', type=float)
    try:
        table = connection.table('weather_data_table')
        weather_data = table.scan(filter="SingleColumnValueFilter('%s', 'humidity', >=, 'binary:%f') AND SingleColumnValueFilter('%s', 'humidity', <=, 'binary:%f')" % (column_family, hum_min, column_family, hum_max))
        formatted_data = format_weather_data(weather_data)
        return jsonify(formatted_data) if formatted_data else jsonify({"error": "Aucune donnée météorologique disponible pour la plage d'humidité spécifiée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather_by_temp_range():
    temp_min = request.args.get('temp_min', type=float)
    temp_max = request.args.get('temp_max', type=float)
    try:
        table = connection.table('weather_data_table')
        weather_data = table.scan(filter="SingleColumnValueFilter('%s', 'temp_min', >=, 'binary:%f') AND SingleColumnValueFilter('%s', 'temp_max', <=, 'binary:%f')" % (column_family, temp_min, column_family, temp_max))
        formatted_data = format_weather_data(weather_data)
        return jsonify(formatted_data) if formatted_data else jsonify({"error": "Aucune donnée météorologique disponible pour la plage de température spécifiée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather/by_name', methods=['GET'])
def get_weather_by_name():
    city_name = request.args.get('name', type=str)
    if not city_name:
        return jsonify({"error": "Le nom de la ville doit être spécifié"}), 400
    try:
        table = connection.table('weather_data_table')
        weather_data = table.scan(filter="SingleColumnValueFilter('%s', 'name', =, 'binary:%s')" % (column_family, city_name))
        formatted_data = format_weather_data(weather_data)
        return jsonify(formatted_data) if formatted_data else jsonify({"error": "Aucune donnée météorologique disponible pour la ville spécifiée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather/by_date', methods=['GET'])
def get_weather_by_date():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Veuillez spécifier une date au format 'jour/mois/année'"}), 400

    date = parse_date(date_str)
    if not date:
        return jsonify({"error": "Format de date invalide. Assurez-vous d'utiliser le format 'jour/mois/année'"}), 400
    
    try:
        table = connection.table('weather_data_table')
        start_date = date.strftime('%Y-%m-%d')
        end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        weather_data = table.scan(row_start=start_date, row_stop=end_date)
        formatted_data = format_weather_data(weather_data)
        return jsonify(formatted_data) if formatted_data else jsonify({"error": "Aucune donnée météorologique disponible pour la date spécifiée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

