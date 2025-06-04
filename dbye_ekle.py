import random
import pyodbc

# MSSQL bağlantısı
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=Smart_Plant_Recomandation_System;"
    "Trusted_Connection=yes;"
)

def get_all_suggested_plants():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT suggested_plant FROM Feedback")
    plants = [row[0] for row in cursor.fetchall()]
    conn.close()
    return plants

def simulate_user_feedback_form(plants_from_db):
    form_data = {
        "area_size": random.choice(["Mini", "Small", "Medium", "Large"]),
        "sunlight_need": random.choice([
            "6+ hours", "1-2 hours daily", "Can live in shade", "Bright indirect light"
        ]),
        "environment_type": random.choice(["Indoor", "Outdoor", "Semi-outdoor"]),
        "climate_type": random.choice(["Spring", "Summer", "Winter", "All seasons"]),
        "fertilizer_frequency": random.choice(["Monthly", "1-2 times a year", "Never needed"]),
        "pesticide_frequency": random.choice(["Monthly", "1-2 times a year", "Never needed"]),
        "watering_frequency": random.choice(["Daily", "Weekly", "Bi-weekly", "Every 2-3 days"]),
        "has_pet": random.choice(["Yes", "No"]),
        "has_child": random.choice(["Yes", "No"]),
        "suggested_plant": random.choice(plants_from_db),
        "user_feedback": random.choice([0, 1])
    }
    return form_data

# === Ana kullanım ===
plants_from_db = get_all_suggested_plants()
for i in range(5):
    print(f"📝 Simulated Form #{i+1}")
    print(simulate_user_feedback_form(plants_from_db))
    print("-" * 50)
