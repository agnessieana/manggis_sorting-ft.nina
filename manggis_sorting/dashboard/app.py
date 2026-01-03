import streamlit as st
import time
import requests
from rules import RULES, GEJALA
from fuzzy_system import build_fuzzy_system

# ======================================================
# CONFIG
# ======================================================
FIREBASE_URL = "https://manggis-2955d-default-rtdb.asia-southeast1.firebasedatabase.app/"
DEVICE_TIMEOUT = 10
REFRESH_INTERVAL = 1 # detik (AMAN)

st.set_page_config(
    page_title="Dashboard Sortir Manggis",
    layout="wide"
)

# ======================================================
# SESSION STATE (WAJIB UNTUK AUTO REFRESH AMAN)
# ======================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# ======================================================
# GLOBAL STYLE
# ======================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    :root{
        --primary-purple: #C9A6FF; /* ungu muda */
        --soft-pink: #FFD7EA;      /* pink muda */
        --soft-yellow: #FFF3BF;    /* kuning soft */
        --bg-dark: #03040A;
        --card-dark: #0b0d12;
        --muted: #bfc5d6;
    }
    *{font-family: 'Poppins', sans-serif;}
    .block-container {
        padding-top: 1.2rem;
        max-width: 1200px;
    }
    h1, h2, h3 {
        color: #f3f4f6;
        margin-bottom: .4rem;
    }

    /* KPI card */
    .kpi-card{
        padding:18px;
        border-radius:14px;
        color:#07122a;
        min-height:110px;
        box-shadow: 0 8px 24px rgba(2,6,23,0.45);
        display:flex;
        flex-direction:column;
        justify-content:center;
    }
    .kpi-title{font-size:13px;opacity:0.9;color:var(--card-dark)}
    .kpi-value{font-size:32px;font-weight:700;margin-top:6px}

    /* device card */
    .device-card{
        background-color:var(--card-dark);
        padding:12px 14px;
        border-radius:12px;
        margin-bottom:10px;
        color:#e6e9f2;
        box-shadow:0 6px 20px rgba(0,0,0,0.35);
    }
    .device-row{display:flex;justify-content:space-between;align-items:center}
    .device-meta{font-size:13px;color:var(--muted)}
    .status-badge{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;vertical-align:middle}

    .muted{color:var(--muted);font-size:13px}
    .control-row{display:flex;gap:8px;align-items:center}

    /* small progress bar */
    .faux-progress{background:#11131a;border-radius:10px;padding:6px}
    .faux-fill{height:10px;background:linear-gradient(90deg,var(--primary-purple), var(--soft-pink));border-radius:8px}

</style>
""", unsafe_allow_html=True)

# ======================================================
# FIREBASE FUNCTIONS
# ======================================================
def get_summary():
    try:
        r = requests.get(f"{FIREBASE_URL}/summary.json", timeout=3)
        return r.json() if r.ok and r.json() else {}
    except:
        return {}

def get_logs(limit=20):
    try:
        r = requests.get(f"{FIREBASE_URL}/grading_results.json", timeout=3)
        if not r.ok or not r.json():
            return []
        return list(r.json().values())[-limit:]
    except:
        return []

def get_devices():
    try:
        r = requests.get(f"{FIREBASE_URL}/devices.json", timeout=3)
        return r.json() if r.ok and r.json() else {}
    except:
        return {}

# ======================================================
# UI COMPONENTS
# ======================================================
def kpi_card(title, value, color):
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, {color}, #0b0d12);">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def device_status_card(device, status, delta):
    color = "#7CE4A6" if status == "online" else "#FF9B9B"
    st.markdown(f"""
    <div class="device-card" style="border-left:6px solid {color};">
        <div class="device-row">
            <div><strong>{device}</strong></div>
            <div class="device-meta"><span class="status-badge" style="background:{color};"></span> <span style="color:{color}">{status.upper()}</span> • {delta}s</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# HELPER
# ======================================================
def interpretasi_keputusan(nilai, grade):
    if grade == 'A':
        if nilai >= 85: return "EKSPOR"
        elif nilai >= 65: return "LOKAL PREMIUM"
        else: return "PRODUK OLAHAN"
    elif grade == 'B':
        if nilai >= 60: return "LOKAL BIASA"
        else: return "PRODUK OLAHAN"
    elif grade == 'C':
        if nilai >= 50: return "DITUNDA HINGGA MATANG"
        else: return "PRODUK OLAHAN"
    return "TIDAK DIKETAHUI"

# ======================================================
# HEADER
# ======================================================
st.title("Dashboard Sortir Manggis")
st.caption("Sistem Monitoring IoT & Sistem Pakar Kualitas Buah Manggis")
st.divider()

# ======================================================
# SIDEBAR
# ======================================================
menu = st.sidebar.radio(
    "MENU UTAMA",
    [
        "Realtime Monitoring",
        "Histori Grading",
        "Diagnosa Penyakit",
        "Kelayakan Pasar"
    ]
)

# Auto-refresh controls
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 1

st.sidebar.checkbox("Auto-refresh", value=st.session_state.auto_refresh, key="auto_refresh")
if st.session_state.auto_refresh:
    st.sidebar.slider("Refresh interval (s)", 1, 10, st.session_state.refresh_interval, key="refresh_interval")

# ======================================================
# Realtime Monitoring (Auto-refresh optional)
# ======================================================
if menu == "Realtime Monitoring":
    st.markdown("### Overview Produksi Hari Ini")
    st.caption("Live — data diperbarui otomatis bila Auto-refresh aktif")

    summary = get_summary()
    col1, col2, col3 = st.columns(3)

    with col1:
        kpi_card("Grade A (Premium)", summary.get("grade_1", 0), "#C9A6FF")
    with col2:
        kpi_card("Grade B (Lokal)", summary.get("grade_2", 0), "#FFD7EA")
    with col3:
        kpi_card("Grade C (Sortir)", summary.get("grade_3", 0), "#FFF3BF")

    st.divider()
    st.markdown("### Status Perangkat IoT")

    devices = get_devices()
    now = int(time.time())

    if not devices:
        st.warning("Belum ada perangkat terhubung")
    else:
        for device_id, data in devices.items():
            delta = now - data.get("last_seen", 0)
            status = "online" if delta <= DEVICE_TIMEOUT else "offline"
            device_status_card(device_id, status, delta)

    # Controlled auto-refresh using sidebar settings
    if st.session_state.get("auto_refresh", True):
        if time.time() - st.session_state.last_refresh >= st.session_state.get("refresh_interval", 1):
            st.session_state.last_refresh = time.time()
            st.rerun()



# ======================================================
# Histori Grading (Filterable)
# ======================================================
elif menu == "Histori Grading":
    st.markdown("### Riwayat Grading Terakhir")
    logs = get_logs()

    if not logs:
        st.info("Belum ada histori grading")
    else:
        colf1, colf2, colf3 = st.columns([1,1,1])
        with colf1:
            grade_filter = st.selectbox("Filter Grade", ["Semua","A","B","C"])
        with colf2:
            device_search = st.text_input("Cari Device ID")
        with colf3:
            limit = st.slider("Jumlah tampilan", 5, 100, 20)

        # apply filters
        filtered = []
        for log in reversed(logs):
            if grade_filter != "Semua" and log.get('grade') != grade_filter:
                continue
            if device_search and device_search.lower() not in log.get('device_id','').lower():
                continue
            filtered.append(log)

        filtered = filtered[:limit]

        with st.expander("Klik untuk melihat detail"):
            for log in filtered:
                waktu = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(log["timestamp"])
                )
                st.markdown(f"""
                **Grade {log['grade']} ({log['grade_label']})**  
                Device: `{log['device_id']}`  
                Waktu: {waktu}
                """)
                st.divider()

