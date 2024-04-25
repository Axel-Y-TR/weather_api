import json
import time
import logging
from datetime import datetime
import requests
import happybase
from flask import Flask, jsonify
from routes import *

app = Flask(__name__)

connection = happybase.Connection('172.20.0.2', port=9090)  # Connexion à HBase

# Définition de la famille de colonnes pour la table HBase
column_family = 'weather_data'

"""
    GET: Appel les données

    Réponse:
        - Succès: Liste des données météorologique
"""
@app.route('/api/weather/ingest', methods=['GET'])
def get_ingest_data():
    weather_data = store_weather_data_in_db()
    return jsonify({"info": "Succès d'ingestion (chargement de données)"}) if weather_data else jsonify({"error": "Aucune donnée météorologique disponible"})

def get_weather_data(lat, lon, api_key):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "units": 'metric',
        "appid": api_key
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Erreur de connexion:", e)
        return None

def get_data(lat, lon):
    api_key = "74fba207e3c6e53a8e1b95c9457311a8"
    return get_weather_data(lat, lon, api_key)

def store_weather_data_in_db():
    app.logger.info(app)
    try:
        if b'weather_data_table' not in connection.tables():  # Vérification si la table existe
            app.logger.info("La table weather_data_table n'existe pas, création...")
            connection.create_table(
                'weather_data_table',
                {column_family: dict()}  # Spécifiez la famille de colonnes
            )
           

        with connection.table(b'weather_data_table').batch(batch_size=1000) as table:
            # Suite du code pour insérer les données dans la table...
            pass

        with connection.table('weather_data_table').batch(batch_size=1000) as table:  # Accès à la table HBase
            with open('city.json', 'r', encoding='utf-8') as d:
                data = json.load(d)
                for city in data[:5]:  # Import only the first 5 cities
                    coord = city.get('coord')
                    if coord:
                        lat = coord.get('lat')
                        lon = coord.get('lon')
                        if lat is not None and lon is not None:
                            weather_data = get_data(lat, lon)
                           

                            if weather_data:
                                row_key = str(city['id'])
                                table.put(row_key, {
                                    f"{column_family}:name": city['name'],
                                    f"{column_family}:coord": json.dumps(city['coord']),
                                    f"{column_family}:temp_min": str(weather_data['main']['temp_min']),
                                    f"{column_family}:temp_max": str(weather_data['main']['temp_max']),
                                    f"{column_family}:humidity": str(weather_data['main']['humidity']),
                                    f"{column_family}:pressure": str(weather_data['main']['pressure']),
                                    f"{column_family}:wind_speed": str(weather_data['wind']['speed']),
                                    f"{column_family}:insertion_time": str(datetime.now())
                                })
                                app.logger.info("%s - Succès dans la collecte de données", city['name'])
                            else:
                                app.logger.info("Impossible de récupérer les données météorologiques pour %s.", city['name'])
                        else:
                            app.logger.info("La ville %s ne contient pas de coordonnées valides.", city['name'])
                    else:
                        app.logger.info("La ville %s ne contient pas de champ 'coord'.", city['name'])
                    
                

        return True
    except requests.exceptions.RequestException as e:
        app.logger.error("Erreur de connexion à l'API OpenWeatherMap: %s", e)
        return False


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8182)
    # Créer un logger pour l'application Flask
    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)


    # Boucle pour appeler toutes les minutes
    while True:
        store_weather_data_in_db()
        time.sleep(60)
