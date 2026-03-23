import streamlit as st
import requests
import pandas as pd
from streamlit_folium import st_folium
import folium

# --- ΡΥΘΜΙΣΕΙΣ & ΠΑΡΑΜΕΤΡΟΙ ---
st.set_page_config(page_title="PeRGio Fishing Master", layout="wide")

def calculate_pergio_score(p_val, p_trend, moon, wind, onshore, clouds):
    score = 0
    # 1. Βαρομετρική Πίεση (40%)
    if p_val < 1010: score += 20
    elif 1011 <= p_val <= 1017: score += 10
    if p_trend == "falling": score += 20
        
    # 2. Σελήνη (30%) - Απλοποιημένη προσέγγιση φωτεινότητας
    if moon <= 15: score += 30
    elif moon >= 85: score += 20
    elif 40 <= moon <= 60: score += 0
    else: score += 10
        
    # 3. Άνεμος & Αφρουδιά (20%)
    if 3 <= wind <= 5: score += 10
    if onshore: score += 10
        
    # 4. Συννεφιά (10%)
    if clouds > 50: score += 10
    return score

# --- ΣΥΝΑΡΤΗΣΕΙΣ API ---
def get_weather_data(lat, lon, owm_key):
    # API 1: Open-Meteo (No Key)
    res_om = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=surface_pressure,cloudcover").json()
    
    # API 2: OpenWeatherMap (Needs Key from Secrets)
    res_owm = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={owm_key}&units=metric").json()
    
    # Μέσοι Όροι (Reliability Layer)
    avg_press = (res_om['hourly']['surface_pressure'][0] + res_owm['main']['pressure']) / 2
    avg_wind = (res_om['current_weather']['windspeed'] / 3.6 + res_owm['wind']['speed']) / 2
    avg_clouds = (res_om['hourly']['cloudcover'][0] + res_owm['clouds']['all']) / 2
    
    return avg_press, avg_wind, avg_clouds

# --- GUI ---
st.title("🎣 PeRGio Fishing Master (Multi-API)")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 Επιλογή Σημείου")
    m = folium.Map(location=[37.98, 23.72], zoom_start=7)
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=400, width=500)
    
    lat, lon = 37.98, 23.72
    if map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lon = map_data['last_clicked']['lng']
        st.success(f"Επιλέχθηκε: {lat:.4f}, {lon:.4f}")

with col2:
    st.subheader("📊 Ανάλυση & Σκορ")
    if st.button("Λήψη Δεδομένων & Υπολογισμός"):
        try:
            owm_key = st.secrets["OPENWEATHER_API_KEY"]
            p, w, c = get_weather_data(lat, lon, owm_key)
            
            # Εδώ ορίζουμε την τάση ως "σταθερή" για το τρέχον παράδειγμα 
            # (μπορεί να βελτιωθεί με ιστορικά δεδομένα)
            score = calculate_pergio_score(p, "stable", 50, w, True, c)
            
            st.metric("PeRGio Score", f"{score}%")
            st.write(f"🔹 Πίεση: {p:.1f} hPa")
            st.write(f"🔹 Άνεμος: {w:.1f} m/s")
            st.write(f"🔹 Συννεφιά: {c:.0f}%")
            
            if score >= 80: st.success("Χρυσή Ευκαιρία!")
            elif score >= 50: st.info("Καλή Μέρα")
            else: st.warning("Δύσκολες Συνθήκες")
        except Exception as e:
            st.error("Βεβαιωθείτε ότι έχετε προσθέσει το API Key στα Secrets.")

