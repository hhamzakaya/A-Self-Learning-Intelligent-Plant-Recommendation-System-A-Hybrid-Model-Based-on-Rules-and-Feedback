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

# Veritabanından mevcut veriyi çek
query = "SELECT * FROM Feedback"
conn = pyodbc.connect(conn_str)
df = pd.read_sql(query, conn)

df.columns = [
    "area_size", "sunlight_need", "environment_type", "climate_type",
    "fertilizer_frequency", "pesticide_frequency", "has_pet", "has_child",
    "suggested_plant", "user_feedback", "id", "watering_frequency"
]

# === Veri Genişletme ===
condition_cols = [
    "area_size", "sunlight_need", "environment_type", "climate_type",
    "fertilizer_frequency", "pesticide_frequency", "has_pet", "has_child", "watering_frequency"
]

all_plants = set(df["suggested_plant"].unique())
synthetic_data = []
max_new_records = 80

unique_conditions = df[condition_cols].drop_duplicates().to_dict(orient="records")

for condition in unique_conditions:
    existing_plants = set(
        df.loc[
            (df[condition_cols] == pd.Series(condition)).all(axis=1),
            "suggested_plant"
        ]
    )
    candidate_plants = list(all_plants - existing_plants)

    for _ in range(min(3, len(candidate_plants))):
        if len(synthetic_data) >= max_new_records:
            break
        new_plant = random.choice(candidate_plants)
        candidate_plants.remove(new_plant)

        new_row = condition.copy()
        new_row["suggested_plant"] = new_plant
        new_row["user_feedback"] = 1
        
        synthetic_data.append(new_row)

df_synthetic = pd.DataFrame(synthetic_data)
df_synthetic["id"] = range(df["id"].max() + 1, df["id"].max() + 1 + len(df_synthetic))


# === Yeni kayıtları DATABASE'e yaz ===
cursor = conn.cursor()

for _, row in df_synthetic.iterrows():
    cursor.execute("""
    INSERT INTO Feedback (
        area_size, sunlight_need, environment_type, climate_type,
        fertilizer_frequency, pesticide_frequency, has_pet, has_child,
        suggested_plant, user_feedback, watering_frequency
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", tuple(row[col] for col in df.columns if col != "id"))


conn.commit()
cursor.close()
conn.close()

print(f"✅ {len(df_synthetic)} kayıt SQL Server'daki Feedback tablosuna eklendi.")
