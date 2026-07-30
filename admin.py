"""
admin.py — Panel Admin VitaCampus
Diimpor & dipanggil dari app.py. Berisi:
  - Login admin (form terpisah, dipicu tombol "🔑 Admin" di pojok kanan atas)
  - 6 fitur admin:
      1. Daftar user terdaftar
      2. Mahasiswa dengan indikasi masalah kesehatan
      3. Statistik kesehatan semua mahasiswa
      4. Kirim notifikasi manual
      5. Export data & statistik (CSV/Excel)
      6. Tambah user manual
"""

import streamlit as st
import pandas as pd
import hashlib
from io import BytesIO
from datetime import datetime, date
from supabase import create_client, Client

# ─────────────────────────────────────────────
# SUPABASE (client sendiri, terpisah dari app.py)
# ─────────────────────────────────────────────
@st.cache_resource
def init_supabase_admin() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase_admin = init_supabase_admin()


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ─────────────────────────────────────────────
# AUTH ADMIN
# ─────────────────────────────────────────────
def login_admin(username: str, password: str):
    res = (
        supabase_admin.table("users")
        .select("*")
        .eq("username", username.lower().strip())
        .eq("is_admin", True)
        .execute()
    )
    if not res.data:
        return False, "Username admin tidak ditemukan / bukan admin!"
    u = res.data[0]
    if u["password_hash"] != hash_pw(password):
        return False, "Password salah!"
    return True, u


def admin_login_form():
    """Form kecil yang muncul saat tombol 'Admin' di pojok kanan atas diklik."""
    with st.container(border=True):
        st.markdown("### 🔑 Login Admin")
        with st.form("form_login_admin", clear_on_submit=False):
            un = st.text_input("Username Admin", key="admin_un")
            pw = st.text_input("Password Admin", type="password", key="admin_pw")
            c1, c2 = st.columns(2)
            with c1:
                submit = st.form_submit_button("🔐 Masuk", use_container_width=True)
            with c2:
                cancel = st.form_submit_button("✖️ Batal", use_container_width=True)

            if submit:
                if not un or not pw:
                    st.error("Username dan password wajib diisi!")
                else:
                    with st.spinner("Memverifikasi..."):
                        ok, result = login_admin(un, pw)
                    if ok:
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_username = result["username"]
                        st.session_state.show_admin_login = False
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")

            if cancel:
                st.session_state.show_admin_login = False
                st.rerun()


# ─────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────
def get_all_users():
    res = supabase_admin.table("users").select("*").execute()
    return res.data or []


def get_all_logs():
    res = supabase_admin.table("health_logs").select("*").execute()
    return res.data or []


def hitung_skor(log):
    skor = 0
    t = log.get("jam_tidur", 0) or 0
    skor += 25 if 7 <= t <= 9 else (15 if (6 <= t < 7 or 9 < t <= 10) else (5 if t > 0 else 0))
    skor += min((log.get("makan_sehat", 0) or 0) * 8, 25)
    o = log.get("menit_olahraga", 0) or 0
    skor += 25 if o >= 30 else (15 if o >= 15 else (7 if o > 0 else 0))
    skor += max(0, 25 - (log.get("level_stres", 5) or 5) * 2.5)
    return round(skor)


def send_notifikasi(username: str, pesan: str):
    """Kirim notifikasi manual. Menambah notif_count & last_notif di tabel users.
    Kalau tabel 'notifications' tersedia, pesan juga disimpan di sana."""
    user = supabase_admin.table("users").select("notif_count").eq("username", username).execute()
    current = (user.data[0].get("notif_count") or 0) if user.data else 0

    supabase_admin.table("users").update({
        "notif_count": current + 1,
        "last_notif": datetime.now().isoformat(),
    }).eq("username", username).execute()

    try:
        supabase_admin.table("notifications").insert({
            "username": username,
            "message": pesan,
            "created_at": datetime.now().isoformat(),
        }).execute()
        return True, None
    except Exception:
        # tabel notifications belum dibuat — tetap sukses, cuma pesan tidak tersimpan
        return True, "notes_table_missing"


