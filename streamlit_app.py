import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# --- ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="PeRGio Fishing Pro", layout="wide")

def calculate_pergio_score(p_val, p_trend, moon, wind, onshore, clouds):
    score = 0
    # 1. Πίεση (40%)
    if p_val < 1010: score += 20
    elif 1011 <= p_val <= 1017: score += 10
    if p_trend == "falling": score += 20
    # 2. Σελήνη (30%) - Εδώ χρησιμοποιούμε τη φωτεινότητα από το API
    if moon <= 0.15: score += 30
    elif moon >= 0.85: score += 20
    else: score += 10
    # 3. Άνεμος & Αφρουδιά (20%)
    if 3 <= wind <= 5: score += 10
    if onshore: score += 10
    # 4. Συννεφιά (10%)
    if clouds > 50: score += 10
    return score

# --- ΛΗΨΗ ΔΕΔΟΜΕΝΩΝ 5 ΗΜΕΡΩΝ / 3 ΩΡΩΝ ---
def get_forecast(lat, lon, api_key):
    # Το δωρεάν API της OpenWeather δίνει πρόβλεψη 5 ημερών ανά 3 ώρες
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=el"
    res = requests.get(url).json()
    
    forecast_list = []
    prev_pressure = res['list'][0]['main']['pressure']
    
    for item in res['list']:
        curr_pressure = item['main']['pressure']
        trend = "falling" if curr_pressure < prev_pressure else "stable"
        
        # Υπολογισμός Score
        # Σημείωση: Το 5-day forecast δεν δίνει moon phase απευθείας, 
        # χρησιμοποιούμε μια μέση τιμή ή το data από το One Call αν υπάρχει.
        score = calculate_pergio_score(
            curr_pressure, trend, 0.5, item['wind']['speed'], True, item['clouds']['all']
        )
        
        forecast_list.append({
            "Χρόνος": datetime.fromtimestamp(item['dt']).strftime('%d/%m %H:%M'),
            "Score %": score,
            "Πίεση (hPa)": curr_pressure,
            "Άνεμος (m/s)": item['wind']['speed'],
            "Βροχή": item.get('weather', [{}])[0].get('description', 'Καθαρός'),
            "Σύννεφα %": item['clouds']['all']
        })
        prev_pressure = curr_pressure
        
    return pd.DataFrame(forecast_list), res['city']

# --- GUI ---
st.title("🎣 PeRGio Fishing Pro: 5-Day Detail")

# Χάρτης και Επιλογή
m = folium.Map(location=[37.98, 23.72], zoom_start=7)
m.add_child(folium.LatLngPopup())
map_output = st_folium(m, height=300, width=None)

lat, lon = 37.98, 23.72
if map_output['last_clicked']:
    lat, lon = map_output['last_clicked']['lat'], map_output['last_clicked']['lng']

if st.button("Ανάλυση Εβδομάδας (Ανά 3 Ώρες)"):
    api_key = st.secrets["OPENWEATHER_API_KEY"]
    df, city_info = get_forecast(lat, lon, api_key)
    
    # 1. Ανατολή & Δύση
    sunrise = datetime.fromtimestamp(city_info['sunrise']).strftime('%H:%M')
    sunset = datetime.fromtimestamp(city_info['sunset']).strftime('%H:%M')
    
    st.info(f"☀️ Ανατολή: {sunrise} | 🌙 Δύση: {sunset} | 📍 Περιοχή: {city_info['name']}")
    
    # 2. Γράφημα Score
    st.subheader("Πρόβλεψη PeRGio Score")
    st.line_chart(df.set_index("Χρόνος")["Score %"])
    
    # 3. Αναλυτικός Πίνακας (Statistics)
    st.subheader("Αναλυτικά Στατιστικά (Ανά 3 Ώρες)")
    
    # Χρωματική σήμανση για τη βροχή και το σκορ
    def highlight_cells(val):
        if isinstance(val, int) and val >= 80: return 'background-color: #2ecc71'
        if "βροχή" in str(val).lower(): return 'background-color: #3498db'
        return ''

    st.dataframe(df.style.applymap(highlight_cells))
    
