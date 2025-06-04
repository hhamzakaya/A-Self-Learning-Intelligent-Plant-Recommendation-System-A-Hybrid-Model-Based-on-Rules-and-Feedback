import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=Smart_Plant_Recomandation_System;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# En yüksek ID'leri al
cursor.execute("SELECT id FROM Feedback ORDER BY id DESC")
ids = [row[0] for row in cursor.fetchall()]

# 5000 kayıt bırak, diğerlerini sil
ids_to_delete = ids[5000:]  # en son 5000 kayıt hariç

for del_id in ids_to_delete:
    cursor.execute("DELETE FROM Feedback WHERE id = ?", del_id)

conn.commit()
cursor.close()
conn.close()

print(f"✅ {len(ids_to_delete)} kayıt silindi. Yaklaşık 5000 kayıt kaldı.")
