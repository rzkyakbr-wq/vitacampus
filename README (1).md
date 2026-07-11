# 🌿 VitaCampus – Sistem Monitoring Kesehatan & Kebiasaan Harian Mahasiswa

## Deskripsi Proyek

**VitaCampus** adalah aplikasi berbasis Streamlit yang membantu mahasiswa memantau dan meningkatkan kualitas kesehatan hariannya. Dengan permasalahan umum mahasiswa seperti kurang tidur, pola makan tidak teratur, jarang olahraga, dan stres tinggi saat ujian — VitaCampus hadir sebagai solusi digital yang simpel dan personal.

## Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🏠 Dashboard | Ringkasan skor kesehatan mingguan + tips personal |
| 📝 Catat Hari Ini | Input harian: tidur, hidrasi, olahraga, stres, produktivitas |
| 📊 Analisis & Grafik | Visualisasi tren + korelasi antar variabel kesehatan |
| 👤 Profil Saya | Data mahasiswa + kalkulasi IMT otomatis |
| 📋 Riwayat Log | Tabel dan detail semua catatan kesehatan |

## Cara Menjalankan

### 1. Clone Repository
```bash
git clone https://github.com/username/vitacampus.git
cd vitacampus
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi
```bash
streamlit run app.py
```

### 4. Buka di Browser
Aplikasi akan terbuka otomatis di `http://localhost:8501`

## Teknologi yang Digunakan
- **Python 3.9+**
- **Streamlit** – framework web app
- **Pandas** – manajemen data
- **Plotly** – visualisasi interaktif
- **JSON** – penyimpanan data lokal

## Rumus Skor Kesehatan (0–100)

| Komponen | Bobot | Kriteria |
|----------|-------|----------|
| Tidur | 25 poin | Ideal: 7–9 jam |
| Nutrisi | 25 poin | Makan sehat ≥3x/hari |
| Olahraga | 25 poin | ≥30 menit/hari |
| Stres (terbalik) | 25 poin | Level stres rendah = nilai tinggi |

## Struktur File
```
vitacampus/
├── app.py              # Kode utama Streamlit
├── requirements.txt    # Daftar library
├── README.md           # Dokumentasi
└── health_data.json    # Data tersimpan (auto-generated)
```

## Kontribusi
Proyek ini dibuat sebagai tugas mata kuliah Pemrograman Python.

---
*VitaCampus – Sehat itu investasi terbaik seorang mahasiswa* 🌿
