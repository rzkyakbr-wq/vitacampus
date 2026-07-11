import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import hashlib
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="VitaCampus – Health Tracker Mahasiswa",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS KUSTOM
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif; }

    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-left: 5px solid #3D9970;
        margin-bottom: 12px;
    }
    .metric-card h3 { margin: 0 0 4px 0; color: #1a1a1a !important; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card .value { font-size: 2rem; font-weight: 800; color: #3D9970 !important; }
    .metric-card .sub { font-size: 0.8rem; color: #888 !important; margin-top: 2px; }

    .health-badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
    .badge-green { background: #d1fae5; color: #065f46; }
    .badge-yellow { background: #fef3c7; color: #92400e; }
    .badge-red { background: #fee2e2; color: #991b1b; }

    .section-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.3rem; font-weight: 700; color: #1a2e1a;
        margin-bottom: 16px; padding-bottom: 8px;
        border-bottom: 2px solid #e8f5e9;
    }

    .tip-box {
        background: linear-gradient(135deg, #e8f5e9, #f0faf0);
        border: 1px solid #a5d6a7; border-radius: 12px;
        padding: 16px 20px; margin: 12px 0;
        color: #1b3a1f !important;
    }
    .tip-box b { color: #2e7d32 !important; }

    .auth-card {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.10);
        max-width: 420px;
        margin: 0 auto;
    }
    .auth-card h2 { color: #1b4332; font-family: 'Plus Jakarta Sans', sans-serif; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1b4332 0%, #2d6a4f 100%);
    }
    div[data-testid="stSidebar"] * { color: #d8f3dc !important; }

    .stButton > button {
        background: linear-gradient(135deg, #3D9970, #2d6a4f);
        color: white; border: none; border-radius: 10px;
        padding: 10px 28px; font-weight: 600; font-size: 0.9rem;
        transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(61,153,112,0.4); }

    .log-entry {
        background: white; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 8px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #81c784;
        color: #1a1a1a !important;
    }
    .log-entry b { color: #1b3a1f !important; }
    .log-entry small { color: #555 !important; }

    .user-chip {
        background: rgba(255,255,255,0.15);
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATABASE (JSON file per user)
# ─────────────────────────────────────────────
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, default=str)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, profil):
    db = load_db()
    if username in db:
        return False, "Username sudah dipakai!"
    db[username] = {
        "password": hash_password(password),
        "profil": profil,
        "logs": []
    }
    save_db(db)
    return True, "Registrasi berhasil!"

def login_user(username, password):
    db = load_db()
    if username not in db:
        return False, "Username tidak ditemukan!"
    if db[username]["password"] != hash_password(password):
        return False, "Password salah!"
    return True, db[username]

def get_user_data(username):
    db = load_db()
    return db.get(username, {})

def save_user_data(username, data):
    db = load_db()
    db[username] = data
    save_db(db)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

# ─────────────────────────────────────────────
# FUNGSI KESEHATAN
# ─────────────────────────────────────────────
def hitung_skor(log):
    skor = 0
    tidur = log.get("jam_tidur", 0)
    if 7 <= tidur <= 9: skor += 25
    elif 6 <= tidur < 7 or 9 < tidur <= 10: skor += 15
    elif tidur > 0: skor += 5
    makan = log.get("makan_sehat", 0)
    skor += min(makan * 8, 25)
    olahraga = log.get("menit_olahraga", 0)
    if olahraga >= 30: skor += 25
    elif olahraga >= 15: skor += 15
    elif olahraga > 0: skor += 7
    stres = log.get("level_stres", 5)
    skor += max(0, 25 - stres * 2.5)
    return round(skor)

def label_skor(s):
    if s >= 75: return ("Sangat Baik 🌟", "badge-green")
    elif s >= 50: return ("Cukup Baik 👍", "badge-yellow")
    else: return ("Perlu Perhatian ⚠️", "badge-red")

def tips_kesehatan(log):
    tips = []
    if log.get("jam_tidur", 8) < 7:
        tips.append("😴 Tidurmu kurang dari 7 jam — coba tidur lebih awal malam ini!")
    if log.get("minum_air", 8) < 8:
        tips.append("💧 Minum airmu masih kurang — targetkan 8 gelas per hari.")
    if log.get("menit_olahraga", 0) < 30:
        tips.append("🏃 Coba olahraga ringan 30 menit — jalan kaki ke kampus pun sudah membantu!")
    if log.get("level_stres", 0) >= 7:
        tips.append("🧘 Stresmu tinggi — coba teknik pernapasan 4-7-8 atau istirahat sejenak.")
    if log.get("makan_sehat", 0) < 2:
        tips.append("🥗 Kurangi junk food dan tambahkan sayur/buah ke makan harianmu.")
    if not tips:
        tips.append("✅ Hari ini luar biasa! Pertahankan pola hidupmu yang sehat.")
    return tips

def get_df(logs):
    if not logs:
        return pd.DataFrame()
    df = pd.DataFrame(logs)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df.sort_values("tanggal")

# ─────────────────────────────────────────────
# HALAMAN: LOGIN & REGISTER
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        st.markdown("# 🌿 VitaCampus")
        st.markdown("*Sistem Monitoring Kesehatan Mahasiswa*")
        st.markdown("---")

        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Daftar Akun Baru"])

        # ── LOGIN ──
        with tab_login:
            st.markdown("### Selamat Datang Kembali!")
            with st.form("form_login"):
                username = st.text_input("Username", placeholder="Masukkan username")
                password = st.text_input("Password", type="password", placeholder="Masukkan password")
                login_btn = st.form_submit_button("🔐 Login", use_container_width=True)

                if login_btn:
                    if not username or not password:
                        st.error("Username dan password wajib diisi!")
                    else:
                        ok, result = login_user(username, password)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.success("✅ Login berhasil!")
                            st.rerun()
                        else:
                            st.error(result)

        # ── REGISTER ──
        with tab_register:
            st.markdown("### Buat Akun Baru")
            with st.form("form_register"):
                st.markdown("**Akun**")
                col1, col2 = st.columns(2)
                with col1:
                    reg_username = st.text_input("Username*", placeholder="Buat username unik")
                with col2:
                    reg_password = st.text_input("Password*", type="password", placeholder="Min. 6 karakter")

                st.markdown("**Data Diri**")
                col1, col2 = st.columns(2)
                with col1:
                    reg_nama = st.text_input("Nama Lengkap*", placeholder="Nama sesuai KTM")
                    reg_nim = st.text_input("NIM*", placeholder="Nomor Induk Mahasiswa")
                    reg_prodi = st.text_input("Program Studi*", placeholder="Contoh: Informatika")
                    reg_semester = st.number_input("Semester*", 1, 14, value=1)
                with col2:
                    reg_tb = st.number_input("Tinggi Badan (cm)*", 140, 220, value=165)
                    reg_bb = st.number_input("Berat Badan (kg)*", 30, 150, value=60)
                    reg_target_tidur = st.slider("Target Jam Tidur/Hari", 6.0, 10.0, 8.0, 0.5)
                    reg_target_air = st.slider("Target Gelas Air/Hari", 4, 15, 8)

                reg_btn = st.form_submit_button("✅ Daftar Sekarang", use_container_width=True)

                if reg_btn:
                    if not all([reg_username, reg_password, reg_nama, reg_nim, reg_prodi]):
                        st.error("Semua field bertanda * wajib diisi!")
                    elif len(reg_password) < 6:
                        st.error("Password minimal 6 karakter!")
                    else:
                        imt = reg_bb / ((reg_tb / 100) ** 2)
                        kat_imt = "Kurang Berat Badan" if imt < 18.5 else "Normal" if imt < 25 else "Kelebihan Berat Badan" if imt < 30 else "Obesitas"
                        profil = {
                            "nama": reg_nama, "nim": reg_nim,
                            "prodi": reg_prodi, "semester": reg_semester,
                            "tb": reg_tb, "bb": reg_bb,
                            "target_tidur": reg_target_tidur,
                            "target_air": reg_target_air,
                            "imt": round(imt, 1), "kat_imt": kat_imt
                        }
                        ok, msg = register_user(reg_username, reg_password, profil)
                        if ok:
                            st.success(f"✅ {msg} Silakan login!")
                        else:
                            st.error(msg)

# ─────────────────────────────────────────────
# HALAMAN UTAMA (SETELAH LOGIN)
# ─────────────────────────────────────────────
else:
    username = st.session_state.username
    user_data = get_user_data(username)
    profil = user_data.get("profil", {})
    logs = user_data.get("logs", [])

    # SIDEBAR
    with st.sidebar:
        st.markdown("## 🌿 VitaCampus")
        st.markdown(f'<div class="user-chip">👤 {profil.get("nama", username)}</div>', unsafe_allow_html=True)
        st.markdown(f"*{profil.get('prodi', '')} — Sem {profil.get('semester', '')}*")
        st.markdown("---")
        menu = st.radio(
            "Navigasi",
            ["🏠 Dashboard", "📝 Catat Hari Ini", "📊 Analisis & Grafik", "👤 Profil Saya", "📋 Riwayat Log"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    # ── DASHBOARD ──
    if menu == "🏠 Dashboard":
        st.markdown(f"# 🌿 Halo, {profil.get('nama', username).split()[0]}! 👋")
        st.markdown("**Sistem Monitoring Kesehatan & Kebiasaan Harian Mahasiswa**")
        st.markdown("---")

        df = get_df(logs)

        if df.empty:
            st.info("👋 Belum ada data. Mulai catat kesehatanmu di menu **Catat Hari Ini**!")
        else:
            hari_ini = date.today()
            tiga_puluh_hari_lalu = hari_ini - timedelta(days=30)
            df["skor"] = df.apply(hitung_skor, axis=1)
            df_30 = df[df["tanggal"].dt.date >= tiga_puluh_hari_lalu].copy()

            skor_rata = int(df_30["skor"].mean()) if not df_30.empty else 0
            label, badge_class = label_skor(skor_rata)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                tidur_avg = round(df_30["jam_tidur"].mean(), 1) if not df_30.empty else 0
                st.markdown(f"""<div class="metric-card">
                    <h3>⏰ Rata-rata Tidur</h3>
                    <div class="value">{tidur_avg} jam</div>
                    <div class="sub">30 hari terakhir</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                air_avg = round(df_30["minum_air"].mean(), 1) if not df_30.empty else 0
                st.markdown(f"""<div class="metric-card">
                    <h3>💧 Rata-rata Air</h3>
                    <div class="value">{air_avg} gelas</div>
                    <div class="sub">30 hari terakhir</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                olah_avg = round(df_30["menit_olahraga"].mean()) if not df_30.empty else 0
                st.markdown(f"""<div class="metric-card">
                    <h3>🏃 Rata-rata Olahraga</h3>
                    <div class="value">{olah_avg} mnt</div>
                    <div class="sub">30 hari terakhir</div>
                </div>""", unsafe_allow_html=True)
            with col4:
                st.markdown(f"""<div class="metric-card">
                    <h3>⭐ Skor Kesehatan</h3>
                    <div class="value">{skor_rata}/100</div>
                    <div class="sub"><span class="health-badge {badge_class}">{label}</span></div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown('<div class="section-title">📈 Tren Skor Kesehatan 30 Hari Terakhir</div>', unsafe_allow_html=True)
            if not df_30.empty:
                fig = px.area(df_30, x="tanggal", y="skor",
                              color_discrete_sequence=["#3D9970"],
                              labels={"skor": "Skor Kesehatan", "tanggal": "Tanggal"})
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                  margin=dict(l=10, r=10, t=10, b=10), height=220,
                                  yaxis=dict(range=[0, 100], gridcolor="#f0f0f0"),
                                  xaxis=dict(gridcolor="#f0f0f0"), showlegend=False)
                fig.update_traces(fillcolor="rgba(61,153,112,0.15)", line_width=2.5)
                st.plotly_chart(fig, width="stretch")

            if logs:
                log_terakhir = logs[-1]
                st.markdown('<div class="section-title">💡 Tips untuk Kamu Hari Ini</div>', unsafe_allow_html=True)
                for tip in tips_kesehatan(log_terakhir):
                    st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

    # ── CATAT HARI INI ──
    elif menu == "📝 Catat Hari Ini":
        st.markdown("# 📝 Catat Kesehatan Hari Ini")
        st.markdown("Isi dengan jujur ya — datanya hanya untuk dirimu sendiri! 😊")
        st.markdown("---")

        with st.form("form_log"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 😴 Tidur")
                tanggal = st.date_input("Tanggal", value=date.today())
                jam_tidur = st.slider("Berapa jam kamu tidur tadi malam?", 0.0, 12.0, 7.0, 0.5)
                kualitas_tidur = st.select_slider("Kualitas tidur",
                    options=["Sangat Buruk", "Buruk", "Biasa", "Baik", "Sangat Baik"], value="Baik")
                st.markdown("### 💧 Hidrasi & Nutrisi")
                minum_air = st.slider("Gelas air yang diminum hari ini", 0, 15, 8)
                makan_sehat = st.slider("Berapa kali makan bergizi (sayur/buah/protein)?", 0, 5, 3)
                skip_sarapan = st.checkbox("Aku melewatkan sarapan hari ini")
            with col2:
                st.markdown("### 🏃 Aktivitas Fisik")
                menit_olahraga = st.slider("Menit berolahraga / aktivitas fisik", 0, 120, 30, 5)
                jenis_olahraga = st.multiselect("Jenis aktivitas",
                    ["Jalan kaki", "Lari", "Gym", "Renang", "Bersepeda", "Yoga/Stretching", "Olahraga tim", "Lainnya"])
                st.markdown("### 🧠 Mental & Produktivitas")
                level_stres = st.slider("Level stres hari ini (1=santai, 10=sangat stres)", 1, 10, 4)
                suasana_hati = st.select_slider("Suasana hati dominan",
                    options=["😞 Buruk", "😕 Kurang Baik", "😐 Netral", "🙂 Baik", "😄 Sangat Baik"], value="🙂 Baik")
                jam_belajar = st.slider("Jam belajar/mengerjakan tugas", 0.0, 12.0, 4.0, 0.5)
                catatan = st.text_area("Catatan pribadi (opsional)", placeholder="Ceritakan harimu...", height=80)

            submitted = st.form_submit_button("💾 Simpan Catatan Hari Ini", use_container_width=True)
            if submitted:
                log_baru = {
                    "tanggal": str(tanggal), "jam_tidur": jam_tidur,
                    "kualitas_tidur": kualitas_tidur, "minum_air": minum_air,
                    "makan_sehat": makan_sehat, "skip_sarapan": skip_sarapan,
                    "menit_olahraga": menit_olahraga, "jenis_olahraga": jenis_olahraga,
                    "level_stres": level_stres, "suasana_hati": suasana_hati,
                    "jam_belajar": jam_belajar, "catatan": catatan,
                    "skor": hitung_skor({"jam_tidur": jam_tidur, "makan_sehat": makan_sehat,
                                         "menit_olahraga": menit_olahraga, "level_stres": level_stres})
                }
                user_data["logs"] = [l for l in logs if l["tanggal"] != str(tanggal)]
                user_data["logs"].append(log_baru)
                save_user_data(username, user_data)
                label, _ = label_skor(log_baru["skor"])
                st.success(f"✅ Tersimpan! Skor kesehatanmu: **{log_baru['skor']}/100** — {label}")
                for tip in tips_kesehatan(log_baru):
                    st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

    # ── ANALISIS & GRAFIK ──
    elif menu == "📊 Analisis & Grafik":
        st.markdown("# 📊 Analisis Kesehatan")
        st.markdown("---")
        df = get_df(logs)

        if df.empty:
            st.warning("Belum ada data. Catat kesehatanmu dulu ya!")
        else:
            df["skor"] = df.apply(hitung_skor, axis=1)
            col_f1, _ = st.columns([1, 3])
            with col_f1:
                periode = st.selectbox("Periode", ["7 Hari", "14 Hari", "30 Hari", "Semua"])
            hari_map = {"7 Hari": 7, "14 Hari": 14, "30 Hari": 30}
            if periode != "Semua":
                cutoff = date.today() - timedelta(days=hari_map[periode])
                df = df[df["tanggal"].dt.date >= cutoff]
            st.markdown(f"Menampilkan **{len(df)} hari** data")
            st.markdown("---")

            tab1, tab2, tab3, tab4 = st.tabs(["⭐ Skor Harian", "😴 Tidur & Air", "🏃 Olahraga & Stres", "🧠 Produktivitas"])

            with tab1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["tanggal"], y=df["skor"], mode="lines+markers",
                    line=dict(color="#3D9970", width=3), marker=dict(size=8, color="#2d6a4f")))
                fig.add_hline(y=75, line_dash="dash", line_color="#81c784", annotation_text="Target (75)")
                fig.update_layout(title="Skor Kesehatan Harian", yaxis=dict(range=[0,100], title="Skor"),
                    plot_bgcolor="white", paper_bgcolor="white", height=350)
                st.plotly_chart(fig, width="stretch")
                fig2 = px.histogram(df, x="skor", nbins=10, color_discrete_sequence=["#3D9970"],
                    title="Distribusi Skor Kesehatan")
                fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=250)
                st.plotly_chart(fig2, width="stretch")

            with tab2:
                fig = make_subplots(rows=2, cols=1, subplot_titles=("Jam Tidur per Hari", "Konsumsi Air per Hari"))
                fig.add_trace(go.Bar(x=df["tanggal"], y=df["jam_tidur"], marker_color="#42a5f5"), row=1, col=1)
                fig.add_hline(y=7, line_dash="dot", line_color="orange", row=1, col=1)
                fig.add_trace(go.Bar(x=df["tanggal"], y=df["minum_air"], marker_color="#26c6da"), row=2, col=1)
                fig.add_hline(y=8, line_dash="dot", line_color="orange", row=2, col=1)
                fig.update_layout(height=450, plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
                st.plotly_chart(fig, width="stretch")

            with tab3:
                fig = make_subplots(rows=1, cols=2, subplot_titles=("Menit Olahraga", "Level Stres"))
                fig.add_trace(go.Bar(x=df["tanggal"], y=df["menit_olahraga"], marker_color="#66bb6a"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df["tanggal"], y=df["level_stres"], mode="lines+markers",
                    line=dict(color="#ef5350", width=2)), row=1, col=2)
                fig.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
                st.plotly_chart(fig, width="stretch")

            with tab4:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["tanggal"], y=df["jam_belajar"], fill="tozeroy",
                    fillcolor="rgba(61,153,112,0.15)", line=dict(color="#3D9970", width=2)))
                fig.update_layout(title="Jam Belajar per Hari", height=320,
                    plot_bgcolor="white", paper_bgcolor="white", yaxis_title="Jam")
                st.plotly_chart(fig, width="stretch")

            st.markdown("---")
            st.markdown('<div class="section-title">📊 Ringkasan Statistik</div>', unsafe_allow_html=True)
            stats = df[["jam_tidur", "minum_air", "menit_olahraga", "level_stres", "jam_belajar", "skor"]].describe().T
            stats.columns = ["Jumlah", "Rata-rata", "Std Dev", "Min", "25%", "50%", "75%", "Maks"]
            stats["Rata-rata"] = stats["Rata-rata"].round(2)
            st.dataframe(stats[["Rata-rata", "Min", "Maks", "Std Dev"]], use_container_width=True)

    # ── PROFIL SAYA ──
    elif menu == "👤 Profil Saya":
        st.markdown("# 👤 Profil Saya")
        st.markdown("---")

        with st.form("form_profil"):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Lengkap", value=profil.get("nama", ""))
                nim = st.text_input("NIM", value=profil.get("nim", ""))
                prodi = st.text_input("Program Studi", value=profil.get("prodi", ""))
                semester = st.number_input("Semester", 1, 14, value=int(profil.get("semester", 1)))
            with col2:
                tb = st.number_input("Tinggi Badan (cm)", 140, 220, value=int(profil.get("tb", 165)))
                bb = st.number_input("Berat Badan (kg)", 30, 150, value=int(profil.get("bb", 60)))
                target_tidur = st.slider("Target Jam Tidur/Hari", 6.0, 10.0,
                    value=float(profil.get("target_tidur", 8.0)), step=0.5)
                target_air = st.slider("Target Gelas Air/Hari", 4, 15, value=int(profil.get("target_air", 8)))

            if st.form_submit_button("💾 Simpan Perubahan", use_container_width=True):
                imt = bb / ((tb / 100) ** 2)
                kat_imt = "Kurang Berat Badan" if imt < 18.5 else "Normal" if imt < 25 else "Kelebihan Berat Badan" if imt < 30 else "Obesitas"
                user_data["profil"] = {
                    "nama": nama, "nim": nim, "prodi": prodi, "semester": semester,
                    "tb": tb, "bb": bb, "target_tidur": target_tidur, "target_air": target_air,
                    "imt": round(imt, 1), "kat_imt": kat_imt
                }
                save_user_data(username, user_data)
                st.success("✅ Profil berhasil diperbarui!")
                st.rerun()

        if profil.get("imt"):
            st.markdown("---")
            st.markdown('<div class="section-title">📏 Indeks Massa Tubuh (IMT)</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div class="metric-card">
                    <h3>IMT Kamu</h3>
                    <div class="value">{profil['imt']}</div>
                    <div class="sub">{profil['kat_imt']}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=profil["imt"],
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={"axis": {"range": [10, 40]}, "bar": {"color": "#3D9970"},
                           "steps": [{"range": [10, 18.5], "color": "#90caf9"},
                                     {"range": [18.5, 25], "color": "#a5d6a7"},
                                     {"range": [25, 30], "color": "#fff176"},
                                     {"range": [30, 40], "color": "#ef9a9a"}]}))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, width="stretch")

    # ── RIWAYAT LOG ──
    elif menu == "📋 Riwayat Log":
        st.markdown("# 📋 Riwayat Catatan Kesehatan")
        st.markdown("---")
        df = get_df(logs)

        if df.empty:
            st.info("Belum ada catatan. Mulai dari menu **Catat Hari Ini**!")
        else:
            df["skor"] = df.apply(hitung_skor, axis=1)
            df_tampil = df[["tanggal", "jam_tidur", "minum_air", "menit_olahraga",
                             "level_stres", "jam_belajar", "skor"]].copy()
            df_tampil["tanggal"] = df_tampil["tanggal"].dt.strftime("%d %b %Y")
            df_tampil.columns = ["Tanggal", "Tidur (jam)", "Air (gelas)", "Olahraga (mnt)", "Stres", "Belajar (jam)", "Skor"]
            st.dataframe(df_tampil.sort_values("Tanggal", ascending=False), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown('<div class="section-title">📖 Log Detail (10 Terakhir)</div>', unsafe_allow_html=True)
            for log in reversed(logs[-10:]):
                skor = log.get("skor", hitung_skor(log))
                label, _ = label_skor(skor)
                catatan_text = log.get("catatan", "")
                st.markdown(f"""<div class="log-entry">
                    <b>{log['tanggal']}</b> &nbsp;|&nbsp; Skor: <b>{skor}</b> — {label}
                    &nbsp;|&nbsp; Tidur: {log.get('jam_tidur','?')}j
                    &nbsp;|&nbsp; Air: {log.get('minum_air','?')} gelas
                    &nbsp;|&nbsp; Olahraga: {log.get('menit_olahraga','?')} mnt
                    &nbsp;|&nbsp; Stres: {log.get('level_stres','?')}/10
                    {"<br><small>💬 " + catatan_text + "</small>" if catatan_text else ""}
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🗑️ Hapus Semua Data Saya"):
                st.warning("Yakin ingin menghapus semua data kesehatanmu?")
                if st.button("✅ Ya, Hapus Semua", key="confirm_delete"):
                    user_data["logs"] = []
                    save_user_data(username, user_data)
                    st.success("Data berhasil dihapus.")
                    st.rerun()
