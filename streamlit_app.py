import streamlit as st
import requests
import json
from datetime import datetime
import folium
from streamlit_folium import st_folium

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="PeRGio Fishing Pro", layout="wide")

days_translation = {
    "Monday": "Δευτέρα", "Tuesday": "Τρίτη", "Wednesday": "Τετάρτη",
    "Thursday": "Πέμπτη", "Friday": "Παρασκευή", "Saturday": "Σάββατο", "Sunday": "Κυριακή"
}

# --- 2. ΔΙΑΧΕΙΡΙΣΗ ΜΝΗΜΗΣ ΤΟΠΟΘΕΣΙΩΝ ---
if 'my_places' not in st.session_state:
    try:
        with open('places.json', 'r', encoding='utf-8') as f:
            st.session_state.my_places = json.load(f)
    except:
        st.session_state.my_places = {"Πειραιάς": [37.94, 23.64]}

# --- 3. ΛΟΓΙΚΗ SCORE ---
def calculate_pergio_score(p_val, p_trend, wind, clouds, description):
    score = 0
    if p_val < 1010: score += 20
    elif 1011 <= p_val <= 1017: score += 10
    if p_trend == "falling": score += 20
    if 3 <= wind <= 5: score += 20 # Ιδανικά Μποφόρ
    if clouds > 50: score += 10
    if "βροχή" in description.lower() or "rain" in description.lower(): score -= 15
    return max(0, min(100, score + 30)) # +30 βάσει Σελήνης (μέσος όρος)

# --- 4. SIDEBAR: ΔΙΑΧΕΙΡΙΣΗ ΣΗΜΕΙΩΝ ---
st.sidebar.header("📍 Διαχείριση Σημείων")

# Επιλογή υπάρχοντος
selected_name = st.sidebar.selectbox("Τα μέρη μου:", list(st.session_state.my_places.keys()))
lat_init, lon_init = st.session_state.my_places[selected_name]

st.sidebar.divider()

# Προσθήκη νέου
new_place_name = st.sidebar.text_input("Όνομα νέου σημείου:")
save_button = st.sidebar.button("💾 Αποθήκευση Επιλεγμένου Σημείου")

# --- 5. ΚΥΡΙΟ GUI & ΧΑΡΤΗΣ ---
st.title(" 🎣 PeRGio Fishing Pro")

st.subheader("Επιλέξτε σημείο στον χάρτη ή από το Sidebar")
m = folium.Map(location=[lat_init, lon_init], zoom_start=10)
folium.Marker([lat_init, lon_init], popup=selected_name, icon=folium.Icon(color='red')).add_to(m)
m.add_child(folium.LatLngPopup())

# Επιστροφή δεδομένων από τον χάρτη
map_data = st_folium(m, height=350, width=800, key="main_map")

# Λογική Αποθήκευσης
current_lat, current_lon = lat_init, lon_init
if map_data['last_clicked']:
    current_lat = map_data['last_clicked']['lat']
    current_lon = map_data['last_clicked']['lng']
    st.write(f"Επιλεγμένες συντεταγμένες: `{current_lat:.4f}, {current_lon:.4f}`")

if save_button and new_place_name:
    st.session_state.my_places[new_place_name] = [current_lat, current_lon]
    st.sidebar.success(f"Το σημείο '{new_place_name}' προστέθηκε προσωρινά!")
    st.sidebar.warning("⚠️ Για μόνιμη αποθήκευση, ενημερώστε το αρχείο places.json στο GitHub.")

# --- 6. ΑΝΑΛΥΣΗ ---
if st.button("🚀 Εκτέλεση Ανάλυσης"):
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={current_lat}&lon={current_lon}&appid={api_key}&units=metric&lang=el"
        res = requests.get(url).json()
        
        days_dict = {}
        prev_p = res['list'][0]['main']['pressure']
        
        for item in res['list']:
            dt = datetime.fromtimestamp(item['dt'])
            day_label = f"{days_translation.get(dt.strftime('%A'), dt.strftime('%A'))} {dt.strftime('%d/%m')}"
            
            if day_label not in days_dict: days_dict[day_label] = []
            
            curr_p = item['main']['pressure']
            score = calculate_pergio_score(curr_p, "falling" if curr_p < prev_p else "stable", item['wind']['speed'], item['clouds']['all'], item['weather'][0]['description'])
            
            days_dict[day_label].append({
                "ώρα": dt.strftime('%H:%M'),
                "score": score,
                "καιρός": item['weather'][0]['description'],
                "άνεμος": item['wind']['speed']
            })
            prev_p = curr_p

        for day, data in days_dict.items():
            with st.expander(f"📅 {day}"):
                cols = st.columns(len(data))
                for i, d in enumerate(data):
                    with cols[i]:
                        color = "green" if d['score'] >= 75 else "orange" if d['score'] >= 45 else "red"
                        st.markdown(f"**{d['ώρα']}**\n### :{color}[{d['score']}%]\n{d['καιρός']}")
    except Exception as e:
        st.error(f"Σφάλμα API: Ελέγξτε τα Secrets.")

# --- 7. ΕΞΑΓΩΓΗ ΓΙΑ GITHUB (Μόνιμη Αποθήκευση) ---
if st.sidebar.checkbox("Εμφάνιση JSON για GitHub"):
    st.sidebar.code(json.dumps(st.session_state.my_places, indent=4, ensure_ascii=False))
    