# ======================================================
# Diagnosa Penyakit
# ======================================================
elif menu == "Diagnosa Penyakit":
    st.markdown("### Diagnosa Penyakit Tanaman")
    st.info("Centang gejala yang terlihat pada tanaman manggis")

    with st.form("diagnosa"):
        user_gejala = {
            kode: st.checkbox(f"{kode} — {desc}")
            for kode, desc in GEJALA.items()
        }
        submitted = st.form_submit_button("Analisis Penyakit")

    if submitted:
        hasil = {}
        for penyakit, daftar_gejala in RULES.items():
            cocok = sum(user_gejala.get(g, False) for g in daftar_gejala)
            if cocok > 0:
                hasil[penyakit] = round((cocok / len(daftar_gejala)) * 100, 2)

        st.divider()
        if not hasil:
            st.success("Tanaman dalam kondisi sehat")
        else:
            for p, nilai in sorted(hasil.items(), key=lambda x: x[1], reverse=True):
                st.warning(f"{p} ({nilai}%)")
                st.progress(int(nilai))

# ======================================================
# Kelayakan Pasar (Fuzzy)
# ======================================================
elif menu == "Kelayakan Pasar":
    st.markdown("### Sistem Pakar Kelayakan Pasar")
    st.caption("Metode Fuzzy Logic")

    col1, col2 = st.columns([1, 2])

    with col1:
        grade = st.selectbox("Grade Manggis", ["A", "B", "C"])

    with col2:
        busuk = st.slider("Busuk (%)", 0, 100, 0)
        cacat = st.slider("Cacat Fisik (%)", 0, 100, 0)
        cuping = st.slider("Cuping Rusak (%)", 0, 100, 0)

    if st.button("Hitung Kelayakan"):
        sistem = build_fuzzy_system(grade)
        sistem.input['busuk'] = busuk
        sistem.input['cacat'] = cacat
        sistem.input['cuping'] = cuping

        try:
            sistem.compute()
            nilai = sistem.output['keputusan']
            rekomendasi = interpretasi_keputusan(nilai, grade)

            st.divider()
            st.metric("Skor Kelayakan", f"{nilai:.2f}")
            st.progress(int(nilai))

            if rekomendasi == "EKSPOR":
                st.success(f"{rekomendasi}")
            elif "LOKAL" in rekomendasi:
                st.info(f"{rekomendasi}")
            elif "DITUNDA" in rekomendasi:
                st.warning(f"{rekomendasi}")
            else:
                st.error(f"{rekomendasi}")

        except:
            st.error("Terjadi kesalahan pada perhitungan fuzzy")
