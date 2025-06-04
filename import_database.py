import pandas as pd
import random
import pyodbc

# MSSQL bağlantı bilgileri
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=Smart_Plant_Recomandation_System;"
    "Trusted_Connection=yes;"
)

# Veriyi oku
query = "SELECT * FROM Feedback"
conn = pyodbc.connect(conn_str)
df = pd.read_sql(query, conn)

df.columns = [
    "area_size", "sunlight_need", "environment_type", "climate_type",
    "fertilizer_frequency", "pesticide_frequency", "has_pet", "has_child",
    "suggested_plant", "user_feedback", "id", "watering_frequency"
]

# === Örüntü Kuralları ===
positive_rules = [
    lambda r: r["environment_type"] == "Indoor" and "indirect" in r["sunlight_need"].lower(),
    lambda r: r["climate_type"] in ["All seasons", "Winter"] and r["watering_frequency"] in ["Weekly", "Bi-weekly"],
    lambda r: r["area_size"] in ["Mini", "Small"] and r["sunlight_need"] == "6+ hours",
]

negative_rules = [
    lambda r: r["environment_type"] == "Indoor" and r["sunlight_need"] == "6+ hours",
    lambda r: r["climate_type"] == "Summer" and r["watering_frequency"] == "Never needed",
]

# === Yeni veriyi oluştur ===
condition_cols = [
    "area_size", "sunlight_need", "environment_type", "climate_type",
    "fertilizer_frequency", "pesticide_frequency", "has_pet", "has_child", "watering_frequency"
]
all_plants = set(df["suggested_plant"].unique())
unique_conditions = df[condition_cols].drop_duplicates().to_dict(orient="records")

synthetic_data = []
max_records = 1000

for condition in unique_conditions:
    candidates = list(all_plants)
    random.shuffle(candidates)
    for plant in candidates[:3]:
        if len(synthetic_data) >= max_records:
            break
        row = condition.copy()
        row["suggested_plant"] = plant

        if any(rule(row) for rule in positive_rules):
            row["user_feedback"] = 1
        elif any(rule(row) for rule in negative_rules):
            row["user_feedback"] = 0
        else:
            row["user_feedback"] = random.choice([0, 1])

        synthetic_data.append(row)

df_synth = pd.DataFrame(synthetic_data)

# === DATABASE'e ekle ===
cursor = conn.cursor()
for _, row in df_synth.iterrows():
    cursor.execute("""
        INSERT INTO Feedback (
            area_size, sunlight_need, environment_type, climate_type,
            fertilizer_frequency, pesticide_frequency, has_pet, has_child,
            suggested_plant, user_feedback, watering_frequency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(row[col] for col in df.columns if col != "id"))

conn.commit()
cursor.close()
conn.close()

print(f"✅ {len(df_synth)} kayıt veritabanına eklendi.")
