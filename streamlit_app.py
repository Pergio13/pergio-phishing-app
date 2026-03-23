import streamlit as st
import pandas as pd

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="PeRGio Fishing Score", layout="centered")

# --- ΣΥΝΑΡΤΗΣΗ ΥΠΟΛΟΓΙΣΜΟΥ (LOGIC) ---
def calculate_pergio_score(p_val, p_trend, moon, wind, onshore, clouds):
    """
    Υπολογισμός σκορ βάσει κανόνων Μάρκου Βιδάλη.
    Επεξηγήσεις δίπλα σε κάθε μεταβλητή για πλήρη κατανόηση.
    """
    score = 0
    
    # 1. Βαρομετρική Πίεση (40%)
    if p_val < 1010: score += 20          # Χαμηλή πίεση = Επιθετικότητα
    elif 1011 <= p_val <= 1017: score += 10
    
    if p_trend == "Πτωτική": score += 20    # Πτωτική τάση = Σήμα σίτισης
        
    # 2. Σελήνη & Ρεύματα (30%)
    if moon <= 15: score += 30             # Νέα Σελήνη (0-15%) = Μέγιστα ρεύματα
    elif moon >= 85: score += 20           # Πανσέληνος (85-100%) = Ρεύματα + Φως
    elif 40 <= moon <= 60: score += 0      # Νεκρά νερά = Ακινησία
    else: score += 10
        
    # 3. Άνεμος & Αφρουδιά (20%)
    if 3 <= wind <= 5: score += 10         # 3-5 Μποφόρ = Ιδανική οξυγόνωση
    if onshore: score += 10                # On-shore = Κάλυψη & Τροφή
        
    # 4. Συννεφιά (10%)
    if clouds > 50: score += 10            # Συννεφιά = Περισσότερες ώρες κυνηγιού
        
    return score

# --- GUI - ΔΙΕΠΑΦΗ ΧΡΗΣΤΗ ---
st.title("🎣 PeRGio Fishing Score")
st.write("Εισάγετε τις προβλέψεις της εβδομάδας για να δείτε τη 'Χρυσή Ευκαιρία'.")

# Sidebar για είσοδο δεδομένων
st.sidebar.header("Παράμετροι Ημέρας")
p_val = st.sidebar.number_input("Πίεση (hPa)", value=1013)
p_trend = st.sidebar.selectbox("Τάση Πίεσης", ["Σταθερή", "Πτωτική", "Ανοδική"])
moon = st.sidebar.slider("Φωτεινότητα Σελήνης (%)", 0, 100, 50)
wind = st.sidebar.slider("Ένταση Ανέμου (Bf)", 0, 9, 3)
onshore = st.sidebar.checkbox("Άνεμος προς την ακτή (On-shore / Αφρουδιά)")
clouds = st.sidebar.slider("Συννεφιά (%)", 0, 100, 20)

# Υπολογισμός
final_score = calculate_pergio_score(p_val, p_trend, moon, wind, onshore, clouds)

# Εμφάνιση Αποτελέσματος
st.header(f"Score: {final_score}%")

if final_score >= 80:
    st.success("🎯 ΑΡΙΣΤΟ: Χρυσή ευκαιρία! Τα ψάρια τρέφονται μανιωδώς.")
elif final_score >= 50:
    st.info("👍 ΚΑΛΟ: Απαιτείται σωστό timing στην αλλαγή παλίρροιας.")
else:
    st.warning("⚠️ ΔΥΣΚΟΛΟ: Ψάρια κολλημένα. Χρειάζονται λεπτά εργαλεία.")

# Οπτικοποίηση (Παράδειγμα εβδομάδας - Στατικά δεδομένα για αρχή)
st.divider()
st.subheader("Πρόβλεψη Εβδομάδας")
chart_data = pd.DataFrame({
    'Ημέρα': ['Δευ', 'Τρι', 'Τετ', 'Πεμ', 'Παρ', 'Σαβ', 'Κυρ'],
    'Score': [final_score, 45, 90, 30, 55, 75, 20] # Εδώ θα μπαίνουν τα δεδομένα από το API
})
st.bar_chart(chart_data.set_index('Ημέρα'))