def add_user_manual(username, password, profil, is_admin=False):
    if len(username.strip()) < 3:
        return False, "Username minimal 3 karakter!"
    if len(password) < 6:
        return False, "Password minimal 6 karakter!"
    ex = supabase_admin.table("users").select("username").eq("username", username.lower().strip()).execute()
    if ex.data:
        return False, f"Username '{username}' sudah dipakai!"
    try:
        supabase_admin.table("users").insert({
            "username": username.lower().strip(),
            "password_hash": hash_pw(password),
            "nama": profil["nama"], "nim": profil["nim"],
            "prodi": profil["prodi"], "semester": profil["semester"],
            "tinggi_badan": profil["tb"], "berat_badan": profil["bb"],
            "target_tidur": profil["target_tidur"], "target_air": profil["target_air"],
            "imt": profil["imt"], "kat_imt": profil["kat_imt"],
            "is_admin": is_admin,
        }).execute()
        return True, "User berhasil ditambahkan!"
    except Exception as e:
        return False, str(e)


def to_excel_bytes(sheets: dict) -> bytes:
    """sheets = {'Nama Sheet': DataFrame, ...}"""
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
        return output.getvalue()
    except ImportError:
        return None


# ─────────────────────────────────────────────
# PANEL ADMIN UTAMA
# ─────────────────────────────────────────────
def render_admin_panel():
    with st.sidebar:
        st.markdown("## 🛡️ VitaCampus Admin")
        st.markdown(f'<div class="user-chip">👤 {st.session_state.admin_username}</div>', unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("Menu Admin", [
            "👥 Daftar User",
            "⚠️ Masalah Kesehatan",
            "📊 Statistik Kesehatan",
            "🔔 Kirim Notifikasi",
            "📤 Export Data",
            "➕ Tambah User",
        ], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout Admin"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_username = ""
            st.rerun()

    users = get_all_users()
    logs = get_all_logs()
    df_users = pd.DataFrame(users) if users else pd.DataFrame()
    df_logs = pd.DataFrame(logs) if logs else pd.DataFrame()

    # ── 1. DAFTAR USER ──
    if menu == "👥 Daftar User":
        st.markdown("# 👥 Daftar User Terdaftar")
        st.markdown("---")
        if df_users.empty:
            st.info("Belum ada user terdaftar.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total User", len(df_users))
            c2.metric("Total Admin", int(df_users.get("is_admin", pd.Series(dtype=bool)).sum()) if "is_admin" in df_users else 0)
            c3.metric("Total Mahasiswa", len(df_users) - (int(df_users.get("is_admin", pd.Series(dtype=bool)).sum()) if "is_admin" in df_users else 0))
            st.markdown("---")
            cols_show = [c for c in ["username", "nama", "nim", "prodi", "semester", "is_admin"] if c in df_users.columns]
            search = st.text_input("🔍 Cari nama / username / NIM")
            tampil = df_users[cols_show].copy()
            if search:
                mask = tampil.apply(lambda r: search.lower() in str(r).lower(), axis=1)
                tampil = tampil[mask]
            st.dataframe(tampil, use_container_width=True, hide_index=True)

    # ── 2. MASALAH KESEHATAN ──
    elif menu == "⚠️ Masalah Kesehatan":
        st.markdown("# ⚠️ Mahasiswa dengan Indikasi Masalah Kesehatan")
        st.markdown("Ditandai dari skor kesehatan rendah, stres tinggi, atau catatan terbaru.")
        st.markdown("---")
        if df_logs.empty:
            st.info("Belum ada data catatan kesehatan mahasiswa.")
        else:
            df_logs["skor"] = df_logs.apply(hitung_skor, axis=1)
            df_logs["tanggal"] = pd.to_datetime(df_logs["tanggal"])
            terbaru = df_logs.sort_values("tanggal").groupby("username").tail(1)
            bermasalah = terbaru[(terbaru["skor"] < 50) | (terbaru["level_stres"] >= 7)]
            bermasalah = bermasalah.merge(
                df_users[["username", "nama", "prodi"]] if not df_users.empty else pd.DataFrame(columns=["username", "nama", "prodi"]),
                on="username", how="left"
            )
            if bermasalah.empty:
                st.success("✅ Tidak ada mahasiswa dengan indikasi masalah kesehatan saat ini.")
            else:
                st.warning(f"Ditemukan **{len(bermasalah)} mahasiswa** yang perlu perhatian.")
                for _, row in bermasalah.sort_values("skor").iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row.get('nama', row['username'])}** ({row['username']}) — {row.get('prodi','—')}")
                        st.markdown(f"Skor: **{row['skor']}/100** | Stres: **{row['level_stres']}/10** | Tanggal: {row['tanggal'].strftime('%d %b %Y')}")
                        if row.get("catatan"):
                            st.markdown(f"💬 _{row['catatan']}_")

    # ── 3. STATISTIK KESEHATAN ──
    elif menu == "📊 Statistik Kesehatan":
        st.markdown("# 📊 Statistik Kesehatan Semua Mahasiswa")
        st.markdown("---")
        if df_logs.empty:
            st.info("Belum ada data catatan kesehatan.")
        else:
            df_logs["skor"] = df_logs.apply(hitung_skor, axis=1)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rata-rata Skor", round(df_logs["skor"].mean(), 1))
            c2.metric("Rata-rata Tidur", f"{round(df_logs['jam_tidur'].mean(),1)} j")
            c3.metric("Rata-rata Stres", round(df_logs["level_stres"].mean(), 1))
            c4.metric("Total Catatan", len(df_logs))
            st.markdown("---")
            import plotly.express as px
            fig1 = px.histogram(df_logs, x="skor", nbins=10, title="Distribusi Skor Kesehatan Mahasiswa",
                                 color_discrete_sequence=["#3D9970"])
            st.plotly_chart(fig1, use_container_width=True)
            fig2 = px.box(df_logs, y="level_stres", title="Sebaran Level Stres Mahasiswa",
                          color_discrete_sequence=["#ef5350"])
            st.plotly_chart(fig2, use_container_width=True)

    # ── 4. KIRIM NOTIFIKASI ──
    elif menu == "🔔 Kirim Notifikasi":
        st.markdown("# 🔔 Kirim Notifikasi Manual")
        st.markdown("---")
        if df_users.empty:
            st.info("Belum ada user.")
        else:
            target_mode = st.radio("Target", ["Satu Mahasiswa", "Semua Mahasiswa"], horizontal=True)
            with st.form("form_notif"):
                if target_mode == "Satu Mahasiswa":
                    opsi = [f"{r['username']} — {r.get('nama','')}" for _, r in df_users.iterrows() if not r.get("is_admin")]
                    pilih = st.selectbox("Pilih Mahasiswa", opsi)
                pesan = st.text_area("Isi Notifikasi", placeholder="Contoh: Jangan lupa isi catatan kesehatan harian ya!")
                kirim = st.form_submit_button("📨 Kirim Sekarang", use_container_width=True)

                if kirim:
                    if not pesan.strip():
                        st.error("Isi notifikasi tidak boleh kosong!")
                    else:
                        if target_mode == "Satu Mahasiswa":
                            target_username = pilih.split(" — ")[0]
                            targets = [target_username]
                        else:
                            targets = [r["username"] for _, r in df_users.iterrows() if not r.get("is_admin")]
                        with st.spinner("Mengirim..."):
                            warn_flag = False
                            for t in targets:
                                ok, note = send_notifikasi(t, pesan.strip())
                                if note == "notes_table_missing":
                                    warn_flag = True
                        st.success(f"✅ Notifikasi terkirim ke {len(targets)} mahasiswa!")
                        if warn_flag:
                            st.caption("ℹ️ Catatan: isi pesan belum tersimpan detail karena tabel `notifications` belum ada. "
                                       "Jalankan SQL berikut di Supabase agar pesan bisa tersimpan:")
                            st.code(
                                "CREATE TABLE IF NOT EXISTS notifications (\n"
                                "  id SERIAL PRIMARY KEY,\n"
                                "  username TEXT REFERENCES users(username),\n"
                                "  message TEXT,\n"
                                "  created_at TIMESTAMP DEFAULT now()\n"
                                ");",
                                language="sql"
                            )

    # ── 5. EXPORT DATA ──
    elif menu == "📤 Export Data":
        st.markdown("# 📤 Export Data & Statistik")
        st.markdown("---")
        if df_users.empty and df_logs.empty:
            st.info("Belum ada data untuk diexport.")
        else:
            st.markdown("### Pilih data yang ingin diexport")
            exp_users = st.checkbox("Data User / Mahasiswa", value=True)
            exp_logs = st.checkbox("Data Catatan Kesehatan (health logs)", value=True)

            colA, colB = st.columns(2)
            with colA:
                if st.button("⬇️ Download CSV", use_container_width=True):
                    if exp_users and not df_users.empty:
                        st.download_button("📄 users.csv", df_users.to_csv(index=False).encode("utf-8"),
                                            file_name="users.csv", mime="text/csv", key="dl_users_csv")
                    if exp_logs and not df_logs.empty:
                        st.download_button("📄 health_logs.csv", df_logs.to_csv(index=False).encode("utf-8"),
                                            file_name="health_logs.csv", mime="text/csv", key="dl_logs_csv")
            with colB:
                if st.button("⬇️ Download Excel (semua sheet)", use_container_width=True):
                    sheets = {}
                    if exp_users and not df_users.empty:
                        sheets["Users"] = df_users
                    if exp_logs and not df_logs.empty:
                        sheets["Health_Logs"] = df_logs
                    data = to_excel_bytes(sheets) if sheets else None
                    if data is None:
                        st.error("Gagal membuat file Excel. Pastikan library `openpyxl` sudah terinstall (`pip install openpyxl`).")
                    else:
                        st.download_button("📊 vitacampus_export.xlsx", data,
                                            file_name=f"vitacampus_export_{date.today()}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            key="dl_excel")

    # ── 6. TAMBAH USER MANUAL ──
    elif menu == "➕ Tambah User":
        st.markdown("# ➕ Tambah User Manual")
        st.markdown("Untuk membantu mahasiswa yang gagal mendaftar sendiri.")
        st.markdown("---")
        with st.form("form_tambah_user"):
            c1, c2 = st.columns(2)
            with c1:
                new_un = st.text_input("Username*")
                new_pw = st.text_input("Password*", type="password")
                new_nama = st.text_input("Nama Lengkap*")
                new_nim = st.text_input("NIM*")
                new_prodi = st.text_input("Program Studi*")
                new_semester = st.number_input("Semester*", 1, 14, 1)
            with c2:
                new_tb = st.number_input("Tinggi Badan (cm)*", 140, 220, 165)
                new_bb = st.number_input("Berat Badan (kg)*", 30, 150, 60)
                new_target_tidur = st.slider("Target Jam Tidur/Hari", 6.0, 10.0, 8.0, 0.5)
                new_target_air = st.slider("Target Gelas Air/Hari", 4, 15, 8)
                new_is_admin = st.checkbox("Jadikan admin?")

            if st.form_submit_button("✅ Tambah User", use_container_width=True):
                errors = []
                if not new_un.strip(): errors.append("Username wajib diisi!")
                if not new_pw: errors.append("Password wajib diisi!")
                if not new_nama.strip(): errors.append("Nama wajib diisi!")
                if not new_nim.strip(): errors.append("NIM wajib diisi!")
                if not new_prodi.strip(): errors.append("Program Studi wajib diisi!")

                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")
                else:
                    imt = new_bb / ((new_tb / 100) ** 2)
                    kat_imt = ("Kurang Berat Badan" if imt < 18.5 else "Normal" if imt < 25
                               else "Kelebihan Berat Badan" if imt < 30 else "Obesitas")
                    with st.spinner("Menambahkan user..."):
                        ok, msg = add_user_manual(new_un, new_pw, {
                            "nama": new_nama.strip(), "nim": new_nim.strip(),
                            "prodi": new_prodi.strip(), "semester": int(new_semester),
                            "tb": int(new_tb), "bb": int(new_bb),
                            "target_tidur": new_target_tidur, "target_air": int(new_target_air),
                            "imt": round(imt, 1), "kat_imt": kat_imt,
                        }, is_admin=new_is_admin)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
