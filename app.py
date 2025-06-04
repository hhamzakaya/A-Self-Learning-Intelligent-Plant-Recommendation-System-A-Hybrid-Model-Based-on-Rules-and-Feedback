#app.py – Smart Plant Recommendation System (REDESIGNED VERSION)
# --------------------------------------------------------------
# This version features:
# 1. Two-column layout for better space utilization
# 2. Enhanced UI with custom styling and visual improvements
# 3. Maintains ALL original backend logic and functionality
# --------------------------------------------------------------

import streamlit as st
import pandas as pd
import joblib
import os
import subprocess
import numpy as np
import random  
import streamlit as st
from typing import Tuple
from data_handling import load_plants, add_feedback, sql_connect
from rule_engine import RuleEngine

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


from sklearn.compose import ColumnTransformer

feedback_model = joblib.load("models/feedback_model.pkl")

preprocessor:ColumnTransformer = joblib.load("models/feedback_vec.pkl")

logging.basicConfig(level=logging.DEBUG)



# --------------------------------------------------------------
# 🔧 Page / general config
# --------------------------------------------------------------
st.set_page_config(
    page_title="Smart Plant Recommender",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a more professional look
st.markdown("""
<style>
    /* Main styling */
    .main {
        background-color: #f8fef8;
    }
    
    /* Header styling */
    h1 {
        color: #2e7d32;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    h3 {
        text-align: center;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.75rem;
        text-transform: uppercase;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #2e7d32;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Form elements */
    .stSelectbox label, .stRadio label {
        font-weight: 500;
        color: #1b5e20;
    }
    
    /* Plant card */
    .plant-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-top: 1rem;
    }
    
    /* Feedback section */
    .feedback-section {
        border-top: 1px solid #e0e0e0;
        padding-top: 1rem;
        margin-top: 1rem;
    }
    
    /* Divider */
    .divider {
        background-color: #4CAF50;
        height: 3px;
        margin: 1rem 0;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Header with decorative elements
st.title("🌿 Smart Plant Recommendation System")
st.markdown("### 🌱 Fill the form to get your best‑matching plant:")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# --------------------------------------------------------------
#  Automatic retrain helper - KEEPING ORIGINAL CODE
# --------------------------------------------------------------

def check_and_retrain_if_needed(threshold: int =3)-> bool:
    """Retrain model when accepted‑feedback count is divisible by *threshold*."""
    logger.debug("Retrain ihtiyacı kontrol ediliyor (threshold: %d)", threshold)
    try:
        conn = sql_connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Feedback WHERE user_feedback = 1")
        count = cur.fetchone()[0]
        conn.close()
        logger.info("Toplam pozitif feedback: %s", count)

        if count and count % threshold == 0:
            st.info(f"🔁 Retraining ML model… (total positive feedback: {count})")
            logger.warning("Retrain başlatıldı.")
            
    
             
            subprocess.run([sys.executable, "learning_engine.py"], check=True)
            logger.info("learning_engine.py çalıştırıldı.")
            
            subprocess.run([
                                sys.executable,
                                "learning_engine_v2.py",
                                "--min-support", "0.01",
                                "--min-confidence", "0.01",
                                "--output", "parsed_rules.json"
                            ], check=True)

            logger.info("learning_engine_v2.py çalıştırıldı.")

           


               # 4. KB güncelle
            from kb_updater import update_knowledge_base
            update_knowledge_base("parsed_rules.json", "knowledge_base.json")
            logger.info("Bilgi tabanı güncellendi.")

            st.success("✅ Model retrained & rules updated.")
            return True


            

            
    except Exception as exc:  # pragma: no cover
        logger.error("Retrain sırasında hata: %s", exc)
        st.error(f"❌ Retrain check failed: {exc}")
    return False

# --------------------------------------------------------------
# 📝 User input in two-column layout
# --------------------------------------------------------------

def render_preference_form():
    """Return a dict with the user selections in a two-column layout."""
    
    # Create two columns for the form fields
    col1, col2 = st.columns(2)
    
    with col1:
        area_size = st.selectbox("Space Size", ["Mini", "Small", "Medium", "Large"])
        sunlight_need = st.selectbox(
            "Sunlight Requirement",
            ["Can live in shade", "1-2 hours daily", "Bright indirect light", "6+ hours"],
        )
        environment_type = st.selectbox("Environment Type", ["Indoor", "Outdoor", "Semi-outdoor"])
        climate_type = st.selectbox("Climate Type", ["All seasons", "Spring", "Summer", "Winter"])
        watering_frequency = st.selectbox(
            "Watering Frequency",
            ["Daily", "Weekly", "Bi-weekly", "Every 2-3 days", "Monthly"]
        )
    
    with col2:
        fertilizer_frequency = st.selectbox(
            "Fertilizer Frequency", ["Monthly", "1-2 times a year", "Never needed"]
        )
        pesticide_frequency = st.selectbox(
            "Pesticide Frequency", ["Monthly", "1-2 times a year", "Never needed"]
        )
        
        has_pet = st.radio("Do you have pets?", ["Yes", "No"])
        has_child = st.radio("Do you have children?", ["Yes", "No"])
        

        
    return {
        "area_size": area_size,
        "sunlight_need": sunlight_need,
        "environment_type": environment_type,
        "climate_type": climate_type,
        "fertilizer_frequency": fertilizer_frequency,
        "pesticide_frequency": pesticide_frequency,
        "has_pet": has_pet,
        "has_child": has_child,
        "watering_frequency": watering_frequency
    }

user_input = render_preference_form()

# Centered button with distinct styling
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    recommend_clicked = st.button("🌿 Recommend Plant")

# Eğer kullanıcı Öner butonuna bastıysa
if recommend_clicked:
    logger.info(" Öner butonuna tıklandı.")
    df = load_plants()

    if df.empty:
        logger.error(" Bitki verisi yüklenemedi.")
        st.error("Could not load plant data — check DB connection.")
        st.stop()

    rule_engine = RuleEngine(df)
    candidates = rule_engine.get_candidates(user_input, top_n=5)
    logger.info(" RuleEngine aday bitkiler: %s", candidates)

    logger.info(" ML skorlama başlatılıyor. %d aday değerlendirilecek.", len(candidates))
    scores: list[tuple[str, float]] = []

    # -------------------------------------------------
    # 1) Hiç aday bulunamazsa: tüm veri kümesi üzerinde ML-fallback
        # -------------------------------------------------
        # -------------------------------------------------
    # 1) Kural tabanlı aday bulunamazsa → fallback: tüm veri üzerinde ML skorlaması
    # -------------------------------------------------
    if not candidates:
        logger.warning("Kural tabanlı eşleşme bulunamadı, ML fallback başlatılıyor.")
        st.info("No rule-based match found. Trying best guess with ML...")

        for _, row in df.iterrows():
            record = {**user_input, "suggested_plant": row["plant_name"]}
            if "waterring_frequency" in record:
                record["watering_frequency"] = record.pop("waterring_frequency")

            try:
                record_encoded = preprocessor.transform(pd.DataFrame([record]))
                proba = feedback_model.predict_proba(record_encoded)[0, 1]
                scores.append((row["plant_name"], proba))
                logger.debug("ML skor: %s → %.3f", row["plant_name"], proba)
            except Exception as e:
                logger.error("ML skorlamasında hata: %s", str(e))

    # -------------------------------------------------
    # 2) Aday varsa → adaylar üzerinde skorla
    # -------------------------------------------------
    else:
        
        for plant in candidates:
            record = {**user_input, "suggested_plant": plant}

            try:
                # ML tahmini (proba)
                record_encoded = preprocessor.transform(pd.DataFrame([record]))
                ml_score = feedback_model.predict_proba(record_encoded)[0, 1]

                # FP-Growth confidence skoru
                fp_score = 0.0  # varsayılan değer
                for rule in rule_engine.kb.positive_rules:
                    if rule.suggested_plant == plant and rule.matches(user_input):
                        fp_score = rule.confidence  # veya rule.lift kullanılabilir
                        break

                # Hibrit skor: ağırlıklandırılmış ortalama
                hybrid_score = 0.7 * ml_score + 0.3 * fp_score

                scores.append((plant, hybrid_score))
                logger.debug("ML: %.3f | FP: %.3f → Hybrid: %.3f (%s)", ml_score, fp_score, hybrid_score, plant)

            except Exception as e:
                logger.error("Hibrit skorlamada hata (%s): %s", plant, str(e))


            # Adaylar gerçekten veritabanında var mı?
            scores.sort(key=lambda x: x[1], reverse=True)
            for plant, score in scores:
                if not df[df["plant_name"] == plant].empty:
                    best_plant, best_score = plant, score
                    
                    break
        #logger.info("✅ Kural + ML önerisi: %s (skor: %.3f)", best_plant, best_score)    
            else:
                # fallback'e geri dön
                st.info("⚠️ Candidates not in DB. ML fallback triggered.")
                scores.clear()
                for _, row in df.iterrows():
                    record = {**user_input, "suggested_plant": row["plant_name"]}
                    try:
                        record_encoded = preprocessor.transform(pd.DataFrame([record]))
                        proba = feedback_model.predict_proba(record_encoded)[0, 1]
                        scores.append((row["plant_name"], proba))
                        logger.debug("🔢 ML skor: %s → %.3f", row["plant_name"], proba)
                    except Exception as e:
                        logger.error("ML skorlamasında hata: %s", str(e))

    # -------------------------------------------------
    # 3) En yüksek skorlu adayı seç ve UI'da göster
    # -------------------------------------------------
    if not scores:
        st.error("❌ Herhangi bir öneri üretilemedi.")
        st.stop()

    scores.sort(key=lambda x: x[1], reverse=True)
    top_k = scores[:5]
    past = st.session_state.setdefault("past_recommendations", [])

    # Daha önce önerilmemiş olanı bul
    for plant, score in top_k:
        if plant not in past:
            suggestion = (plant, score)
            past.append(plant)
            break
    else:
        suggestion = random.choice(top_k)

    best_plant, best_score = suggestion
    logger.info("✅ Seçilen öneri: %s (Skor: %.3f)", best_plant, best_score)

    match = df[df["plant_name"].str.strip().str.lower() == best_plant.strip().lower()]
    if match.empty:
        st.error(f"'{best_plant}' için bitki detayları bulunamadı.")
        st.stop()

    row = match.iloc[0]

    # Sadece Session State'e yaz – UI gösterimi yalnızca 1 yerde yapılmalı
    st.session_state["recommended_plant"] = {
        "plant_name": best_plant,
        "description": row["description"],
        "image_url": row["image_url"],
    }
    st.session_state["user_input"] = user_input

# Eğer tavsiye varsa göster
plant_dict = st.session_state.get("recommended_plant")
if plant_dict:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"<div class='plant-card'>", unsafe_allow_html=True)
        st.markdown(f"### {plant_dict['plant_name']}")
        if pd.notna(plant_dict.get("image_url")):
            st.image(plant_dict["image_url"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<div class='plant-card'>", unsafe_allow_html=True)
        if not recommend_clicked:
            st.success(f"✅ Recommended Plant: **{plant_dict['plant_name']}**")

        st.markdown("### 📄 Description:")
        description_html = f"<div style='font-size:20px; line-height:1.6'>{plant_dict['description']}</div>"
        st.markdown(description_html, unsafe_allow_html=True)


        # Geri bildirim formu
        with st.form("feedback_form"):
            fb_choice = st.radio("💬 Was this recommendation suitable for you?", ["Yes", "No"])
            submit = st.form_submit_button("📩 Submit Feedback")

        st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        try:
            feedback_val = 1 if fb_choice == "Yes" else 0
            add_feedback(
                st.session_state["user_input"],
                plant_dict["plant_name"],
                feedback_val,
            )
            st.success(" Feedback saved. Thank you!")
            check_and_retrain_if_needed()
            st.session_state.pop("recommended_plant", None)
            st.session_state.pop("user_input", None)
        except Exception as exc:
            st.error(f" Failed to save feedback: {exc}")
