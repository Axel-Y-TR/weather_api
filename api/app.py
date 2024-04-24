import json
import time
import logging
from datetime import datetime
import requests
from flask import Flask
from pymongo import MongoClient
import threading

app = Flask(__name__)
client = MongoClient('172.20.0.2', 27017)
db = client['weatherdb']

"""
    GET: Appel les données

    Réponse:
        - Succès: Liste des données météorologique
"""
@app.route('/api/weather/ingest', methods=['GET'])
def get_ingest_data():

    weather_data = store_weather_data_in_db()
    return jsonify({"info ":"succes d'ingestion (chargement de données)"}) if weather_data else jsonify({"error": "Aucune donnée météorologique disponible"})


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
    try:
        if 'city' not in db.list_collection_names():
            city_collection = db['city']
            with open('city.json', 'r', encoding='utf-8') as d:
                data = json.load(d)
                for city in data[:5]:  # Import only the first 5 cities
                    city_collection.insert_one(city)
        weather_collection = db['weather']
        city_collection = db['city']
        cursor = city_collection.find()
        for document in cursor:
            coord = document.get('coord')
            if coord:
                lat = coord.get('lat')
                lon = coord.get('lon')
                if lat is not None and lon is not None:
                    weather_data = get_data(lat, lon)
                    logging.info('data', weather_data)
                    
                    if weather_data:
                        weather_record = {
                            "city_id": document['_id'],
                            "name": document['name'],
                            "coord": document['coord'],
                            "temp_min": weather_data['main']['temp_min'],
                            "temp_max": weather_data['main']['temp_max'],
                            "humidity": weather_data['main']['humidity'],
                            "pressure": weather_data['main']['pressure'],
                            "wind_speed": weather_data['wind']['speed'],
                            "insertion_time": datetime.now()
                        }
                        weather_collection.insert_one(weather_record)
                        logging.info(f"{document['name']} - Succès dans la collecte de données")
                    else:
                        logging.info(f"Impossible de récupérer les données météorologiques pour {document['name']}.")
                else:
                    logging.info(f"Le document {document['_id']} ne contient pas de coordonnées valides.")
            else:
                logging.info(f"Le document {document['_id']} ne contient pas de champ 'coord'.")
        return True
        
    except:
        logging.error("Erreur de connexion open whetherAPI")
        return False
from routes import *

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
    # store_weather_data_in_db()

    # Boucle pour appeler toute les minutes
    while True:
        store_weather_data_in_db()
        time.sleep(60)