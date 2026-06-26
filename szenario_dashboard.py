# szenario_dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime

# ============================================================
# 1. PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Szenario-Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# 2. ULTRA LUXURY CSS (Dark Luxury Design)
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; box-sizing: border-box; margin: 0; padding: 0; }
    .stApp { background: linear-gradient(160deg, #0A0A0A 0%, #1A1A1A 35%, #222222 65%, #0A0A0A 100%); min-height: 100vh; }
    .stApp::before { content: ''; position: fixed; top: -20%; left: -20%; width: 140%; height: 140%; background: radial-gradient(ellipse at 40% 30%, rgba(212, 168, 83, 0.03) 0%, transparent 60%); pointer-events: none; z-index: 0; }
    .main > div { background: transparent; max-width: 1300px; margin: 0 auto; padding: 2rem 2rem 4rem 2rem; position: relative; z-index: 1; }
    .block-container { padding-top: 1.5rem; padding-bottom: 4rem; max-width: 1300px; margin: 0 auto; }
    
    .title-wrapper { display: flex; justify-content: center; width: 100%; margin: 0 auto 1.2rem auto; max-width: 700px; white-space: nowrap; }
    .main-title { font-size: 2.6rem; font-weight: 800; letter-spacing: 0.04em; text-align: center; margin: 0; color: #FFFFFF; line-height: 1.2; width: 100%; text-shadow: 0 2px 40px rgba(212, 168, 83, 0.05); white-space: nowrap; }
    .main-title span { background: linear-gradient(135deg, #D4A853 0%, #F5D98E 50%, #D4A853 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    
    .section-headline { font-size: 1.1rem !important; font-weight: 500; text-transform: uppercase; letter-spacing: 0.15em; color: rgba(255, 255, 255, 0.35) !important; text-align: center; margin: 0; }
    
    .result-box { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; text-align: center; }
    .result-box .scenario { font-size: 1.6rem; font-weight: 700; color: #D4A853; margin-bottom: 0.3rem; }
    .result-box .tip { font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin-bottom: 0.3rem; }
    .result-box .detail { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }
    
    .stDataFrame { background: rgba(255, 255, 255, 0.02) !important; backdrop-filter: blur(8px); border-radius: 16px !important; border: 1px solid rgba(255, 255, 255, 0.04) !important; overflow: hidden; margin: 0 auto 1rem auto; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }
    .stDataFrame th { background: rgba(255, 255, 255, 0.03) !important; color: rgba(255, 255, 255, 0.2) !important; font-weight: 500 !important; font-size: 0.6rem !important; text-transform: uppercase !important; letter-spacing: 0.2em !important; text-align: center !important; padding: 0.8rem 1rem !important; border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important; }
    .stDataFrame td { background: transparent !important; color: rgba(255, 255, 255, 0.8) !important; text-align: center !important; padding: 0.7rem 1rem !important; font-size: 0.9rem !important; border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important; }
    .stDataFrame tr:hover td { background: rgba(255, 255, 255, 0.03) !important; }
    .stDataFrame tr:last-child td { border-bottom: none !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. TITLE
# ============================================================
st.markdown("""
    <div class="title-wrapper">
        <h1 class="main-title">📊 SZENARIO <span>DASHBOARD</span></h1>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# 4. KPI-DEFINITIONEN
# ============================================================
KPIS = [
    "Motivation",
    "Offensive",
    "Defensive",
    "Spielweise",
    "Taktik",
    "Spielrelevanz",
    "Formation"
]

# Formationen (sortiert nach Aggressivität)
FORMATIONEN = [
    "3-4-3 (sehr aggressiv)",
    "4-3-3 (aggressiv)",
    "3-5-2 (aggressiv/ausgewogen)",
    "4-2-3-1 (ausgewogen)",
    "4-4-2 (defensiv)",
    "5-3-2 (sehr defensiv)"
]

# KPI-Optionen für Dropdowns
KPI_OPTIONS = {
    "Offensive": ["Stark", "Schwach"],
    "Defensive": ["Stark", "Schwach"],
    "Spielweise": ["Aggressiv", "Defensiv"],
    "Taktik": ["Hoch stehend", "Tief stehend"],
    "Spielrelevanz": ["Hoch", "Niedrig"],
    "Formation": FORMATIONEN
}

# ============================================================
# 5. SZENARIO-LOGIK
# ============================================================

def encode_kpi_value(kpi, value):
    """Wandelt KPI-Werte in numerische Werte um (für Berechnungen)"""
    if kpi == "Motivation":
        return value  # 1-10
    elif kpi in ["Offensive", "Defensive"]:
        return 10 if value == "Stark" else 3
    elif kpi == "Spielweise":
        return 10 if value == "Aggressiv" else 4
    elif kpi == "Taktik":
        return 10 if value == "Hoch stehend" else 4
    elif kpi == "Spielrelevanz":
        return 10 if value == "Hoch" else 3
    elif kpi == "Formation":
        # Formationen nach Aggressivität bewerten (0-10)
        formation_map = {
            "3-4-3 (sehr aggressiv)": 10,
            "4-3-3 (aggressiv)": 8,
            "3-5-2 (aggressiv/ausgewogen)": 7,
            "4-2-3-1 (ausgewogen)": 6,
            "4-4-2 (defensiv)": 4,
            "5-3-2 (sehr defensiv)": 2
        }
        return formation_map.get(value, 5)
    return 5

def encode_kpi_binary(kpi, value):
    """Wandelt KPI-Werte in binäre Werte um (0/1 für stark/schwach)"""
    if kpi == "Motivation":
        return 1 if value >= 7 else 0
    elif kpi in ["Offensive", "Defensive"]:
        return 1 if value == "Stark" else 0
    elif kpi == "Spielweise":
        return 1 if value == "Aggressiv" else 0
    elif kpi == "Taktik":
        return 1 if value == "Hoch stehend" else 0
    elif kpi == "Spielrelevanz":
        return 1 if value == "Hoch" else 0
    elif kpi == "Formation":
        return 1 if value in ["3-4-3 (sehr aggressiv)", "4-3-3 (aggressiv)", "3-5-2 (aggressiv/ausgewogen)"] else 0
    return 0

def get_formation_aggressiveness(value):
    """Gibt die Aggressivität der Formation zurück (1-5)"""
    map = {
        "3-4-3 (sehr aggressiv)": 5,
        "4-3-3 (aggressiv)": 4,
        "3-5-2 (aggressiv/ausgewogen)": 3,
        "4-2-3-1 (ausgewogen)": 3,
        "4-4-2 (defensiv)": 2,
        "5-3-2 (sehr defensiv)": 1
    }
    return map.get(value, 3)

def determine_scenario(kpi_a, kpi_b):
    """
    Bestimmt das Szenario basierend auf den 7 KPIs beider Teams.
    Gibt zurück: (Szenario-Typ, bestes Ergebnis, Tordifferenz, Tendenz)
    """
    
    # Numerische Werte berechnen
    values_a = {}
    values_b = {}
    binary_a = {}
    binary_b = {}
    
    for kpi in KPIS:
        values_a[kpi] = encode_kpi_value(kpi, kpi_a[kpi])
        values_b[kpi] = encode_kpi_value(kpi, kpi_b[kpi])
        binary_a[kpi] = encode_kpi_binary(kpi, kpi_a[kpi])
        binary_b[kpi] = encode_kpi_binary(kpi, kpi_b[kpi])
    
    # Durchschnittswerte
    avg_a = sum(values_a.values()) / len(values_a)
    avg_b = sum(values_b.values()) / len(values_b)
    
    # Motivation
    mot_a = kpi_a["Motivation"]
    mot_b = kpi_b["Motivation"]
    
    # Offensive/Defensive
    off_a = 1 if kpi_a["Offensive"] == "Stark" else 0
    off_b = 1 if kpi_b["Offensive"] == "Stark" else 0
    def_a = 1 if kpi_a["Defensive"] == "Stark" else 0
    def_b = 1 if kpi_b["Defensive"] == "Stark" else 0
    
    # Spielweise
    agg_a = 1 if kpi_a["Spielweise"] == "Aggressiv" else 0
    agg_b = 1 if kpi_b["Spielweise"] == "Aggressiv" else 0
    
    # Taktik
    high_a = 1 if kpi_a["Taktik"] == "Hoch stehend" else 0
    high_b = 1 if kpi_b["Taktik"] == "Hoch stehend" else 0
    
    # Spielrelevanz
    rel_a = 1 if kpi_a["Spielrelevanz"] == "Hoch" else 0
    rel_b = 1 if kpi_b["Spielrelevanz"] == "Hoch" else 0
    
    # Formation (Aggressivität 1-5)
    form_a = get_formation_aggressiveness(kpi_a["Formation"])
    form_b = get_formation_aggressiveness(kpi_b["Formation"])
    
    # ─── SZENARIO-BESTIMMUNG ───
    
    # 1. Motivation + Spielrelevanz Extrem (Muss-Sieg)
    if mot_a >= 8 and rel_a == 1 and mot_b <= 5 and rel_b == 0:
        return "Muss-Sieg (A)", "2:1 oder 3:1", "2 Tore", "A muss gewinnen und wird aggressiv spielen"
    if mot_b >= 8 and rel_b == 1 and mot_a <= 5 and rel_a == 0:
        return "Muss-Sieg (B)", "1:2 oder 1:3", "2 Tore", "B muss gewinnen und wird aggressiv spielen"
    
    # 2. Dominant (Team A ist deutlich überlegen)
    if avg_a >= 8 and avg_b <= 4:
        return "Dominant (A)", "3:0 oder 2:0", "2-3 Tore", "A ist in fast allen KPIs überlegen"
    if avg_b >= 8 and avg_a <= 4:
        return "Dominant (B)", "0:3 oder 0:2", "2-3 Tore", "B ist in fast allen KPIs überlegen"
    
    # 3. Kompakt (Defensive stark, Offensive schwach, tiefe Taktik)
    if def_a == 1 and off_a == 0 and high_a == 0:
        return "Kompakt (A)", "0:0 oder 1:0", "0-1 Tore", "A steht tief und verteidigt stark"
    if def_b == 1 and off_b == 0 and high_b == 0:
        return "Kompakt (B)", "0:0 oder 0:1", "0-1 Tore", "B steht tief und verteidigt stark"
    
    # 4. Risiko (Aggressive Formation + schwache Defensive)
    if form_a >= 4 and def_a == 0:
        return "Risiko (A)", "2:1 oder 1:2", "1-2 Tore", "A spielt aggressiv, Defensive ist anfällig"
    if form_b >= 4 and def_b == 0:
        return "Risiko (B)", "1:2 oder 2:1", "1-2 Tore", "B spielt aggressiv, Defensive ist anfällig"
    
    # 5. Ausgeglichen (ähnliche Werte)
    if abs(avg_a - avg_b) <= 2:
        return "Ausgeglichen", "1:1", "0-1 Tore", "Beide Teams sind sehr ausgeglichen"
    
    # 6. Überraschung (Motivation hoch + Defensive stark + tiefe Taktik)
    if mot_a >= 8 and def_a == 1 and high_a == 0:
        return "Überraschung (A)", "1:0 oder 2:1", "1 Tor", "A ist hoch motiviert und defensiv stark"
    if mot_b >= 8 and def_b == 1 and high_b == 0:
        return "Überraschung (B)", "0:1 oder 1:2", "1 Tor", "B ist hoch motiviert und defensiv stark"
    
    # 7. Standard (alles andere)
    if avg_a > avg_b:
        return "Standard (A)", "2:0", "2 Tore", "A ist insgesamt stärker"
    elif avg_b > avg_a:
        return "Standard (B)", "0:2", "2 Tore", "B ist insgesamt stärker"
    else:
        return "Standard (Remis)", "1:1", "0-1 Tore", "Remis ist wahrscheinlich"

# ============================================================
# 6. DASHBOARD
# ============================================================

# ─── SPIELER-INPUT ───
st.markdown("""
    <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
        <p class="section-headline">⚽ Team-KPIs eingeben</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")

# ─── TEAM A ───
with col1:
    st.markdown("### 🟡 Team A")
    
    team_a = {}
    
    # Motivation (Slider 1-10)
    team_a["Motivation"] = st.slider(
        "Motivation (1–10)",
        min_value=1, max_value=10, value=7,
        key="mot_a",
        help="Wie hoch ist die Motivation? 1 = sehr niedrig, 10 = extrem hoch"
    )
    
    # Offensive
    team_a["Offensive"] = st.selectbox(
        "Offensive",
        options=["Stark", "Schwach"],
        key="off_a"
    )
    
    # Defensive
    team_a["Defensive"] = st.selectbox(
        "Defensive",
        options=["Stark", "Schwach"],
        key="def_a"
    )
    
    # Spielweise
    team_a["Spielweise"] = st.selectbox(
        "Spielweise",
        options=["Aggressiv", "Defensiv"],
        key="spiel_a"
    )
    
    # Taktik
    team_a["Taktik"] = st.selectbox(
        "Taktik",
        options=["Hoch stehend", "Tief stehend"],
        key="takt_a"
    )
    
    # Spielrelevanz
    team_a["Spielrelevanz"] = st.selectbox(
        "Spielrelevanz",
        options=["Hoch", "Niedrig"],
        key="rel_a"
    )
    
    # Formation
    team_a["Formation"] = st.selectbox(
        "Formation",
        options=FORMATIONEN,
        key="form_a"
    )

# ─── TEAM B ───
with col2:
    st.markdown("### 🔵 Team B")
    
    team_b = {}
    
    # Motivation (Slider 1-10)
    team_b["Motivation"] = st.slider(
        "Motivation (1–10)",
        min_value=1, max_value=10, value=6,
        key="mot_b",
        help="Wie hoch ist die Motivation? 1 = sehr niedrig, 10 = extrem hoch"
    )
    
    # Offensive
    team_b["Offensive"] = st.selectbox(
        "Offensive",
        options=["Stark", "Schwach"],
        key="off_b"
    )
    
    # Defensive
    team_b["Defensive"] = st.selectbox(
        "Defensive",
        options=["Stark", "Schwach"],
        key="def_b"
    )
    
    # Spielweise
    team_b["Spielweise"] = st.selectbox(
        "Spielweise",
        options=["Aggressiv", "Defensiv"],
        key="spiel_b"
    )
    
    # Taktik
    team_b["Taktik"] = st.selectbox(
        "Taktik",
        options=["Hoch stehend", "Tief stehend"],
        key="takt_b"
    )
    
    # Spielrelevanz
    team_b["Spielrelevanz"] = st.selectbox(
        "Spielrelevanz",
        options=["Hoch", "Niedrig"],
        key="rel_b"
    )
    
    # Formation
    team_b["Formation"] = st.selectbox(
        "Formation",
        options=FORMATIONEN,
        key="form_b"
    )

# ─── ERGEBNIS ───
st.markdown("---")

scenario, tip, diff, reasoning = determine_scenario(team_a, team_b)

st.markdown("""
    <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
        <p class="section-headline">📊 Szenario</p>
    </div>
""", unsafe_allow_html=True)

# Ergebnis-Box
st.markdown(f"""
    <div class="result-box">
        <div class="scenario">📌 {scenario}</div>
        <div class="tip">🏆 {tip}</div>
        <div class="detail">Tordifferenz: {diff}</div>
        <div class="detail" style="margin-top: 0.5rem;">{reasoning}</div>
    </div>
""", unsafe_allow_html=True)

# ─── KPI-ÜBERSICHT ───
st.markdown("### 📋 KPI-Übersicht")

kpi_data = []
for kpi in KPIS:
    val_a = team_a[kpi]
    val_b = team_b[kpi]
    kpi_data.append({
        "KPI": kpi,
        "Team A": val_a,
        "Team B": val_b
    })

df_kpi = pd.DataFrame(kpi_data)
st.dataframe(df_kpi, use_container_width=True, hide_index=True)

# ─── GEWICHTUNG ANZEIGEN ───
with st.expander("🔍 Wie wird das Szenario berechnet?"):
    st.markdown("""
    **Gewichtung der KPIs für das Szenario:**

    | KPI | Gewichtung | Begründung |
    |-----|------------|------------|
    | **Motivation** | 25 % | Entscheidend bei Turnieren – "Muss-Siege" |
    | **Offensive** | 15 % | Torgefahr |
    | **Defensive** | 15 % | Stabilität |
    | **Spielweise** | 10 % | Aggressiv/Defensiv beeinflusst das Spiel |
    | **Taktik** | 10 % | Hoch/Tief stehend beeinflusst die Räume |
    | **Spielrelevanz** | 15 % | Was steht auf dem Spiel? |
    | **Formation** | 10 % | 3er-Kette vs. 4er-Kette |

    **Die Berechnung:**
    1. Jeder KPI wird in einen numerischen Wert umgewandelt (1–10).
    2. Es werden die Durchschnitte für Team A und Team B berechnet.
    3. Es wird geprüft, welche Szenario-Regeln zutreffen (Motivation, Defensive, Formation, etc.).
    4. Das wahrscheinlichste Szenario wird ausgegeben.
    """)

# ─── SIDEBAR ───
st.sidebar.markdown("### 📖 Anleitung")
st.sidebar.markdown("""
1. **Motivation** – Wie hoch ist die Motivation? (1–10)
2. **Offensive** – Ist die Offensive stark oder schwach?
3. **Defensive** – Ist die Defensive stark oder schwach?
4. **Spielweise** – Spielt das Team aggressiv oder defensiv?
5. **Taktik** – Steht das Team hoch oder tief?
6. **Spielrelevanz** – Ist das Spiel wichtig oder nicht?
7. **Formation** – Welche Formation wird gespielt?

**Das Dashboard berechnet automatisch das Szenario + bestes Ergebnis.** 🚀
""")

st.sidebar.markdown("---")
st.sidebar.caption(f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}")