"""
generate_sample_data.py
Jalankan file ini sekali untuk membuat data contoh di health_data.json
"""
import json
import random
from datetime import date, timedelta

random.seed(42)
logs = []
today = date.today()

for i in range(30, 0, -1):
    d = today - timedelta(days=i)
    jam_tidur = round(random.uniform(5.0, 9.0), 1)
    minum_air = random.randint(4, 12)
    makan_sehat = random.randint(1, 5)
    menit_olahraga = random.choice([0, 0, 15, 30, 30, 45, 60])
    level_stres = random.randint(2, 9)
    jam_belajar = round(random.uniform(1.0, 8.0), 1)

    skor = 0
    skor += 25 if 7 <= jam_tidur <= 9 else (15 if 6 <= jam_tidur < 7 else 5)
    skor += min(makan_sehat * 8, 25)
    skor += 25 if menit_olahraga >= 30 else (15 if menit_olahraga >= 15 else (7 if menit_olahraga > 0 else 0))
    skor += max(0, 25 - level_stres * 2.5)

    logs.append({
        "tanggal": str(d),
        "jam_tidur": jam_tidur,
        "kualitas_tidur": random.choice(["Baik", "Sangat Baik", "Biasa", "Buruk"]),
        "minum_air": minum_air,
        "makan_sehat": makan_sehat,
        "skip_sarapan": random.choice([True, False, False]),
        "menit_olahraga": menit_olahraga,
        "jenis_olahraga": random.sample(["Jalan kaki", "Lari", "Gym"], k=random.randint(0, 2)),
        "level_stres": level_stres,
        "suasana_hati": random.choice(["😄 Sangat Baik", "🙂 Baik", "😐 Netral", "😕 Kurang Baik"]),
        "jam_belajar": jam_belajar,
        "catatan": random.choice(["", "Hari ini lumayan produktif.", "Banyak tugas.", "Refreshing sebentar.", ""]),
        "skor": round(skor)
    })

data = {
    "profile": {
        "nama": "Mahasiswa Contoh",
        "nim": "2300000001",
        "prodi": "Informatika",
        "semester": 4,
        "tb": 168,
        "bb": 65,
        "target_tidur": 8.0,
        "target_air": 8,
        "imt": 23.0,
        "kat_imt": "Normal"
    },
    "logs": logs
}

with open("health_data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Berhasil membuat {len(logs)} hari data contoh!")
print("Sekarang jalankan: streamlit run app.py")
