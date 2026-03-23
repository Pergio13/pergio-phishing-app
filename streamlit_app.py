import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import folium
from streamlit_folium import st_folium

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="PeRGio Fishing Pro", layout="wide")

# Λεξικό Μετάφρασης Ημερών
days_translation = {
    "Monday": "Δευτέρα", "Tuesday": "Τρίτη", "Wednesday": "Τετάρτη",
    "Thursday": "Πέμπτη", "Friday": "Παρασκευή", "Saturday": "Σάββατο", "Sunday": "Κυριακή"
}

# --- 2. ΛΟΓΙΚΗ ΥΠΟΛΟΓΙΣΜΟΥ SCORE (VIDALIS LOGIC) ---
def calculate_pergio_score(p_val, p_trend, moon, wind, clouds, description):
    score = 0
    # Βαρομετρική Πίεση (40%)
    if p_val < 1010: score += 20
    elif 1011 <= p_val <= 1017: score += 10
    if p_trend == "falling": score += 20
    
    # Σελήνη (30%) - Default 0.5 (προς το παρόν)
    if moon <= 0.15: score += 30
    elif moon >= 0.85: score += 20
    else: score += 10
    
    # Άνεμος (20%) - Ιδανικά 3-5 m/s
    if 3 <= wind <= 5: score += 20
    
    # Συννεφιά (10%)
    if clouds > 50: score += 10
    
    # Ποινή για βροχή/καταιγίδα
    desc_lower = description.lower()
    if "βροχή" in desc_lower or "καταιγίδα" in desc_lower or "rain" in desc_lower:
        score -= 15
        
    return max(0, score)

# --- 3. ΦΟΡΤΩΣΗ ΜΟΝΙΜΩΝ ΤΟΠΟΘΕΣΙΩΝ ---
def load_places():
    try:
        with open('places.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Αν αποτύχει, επιστρέφει ένα default σημείο
        return {"Πειραιάς": [37.94, 23.64]}

# --- 4. ΚΥΡΙΟ GUI ---
st.title("🎣 PeRGio Fishing Pro")
st.markdown("---")

# Sidebar
saved_places = load_places()
st.sidebar.header("📍 Τα Μέρη μου")
selected_name = st.sidebar.selectbox("Επιλέξτε Σημείο:", list(saved_places.keys()))
lat, lon = saved_places[selected_name]

# Εμφάνιση Χάρτη - ΔΙΟΡΘΩΣΗ TYPEERROR
st.subheader(f"Πρόβλεψη για: {selected_name}")
m = folium.Map(location=[lat, lon], zoom_start=10)
folium.Marker(
    [lat, lon], 
    popup=selected_name, 
    icon=folium.Icon(color='red', icon='anchor', prefix='fa')
).add_to(m)

# Χρήση σταθερού width και height για σταθερότητα
st_folium(m, height=300, width=700, key="fishing_map")

# --- 5. ΛΗΨΗ ΔΕΔΟΜΕΝΩΝ & ΑΝΑΛΥΣΗ ---
if st.button("🚀 Εμφάνιση Ανάλυσης Εβδομάδας"):
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=el"
        res = requests.get(url).json()
        
        if res.get("cod") != "200":
            st.error(f"API Error: {res.get('message')}")
        else:
            days_dict = {}
            prev_p = res['list'][0]['main']['pressure']
            
            for item in res['list']:
                dt = datetime.fromtimestamp(item['dt'])
                eng_day = dt.strftime('%A')
                day_label = f"{days_translation.get(eng_day, eng_day)} {dt.strftime('%d/%m')}"
                
                if day_label not in days_dict:
                    days_dict[day_label] = []
                
                curr_p = item['main']['pressure']
                trend = "falling" if curr_p < prev_p else "stable"
                desc = item['weather'][0]['description']
                
                score = calculate_pergio_score(curr_p, trend, 0.5, item['wind']['speed'], item['clouds']['all'], desc)
                
                days_dict[day_label].append({
                    "ώρα": dt.strftime('%H:%M'),
                    "score": score,
                    "καιρός": desc,
                    "άνεμος": item['wind']['speed'],
                    "πίεση": curr_p
                })
                prev_p = curr_p

            # Εμφάνιση με Expanders
            for day, measurements in days_dict.items():
                with st.expander(f"📅 {day}"):
                    cols = st.columns(len(measurements))
                    for i, m_data in enumerate(measurements):
                        with cols[i]:
                            s = m_data['score']
                            color = "green" if s >= 75 else "orange" if s >= 40 else "red"
                            st.markdown(f"**{m_data['ώρα']}**")
                            st.markdown(f"### :{color}[{s}%]")
                            st.caption(f"{m_data['καιρός']}")
                            st.caption(f"💨 {m_data['άνεμος']}m/s")

            # Ανατολή/Δύση
            sunrise = datetime.fromtimestamp(res['city']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(res['city']['sunset']).strftime('%H:%M')
            st.divider()
            st.info(f"☀️ Ανατολή: {sunrise} | 🌙 Δύση: {sunset} | 📍 {res['city']['name']}")

    except Exception as e:
        st.error(f"Παρουσιάστηκε πρόβλημα: {str(e)}")
