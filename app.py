import streamlit as st
import pandas as pd
import hashlib
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client, Client

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
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif; }

    .metric-card {
        background: #1b4332;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
        border-left: 5px solid #3D9970;
        margin-bottom: 12px;
    }
    .metric-card h3 { margin: 0 0 4px 0; font-size: 0.82rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.06em; color: #95d5b2 !important; }
    .metric-card .value { font-size: 2rem; font-weight: 800; color: #3D9970 !important; }
    .metric-card .sub { font-size: 0.8rem; margin-top: 2px; color: #b7e4c7 !important; }

    .health-badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 700; }
    .badge-green  { background: #1b4332; color: #95d5b2 !important; border: 1px solid #3D9970; }
    .badge-yellow { background: #3d2c00; color: #ffd166 !important; border: 1px solid #ffd166; }
    .badge-red    { background: #3d0000; color: #ff6b6b !important; border: 1px solid #ff6b6b; }

    .section-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.2rem; font-weight: 700;
        color: #3D9970 !important;
        margin-bottom: 14px; padding-bottom: 8px;
        border-bottom: 2px solid #3D9970;
    }

    .tip-box {
        background: #1b4332;
        border: 1px solid #3D9970;
        border-radius: 12px;
        padding: 14px 18px; margin: 8px 0;
        color: #d8f3dc !important;
        font-size: 0.92rem;
    }

    .log-entry {
        background: #1b4332;
        border-radius: 10px;
        padding: 14px 18px; margin-bottom: 8px;
        border-left: 4px solid #3D9970;
        color: #d8f3dc !important;
    }
    .log-entry b { color: #95d5b2 !important; }
    .log-entry small { color: #b7e4c7 !important; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1b4332 0%, #2d6a4f 100%) !important;
    }
    div[data-testid="stSidebar"] * { color: #d8f3dc !important; }

    .stButton > button {
        background: linear-gradient(135deg, #3D9970, #2d6a4f) !important;
        color: white !important; border: none !important;
        border-radius: 10px; padding: 10px 28px;
        font-weight: 700; transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(61,153,112,0.4) !important; }

    .user-chip {
        background: rgba(255,255,255,0.15);
        border-radius: 999px; padding: 5px 14px;
        font-size: 0.85rem; display: inline-block; margin-bottom: 6px;
        color: #d8f3dc !important;
    }

    .stForm { border: 1px solid #3D9970 !important; border-radius: 14px !important; padding: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KONEKSI SUPABASE
# ─────────────────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    url  = st.secrets["SUPABASE_URL"]
    key  = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ─────────────────────────────────────────────
# DATABASE FUNCTIONS
# ─────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, password, profil):
    # cek username sudah ada
    existing = supabase.table("users").select("username").eq("username", username.lower()).execute()
    if existing.data:
        return False, "Username sudah dipakai!"
    try:
        supabase.table("users").insert({
            "username":     username.lower(),
            "password_hash": hash_pw(password),
            "nama":         profil["nama"],
            "nim":          profil["nim"],
            "prodi":        profil["prodi"],
            "semester":     profil["semester"],
            "tinggi_badan": profil["tb"],
            "berat_badan":  profil["bb"],
            "target_tidur": profil["target_tidur"],
            "target_air":   profil["target_air"],
            "imt":          profil["imt"],
            "kat_imt":      profil["kat_imt"],
        }).execute()
        return True, "Akun berhasil dibuat!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login_user(username, password):
    res = supabase.table("users").select("*").eq("username", username.lower()).execute()
    if not res.data:
        return False, "Username tidak ditemukan!"
    user = res.data[0]
    if user["password_hash"] != hash_pw(password):
        return False, "Password salah!"
    return True, user

def get_profil(username):
    res = supabase.table("users").select("*").eq("username", username).execute()
    return res.data[0] if res.data else {}

def update_profil(username, profil):
    supabase.table("users").update({
        "nama":         profil["nama"],
        "nim":          profil["nim"],
        "prodi":        profil["prodi"],
        "semester":     profil["semester"],
        "tinggi_badan": profil["tb"],
        "berat_badan":  profil["bb"],
        "target_tidur": profil["target_tidur"],
        "target_air":   profil["target_air"],
        "imt":          profil["imt"],
        "kat_imt":      profil["kat_imt"],
    }).eq("username", username).execute()

def get_logs(username):
    res = supabase.table("health_logs").select("*").eq("username", username).order("tanggal").execute()
    return res.data or []

def save_log(username, log):
    # upsert berdasarkan username + tanggal
    supabase.table("health_logs").upsert({
        "username":       username,
        "tanggal":        log["tanggal"],
        "jam_tidur":      log["jam_tidur"],
        "kualitas_tidur": log["kualitas_tidur"],
        "minum_air":      log["minum_air"],
        "makan_sehat":    log["makan_sehat"],
        "skip_sarapan":   log["skip_sarapan"],
        "menit_olahraga": log["menit_olahraga"],
        "jenis_olahraga": str(log["jenis_olahraga"]),
        "level_stres":    log["level_stres"],
        "suasana_hati":   log["suasana_hati"],
        "jam_belajar":    log["jam_belajar"],
        "catatan":        log["catatan"],
        "skor":           log["skor"],
    }, on_conflict="username,tanggal").execute()

def delete_logs(username):
    supabase.table("health_logs").delete().eq("username", username).execute()

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username"  not in st.session_state: st.session_state.username  = ""

# ─────────────────────────────────────────────
# FUNGSI KESEHATAN
# ─────────────────────────────────────────────
def hitung_skor(log):
    skor = 0
    t = log.get("jam_tidur", 0)
    skor += 25 if 7<=t<=9 else (15 if (6<=t<7 or 9<t<=10) else (5 if t>0 else 0))
    skor += min(log.get("makan_sehat", 0)*8, 25)
    o = log.get("menit_olahraga", 0)
    skor += 25 if o>=30 else (15 if o>=15 else (7 if o>0 else 0))
    skor += max(0, 25 - log.get("level_stres", 5)*2.5)
    return round(skor)

def label_skor(s):
    if s >= 75: return ("Sangat Baik 🌟", "badge-green")
    elif s >= 50: return ("Cukup Baik 👍", "badge-yellow")
    return ("Perlu Perhatian ⚠️", "badge-red")

def tips_kesehatan(log):
    tips = []
    if log.get("jam_tidur", 8) < 7:     tips.append("😴 Tidurmu kurang dari 7 jam — coba tidur lebih awal!")
    if log.get("minum_air", 8) < 8:     tips.append("💧 Minum airmu kurang — targetkan 8 gelas per hari.")
    if log.get("menit_olahraga",0) < 30: tips.append("🏃 Olahraga minimal 30 menit — jalan kaki ke kampus pun bisa!")
    if log.get("level_stres", 0) >= 7:   tips.append("🧘 Stresmu tinggi — coba teknik pernapasan 4-7-8.")
    if log.get("makan_sehat", 0) < 2:    tips.append("🥗 Tambahkan sayur/buah ke makan harianmu.")
    if not tips: tips.append("✅ Hari ini luar biasa! Pertahankan pola hidupmu.")
    return tips

def get_df(logs):
    if not logs: return pd.DataFrame()
    df = pd.DataFrame(logs)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df.sort_values("tanggal")

LAYOUT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#3D9970"))

# ─────────────────────────────────────────────
# HALAMAN LOGIN / REGISTER
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown("# 🌿 VitaCampus")
        st.markdown("*Sistem Monitoring Kesehatan Mahasiswa*")
        st.markdown("---")

        tab_login, tab_reg = st.tabs(["🔐 Login", "📝 Daftar Akun Baru"])

        with tab_login:
            st.markdown("### Selamat Datang Kembali!")
            with st.form("form_login"):
                un = st.text_input("Username", placeholder="Masukkan username-mu")
                pw = st.text_input("Password", type="password", placeholder="Masukkan password-mu")
                if st.form_submit_button("🔐 Login", use_container_width=True):
                    if not un or not pw:
                        st.error("Username dan password wajib diisi!")
                    else:
                        with st.spinner("Memverifikasi..."):
                            ok, result = login_user(un, pw)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username  = result["username"]
                            st.success("✅ Login berhasil!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")

        with tab_reg:
            st.markdown("### Buat Akun Baru")
            with st.form("form_register"):
                st.markdown("**🔑 Data Akun**")
                c1, c2 = st.columns(2)
                with c1: reg_un = st.text_input("Username*", placeholder="Min. 3 karakter")
                with c2: reg_pw = st.text_input("Password*", type="password", placeholder="Min. 6 karakter")

                st.markdown("**👤 Data Diri**")
                c1, c2 = st.columns(2)
                with c1:
                    reg_nama     = st.text_input("Nama Lengkap*")
                    reg_nim      = st.text_input("NIM*")
                    reg_prodi    = st.text_input("Program Studi*")
                    reg_semester = st.number_input("Semester*", 1, 14, 1)
                with c2:
                    reg_tb           = st.number_input("Tinggi Badan (cm)*", 140, 220, 165)
                    reg_bb           = st.number_input("Berat Badan (kg)*",  30,  150, 60)
                    reg_target_tidur = st.slider("Target Jam Tidur/Hari", 6.0, 10.0, 8.0, 0.5)
                    reg_target_air   = st.slider("Target Gelas Air/Hari", 4, 15, 8)

                if st.form_submit_button("✅ Daftar Sekarang", use_container_width=True):
                    if not all([reg_un, reg_pw, reg_nama, reg_nim, reg_prodi]):
                        st.error("Semua field bertanda * wajib diisi!")
                    elif len(reg_pw) < 6:
                        st.error("Password minimal 6 karakter!")
                    elif len(reg_un) < 3:
                        st.error("Username minimal 3 karakter!")
                    else:
                        imt     = reg_bb / ((reg_tb/100)**2)
                        kat_imt = ("Kurang Berat Badan" if imt<18.5 else "Normal" if imt<25
                                   else "Kelebihan Berat Badan" if imt<30 else "Obesitas")
                        profil  = {
                            "nama": reg_nama, "nim": reg_nim,
                            "prodi": reg_prodi, "semester": int(reg_semester),
                            "tb": int(reg_tb), "bb": int(reg_bb),
                            "target_tidur": reg_target_tidur,
                            "target_air": int(reg_target_air),
                            "imt": round(imt,1), "kat_imt": kat_imt
                        }
                        with st.spinner("Membuat akun..."):
                            ok, msg = register_user(reg_un, reg_pw, profil)
                        if ok:
                            st.success(f"✅ {msg} Silakan login!")
                        else:
                            st.error(f"❌ {msg}")

# ─────────────────────────────────────────────
# HALAMAN UTAMA
# ─────────────────────────────────────────────
else:
    username = st.session_state.username
    profil   = get_profil(username)
    logs     = get_logs(username)

    with st.sidebar:
        st.markdown("## 🌿 VitaCampus")
        st.markdown(f'<div class="user-chip">👤 {profil.get("nama", username).split()[0]}</div>', unsafe_allow_html=True)
        st.markdown(f"*{profil.get('prodi','—')} · Sem {profil.get('semester','—')}*")
        st.markdown("---")
        menu = st.radio("Menu", [
            "🏠 Dashboard", "📝 Catat Hari Ini",
            "📊 Analisis & Grafik", "👤 Profil Saya", "📋 Riwayat Log"
        ], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.rerun()

    # ── DASHBOARD ──
    if menu == "🏠 Dashboard":
        nama_depan = profil.get("nama", username).split()[0]
        st.markdown(f"# 🌿 Halo, {nama_depan}! 👋")
        st.markdown("**Sistem Monitoring Kesehatan & Kebiasaan Harian Mahasiswa**")
        st.markdown("---")

        df = get_df(logs)
        if df.empty:
            st.info("👋 Belum ada data. Mulai catat di menu **Catat Hari Ini**!")
        else:
            df["skor"] = df.apply(hitung_skor, axis=1)
            cutoff = date.today() - timedelta(days=30)
            df30   = df[df["tanggal"].dt.date >= cutoff]
            skor_rata = int(df30["skor"].mean()) if not df30.empty else 0
            lbl, badge = label_skor(skor_rata)

            c1,c2,c3,c4 = st.columns(4)
            with c1:
                st.markdown(f"""<div class="metric-card"><h3>⏰ Rata-rata Tidur</h3>
                <div class="value">{round(df30['jam_tidur'].mean(),1) if not df30.empty else 0} jam</div>
                <div class="sub">30 hari terakhir</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="metric-card"><h3>💧 Rata-rata Air</h3>
                <div class="value">{round(df30['minum_air'].mean(),1) if not df30.empty else 0} gls</div>
                <div class="sub">30 hari terakhir</div></div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="metric-card"><h3>🏃 Rata-rata Olahraga</h3>
                <div class="value">{round(df30['menit_olahraga'].mean()) if not df30.empty else 0} mnt</div>
                <div class="sub">30 hari terakhir</div></div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class="metric-card"><h3>⭐ Skor Kesehatan</h3>
                <div class="value">{skor_rata}/100</div>
                <div class="sub"><span class="health-badge {badge}">{lbl}</span></div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown('<div class="section-title">📈 Tren Skor 30 Hari Terakhir</div>', unsafe_allow_html=True)
            if not df30.empty:
                fig = px.area(df30, x="tanggal", y="skor", color_discrete_sequence=["#3D9970"])
                fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=220,
                                  yaxis=dict(range=[0,100]), showlegend=False, **LAYOUT)
                fig.update_traces(fillcolor="rgba(61,153,112,0.2)", line_width=2.5)
                st.plotly_chart(fig, width="stretch")

            if logs:
                st.markdown('<div class="section-title">💡 Tips Hari Ini</div>', unsafe_allow_html=True)
                for tip in tips_kesehatan(logs[-1]):
                    st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

    # ── CATAT HARI INI ──
    elif menu == "📝 Catat Hari Ini":
        st.markdown("# 📝 Catat Kesehatan Hari Ini")
        st.markdown("Isi dengan jujur — datanya hanya untukmu! 😊")
        st.markdown("---")

        with st.form("form_log"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 😴 Tidur")
                tgl          = st.date_input("Tanggal", value=date.today())
                jam_tidur    = st.slider("Jam tidur tadi malam", 0.0, 12.0, 7.0, 0.5)
                kualitas     = st.select_slider("Kualitas tidur",
                    ["Sangat Buruk","Buruk","Biasa","Baik","Sangat Baik"], value="Baik")
                st.markdown("### 💧 Hidrasi & Nutrisi")
                minum_air    = st.slider("Gelas air hari ini", 0, 15, 8)
                makan_sehat  = st.slider("Makan bergizi (sayur/buah/protein)", 0, 5, 3)
                skip_sarapan = st.checkbox("Melewatkan sarapan hari ini")
            with c2:
                st.markdown("### 🏃 Aktivitas Fisik")
                menit_olah = st.slider("Menit olahraga/aktivitas fisik", 0, 120, 30, 5)
                jenis_olah = st.multiselect("Jenis aktivitas",
                    ["Jalan kaki","Lari","Gym","Renang","Bersepeda","Yoga/Stretching","Olahraga tim","Lainnya"])
                st.markdown("### 🧠 Mental & Produktivitas")
                level_stres  = st.slider("Level stres (1=santai, 10=sangat stres)", 1, 10, 4)
                suasana_hati = st.select_slider("Suasana hati",
                    ["😞 Buruk","😕 Kurang Baik","😐 Netral","🙂 Baik","😄 Sangat Baik"], value="🙂 Baik")
                jam_belajar  = st.slider("Jam belajar/tugas", 0.0, 12.0, 4.0, 0.5)
                catatan      = st.text_area("Catatan (opsional)", placeholder="Ceritakan harimu...", height=80)

            if st.form_submit_button("💾 Simpan", use_container_width=True):
                log_baru = {
                    "tanggal": str(tgl), "jam_tidur": jam_tidur,
                    "kualitas_tidur": kualitas, "minum_air": minum_air,
                    "makan_sehat": makan_sehat, "skip_sarapan": skip_sarapan,
                    "menit_olahraga": menit_olah, "jenis_olahraga": jenis_olah,
                    "level_stres": level_stres, "suasana_hati": suasana_hati,
                    "jam_belajar": jam_belajar, "catatan": catatan,
                }
                log_baru["skor"] = hitung_skor(log_baru)
                with st.spinner("Menyimpan..."):
                    save_log(username, log_baru)
                lbl, _ = label_skor(log_baru["skor"])
                st.success(f"✅ Tersimpan! Skor: **{log_baru['skor']}/100** — {lbl}")
                for tip in tips_kesehatan(log_baru):
                    st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

    # ── ANALISIS ──
    elif menu == "📊 Analisis & Grafik":
        st.markdown("# 📊 Analisis Kesehatan")
        st.markdown("---")
        df = get_df(logs)
        if df.empty:
            st.warning("Belum ada data. Catat dulu ya!")
        else:
            df["skor"] = df.apply(hitung_skor, axis=1)
            c1, _ = st.columns([1,3])
            with c1:
                periode = st.selectbox("Periode", ["7 Hari","14 Hari","30 Hari","Semua"])
            if periode != "Semua":
                cutoff = date.today() - timedelta(days={"7 Hari":7,"14 Hari":14,"30 Hari":30}[periode])
                df = df[df["tanggal"].dt.date >= cutoff]
            st.markdown(f"Menampilkan **{len(df)} hari** data")
            st.markdown("---")

            tab1,tab2,tab3,tab4 = st.tabs(["⭐ Skor","😴 Tidur & Air","🏃 Olahraga & Stres","🧠 Produktivitas"])

            with tab1:
                fig = go.Figure(go.Scatter(x=df["tanggal"], y=df["skor"], mode="lines+markers",
                    line=dict(color="#3D9970",width=3), marker=dict(size=8,color="#2d6a4f")))
                fig.add_hline(y=75, line_dash="dash", line_color="#95d5b2", annotation_text="Target (75)")
                fig.update_layout(title="Skor Harian", yaxis=dict(range=[0,100]), height=340, **LAYOUT)
                st.plotly_chart(fig, width="stretch")
                fig2 = px.histogram(df, x="skor", nbins=10, color_discrete_sequence=["#3D9970"], title="Distribusi Skor")
                fig2.update_layout(height=240, **LAYOUT)
                st.plotly_chart(fig2, width="stretch")

            with tab2:
                fig = make_subplots(rows=2, cols=1, subplot_titles=("Jam Tidur","Konsumsi Air"))
                fig.add_trace(go.Bar(x=df["tanggal"],y=df["jam_tidur"],marker_color="#42a5f5"), row=1,col=1)
                fig.add_hline(y=7, line_dash="dot", line_color="#ffd166", row=1, col=1)
                fig.add_trace(go.Bar(x=df["tanggal"],y=df["minum_air"],marker_color="#26c6da"), row=2,col=1)
                fig.add_hline(y=8, line_dash="dot", line_color="#ffd166", row=2, col=1)
                fig.update_layout(height=440, showlegend=False, **LAYOUT)
                st.plotly_chart(fig, width="stretch")

            with tab3:
                fig = make_subplots(rows=1,cols=2, subplot_titles=("Menit Olahraga","Level Stres"))
                fig.add_trace(go.Bar(x=df["tanggal"],y=df["menit_olahraga"],marker_color="#66bb6a"), row=1,col=1)
                fig.add_trace(go.Scatter(x=df["tanggal"],y=df["level_stres"],mode="lines+markers",
                    line=dict(color="#ef5350",width=2)), row=1,col=2)
                fig.update_layout(height=320, showlegend=False, **LAYOUT)
                st.plotly_chart(fig, width="stretch")

            with tab4:
                fig = go.Figure(go.Scatter(x=df["tanggal"],y=df["jam_belajar"],fill="tozeroy",
                    fillcolor="rgba(61,153,112,0.2)", line=dict(color="#3D9970",width=2)))
                fig.update_layout(title="Jam Belajar per Hari", height=320, yaxis_title="Jam", **LAYOUT)
                st.plotly_chart(fig, width="stretch")

            st.markdown("---")
            st.markdown('<div class="section-title">📊 Ringkasan Statistik</div>', unsafe_allow_html=True)
            stats = df[["jam_tidur","minum_air","menit_olahraga","level_stres","jam_belajar","skor"]].describe().T
            stats.columns = ["N","Rata-rata","Std Dev","Min","25%","50%","75%","Maks"]
            st.dataframe(stats[["Rata-rata","Min","Maks","Std Dev"]].round(2), use_container_width=True)

    # ── PROFIL ──
    elif menu == "👤 Profil Saya":
        st.markdown("# 👤 Profil Saya")
        st.markdown("---")
        with st.form("form_profil"):
            c1, c2 = st.columns(2)
            with c1:
                nama     = st.text_input("Nama Lengkap", value=profil.get("nama",""))
                nim      = st.text_input("NIM",          value=profil.get("nim",""))
                prodi    = st.text_input("Program Studi",value=profil.get("prodi",""))
                semester = st.number_input("Semester", 1, 14, value=int(profil.get("semester",1)))
            with c2:
                tb           = st.number_input("Tinggi Badan (cm)", 140, 220, value=int(profil.get("tinggi_badan",165)))
                bb           = st.number_input("Berat Badan (kg)",  30,  150, value=int(profil.get("berat_badan",60)))
                target_tidur = st.slider("Target Jam Tidur/Hari", 6.0, 10.0,
                                         value=float(profil.get("target_tidur",8.0)), step=0.5)
                target_air   = st.slider("Target Gelas Air/Hari", 4, 15,
                                         value=int(profil.get("target_air",8)))

            if st.form_submit_button("💾 Simpan", use_container_width=True):
                imt     = bb/((tb/100)**2)
                kat_imt = ("Kurang Berat Badan" if imt<18.5 else "Normal" if imt<25
                           else "Kelebihan Berat Badan" if imt<30 else "Obesitas")
                with st.spinner("Menyimpan..."):
                    update_profil(username, {
                        "nama":nama,"nim":nim,"prodi":prodi,"semester":int(semester),
                        "tb":int(tb),"bb":int(bb),
                        "target_tidur":target_tidur,"target_air":int(target_air),
                        "imt":round(imt,1),"kat_imt":kat_imt
                    })
                st.success("✅ Profil diperbarui!")
                st.rerun()

        if profil.get("imt"):
            st.markdown("---")
            st.markdown('<div class="section-title">📏 Indeks Massa Tubuh (IMT)</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="metric-card">
                    <h3>IMT Kamu</h3>
                    <div class="value">{profil['imt']}</div>
                    <div class="sub">{profil['kat_imt']}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=profil["imt"],
                    domain={"x":[0,1],"y":[0,1]},
                    gauge={"axis":{"range":[10,40]},"bar":{"color":"#3D9970"},
                           "steps":[{"range":[10,18.5],"color":"#1a3a5c"},
                                    {"range":[18.5,25],"color":"#1b4332"},
                                    {"range":[25,30],"color":"#3d2c00"},
                                    {"range":[30,40],"color":"#3d0000"}]}))
                fig.update_layout(height=200, margin=dict(l=20,r=20,t=20,b=20),
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#3D9970"))
                st.plotly_chart(fig, width="stretch")

    # ── RIWAYAT LOG ──
    elif menu == "📋 Riwayat Log":
        st.markdown("# 📋 Riwayat Catatan Kesehatan")
        st.markdown("---")
        df = get_df(logs)
        if df.empty:
            st.info("Belum ada catatan. Mulai dari **Catat Hari Ini**!")
        else:
            df["skor"] = df.apply(hitung_skor, axis=1)
            df_t = df[["tanggal","jam_tidur","minum_air","menit_olahraga","level_stres","jam_belajar","skor"]].copy()
            df_t["tanggal"] = df_t["tanggal"].dt.strftime("%d %b %Y")
            df_t.columns = ["Tanggal","Tidur (j)","Air (gls)","Olahraga (mnt)","Stres","Belajar (j)","Skor"]
            st.dataframe(df_t.sort_values("Tanggal", ascending=False), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown('<div class="section-title">📖 Log Detail (10 Terakhir)</div>', unsafe_allow_html=True)
            for log in reversed(logs[-10:]):
                skor = log.get("skor", hitung_skor(log))
                lbl, _ = label_skor(skor)
                cat = log.get("catatan","")
                st.markdown(f"""<div class="log-entry">
                    <b>{log['tanggal']}</b> | Skor: <b>{skor}</b> — {lbl}
                    | Tidur: {log.get('jam_tidur','?')}j
                    | Air: {log.get('minum_air','?')} gls
                    | Olahraga: {log.get('menit_olahraga','?')} mnt
                    | Stres: {log.get('level_stres','?')}/10
                    {"<br><small>💬 "+cat+"</small>" if cat else ""}
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🗑️ Hapus Semua Data Saya"):
                st.warning("Yakin ingin menghapus semua log kesehatanmu?")
                if st.button("✅ Ya, Hapus", key="del"):
                    with st.spinner("Menghapus..."):
                        delete_logs(username)
                    st.rerun()
