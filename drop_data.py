import pyodbc
import pandas as pd

# MSSQL bağlantı bilgileri
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=Smart_Plant_Recomandation_System;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Veri dağılımını al
df = pd.read_sql("SELECT id, user_feedback FROM Feedback", conn)
count_0 = (df["user_feedback"] == 0).sum()
count_1 = (df["user_feedback"] == 1).sum()

print(f"Veri dağılımı:\n 0: {count_0}\n 1: {count_1}")

# Fazla olan sınıfı belirle
if count_0 > count_1:
    excess_class = 0
    to_delete = count_0 - count_1
elif count_1 > count_0:
    excess_class = 1
    to_delete = count_1 - count_0
else:
    print("Veriler zaten dengeli, silme gerekmez.")
    conn.close()
    exit()

print(f"Silinecek kayıt sayısı: {to_delete} (feedback = {excess_class})")

# Fazlalık kayıtları rastgele seç
excess_ids = df[df["user_feedback"] == excess_class].sample(n=to_delete)["id"].tolist()

# ID'lere göre silme işlemi
for batch in range(0, len(excess_ids), 1000):
    id_chunk = excess_ids[batch:batch+1000]
    placeholders = ",".join("?" for _ in id_chunk)
    query = f"DELETE FROM Feedback WHERE id IN ({placeholders})"
    cursor.execute(query, id_chunk)

conn.commit()
cursor.close()
conn.close()
print(f"✅ {to_delete} kayıt başarıyla silindi ve veri dengelendi.")
