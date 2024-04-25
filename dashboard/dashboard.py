import streamlit as st
import pandas as pd
import json
import requests
import plotly.express as px

st.title('Dashboard Climat et ville')


response = requests.get('http://127.0.0.3:8182/api/weather/all')

# Vérifier si la requête a réussi
if response.status_code == 200:
    # Convertir la réponse en objet JSON
    json_data = response.json()
    
    # Créer un DataFrame à partir de l'objet JSON
    df = pd.DataFrame(json_data)

uniq = set(df['name'])
cities = list(uniq)
cities.append("Toutes les villes")
selected_cities = st.sidebar.multiselect("Sélectionnez une ou plusieurs villes", cities)

# Filtrer le DataFrame en fonction des villes sélectionnées
if "Toutes les villes" in selected_cities:
    selected_city_data = df
else:
    selected_city_data = df[df['name'].isin(selected_cities)]

st.write(df)

fig = px.histogram(selected_city_data, x='name', y='temp_max', histfunc='avg', title='Histogramme de température moyenne par ville')

st.plotly_chart(fig)

select_temp = st.radio("Choisir la température à filtrer", ["min", "max"])

# Slider pour sélectionner la température minimale ou maximale
if select_temp == "min":
    temp = st.slider("Température minimale", min_value=selected_city_data['temp_min'].min(), max_value=selected_city_data['temp_min'].max())
    filtered_df = selected_city_data[selected_city_data['temp_min'] <= temp]
else:
    temp = st.slider("Température maximale", min_value=selected_city_data['temp_max'].min(), max_value=selected_city_data['temp_max'].max())
    filtered_df = selected_city_data[selected_city_data['temp_max'] >= temp]


filtered_df_selected = filtered_df[['name', 'temp_min', 'temp_max','insertion_time']]

# Afficher le DataFrame filtré
st.write(filtered_df_selected)






