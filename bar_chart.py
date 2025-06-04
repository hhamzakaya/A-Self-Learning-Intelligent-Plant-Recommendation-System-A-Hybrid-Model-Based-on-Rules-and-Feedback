import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Dosyayı yükle
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# Pozitif ve negatif kuralları al
pos_rules = kb.get("positive_rules", [])
neg_rules = kb.get("negative_rules", [])

# Her iki set için ayrı DataFrame oluştur
df_pos = pd.DataFrame(pos_rules)
df_pos["feedback"] = 1
df_neg = pd.DataFrame(neg_rules)
df_neg["feedback"] = 0

# Hepsini birleştir
df = pd.concat([df_pos, df_neg], ignore_index=True)

# 1. Bar chart: Pozitif vs Negatif kural sayısı
rule_counts = df["feedback"].value_counts().rename({1: "Positive", 0: "Negative"})

plt.figure(figsize=(6, 4))
sns.barplot(x=rule_counts.index, y=rule_counts.values, palette="Set2")
plt.title("Rule Distribution (Positive vs Negative)")
plt.ylabel("Rule Count")
plt.xlabel("Rule Type")
plt.tight_layout()
plt.savefig("rule_distribution_from_kb.png")
plt.close()

# 2. Bitki bazlı kural frekansı (ilk 30 bitki)
plant_counts = df["suggested_plant"].value_counts().head(15)

plt.figure(figsize=(10, 6))
sns.barplot(y=plant_counts.index, x=plant_counts.values, palette="magma")
plt.title("Top 15 Plants (Knowledge Base)")
plt.xlabel("Rule Count")
plt.ylabel("Rule Name")
plt.tight_layout()
plt.savefig("top_plants_in_kb.png")
plt.close()

print("📊 Knowledge Base analiz grafikleri başarıyla oluşturuldu.")
