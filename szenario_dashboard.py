# szenario_dashboard.py
# ============================================================
# ALL-IN-ONE: CONFIG + MODELS + LOGIC + UI + APP
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from dataclasses import dataclass
from typing import List, Tuple, Dict

# ============================================================
# 1. CONFIG
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

KPI_OPTIONS = {
    "Motivation": ["Hoch", "Niedrig"],
    "Offensive": ["Stark", "Schwach"],
    "Defensive": ["Stark", "Schwach"],
    "Spielweise": ["Aggressiv", "Defensiv"],
    "Taktik": ["Hoch stehend", "Tief stehend"],
    "Spielrelevanz": ["Hoch", "Niedrig"],
    "Formation": [
        "3-4-3 (sehr aggressiv)",
        "4-3-3 (aggressiv)",
        "3-5-2 (aggressiv/ausgewogen)",
        "4-2-3-1 (ausgewogen)",
        "4-4-2 (defensiv)",
        "5-3-2 (sehr defensiv)"
    ]
}

AGGRESSIVE_FORMATIONS = [
    "3-4-3 (sehr aggressiv)",
    "4-3-3 (aggressiv)",
    "3-5-2 (aggressiv/ausgewogen)"
]

COLORS = {
    "background": "#0A0A0A",
    "card_bg": "rgba(255, 255, 255, 0.02)",
    "border": "rgba(255, 255, 255, 0.06)",
    "gold": "#D4A853",
    "gold_light": "#F5D98E",
    "green": "#4CAF50",
    "red": "#EF5350",
    "white": "#FFFFFF",
    "text_muted": "rgba(255, 255, 255, 0.5)"
}

# ============================================================
# 2. MODELS
# ============================================================

@dataclass
class TeamScenario:
    kpis: Dict[str, str]
    bits: List[int] = None
    index: int = None
    bonus: int = None

    def __post_init__(self):
        self.bits = self.create_bits()
        self.index = self.calculate_index()
        self.bonus = self.calculate_bonus()

    def create_bits(self) -> List[int]:
        return [
            1 if self.kpis["Motivation"] == "Hoch" else 0,
            1 if self.kpis["Offensive"] == "Stark" else 0,
            1 if self.kpis["Defensive"] == "Stark" else 0,
            1 if self.kpis["Spielweise"] == "Aggressiv" else 0,
            1 if self.kpis["Taktik"] == "Hoch stehend" else 0,
            1 if self.kpis["Spielrelevanz"] == "Hoch" else 0,
            1 if self.kpis["Formation"] in AGGRESSIVE_FORMATIONS else 0
        ]

    def calculate_index(self) -> int:
        index = 0
        for i, bit in enumerate(self.bits):
            index += bit * (2 ** (6 - i))
        return index

    def calculate_bonus(self) -> int:
        return sum(self.bits)


@dataclass
class MatchScenario:
    team_a: TeamScenario
    team_b: TeamScenario

    @property
    def bonus_diff(self) -> int:
        return self.team_a.bonus - self.team_b.bonus

    @property
    def scenario_type(self) -> Tuple[str, str]:
        a, b = self.team_a.bonus, self.team_b.bonus
        if a >= 6 and b <= 1:
            return "Dominant (A)", "A ist extrem überlegen"
        elif b >= 6 and a <= 1:
            return "Dominant (B)", "B ist extrem überlegen"
        elif a >= 5 and b <= 2:
            return "Überlegen (A)", "A ist deutlich stärker"
        elif b >= 5 and a <= 2:
            return "Überlegen (B)", "B ist deutlich stärker"
        elif abs(a - b) <= 1:
            return "Ausgeglichen", "Beide Teams sind ausgeglichen"
        else:
            return "Standard", "A ist stärker" if a > b else "B ist stärker" if b > a else "Remis"

# ============================================================
# 3. LOGIC
# ============================================================

def get_possible_results(match: MatchScenario, max_goals: int = 8) -> List[Tuple[int, int, int]]:
    diff = match.bonus_diff
    possible = []
    for ga in range(0, max_goals + 1):
        gb = ga - diff
        if 0 <= gb <= max_goals:
            score = abs(ga - match.team_a.bonus) + abs(gb - match.team_b.bonus)
            possible.append((ga, gb, score))
    return sorted(possible, key=lambda x: x[2])

def get_best_guess(match: MatchScenario, max_goals: int = 8) -> Tuple[int, int]:
    results = get_possible_results(match, max_goals)
    if not results:
        return (0, 0)
    return (results[0][0], results[0][1])

def get_all_128_combinations() -> List[Tuple[int, str, int]]:
    combinations = []
    for i in range(128):
        bits = format(i, '07b')
        bonus = bin(i).count("1")
        combinations.append((i, bits, bonus))
    return combinations

def kpi_to_checkmark(kpi_dict: dict, kpi_name: str) -> str:
    state = kpi_dict.get(kpi_name, "Niedrig")
    if kpi_name == "Motivation":
        return "✅" if state == "Hoch" else "❌"
    elif kpi_name == "Offensive":
        return "✅" if state == "Stark" else "❌"
    elif kpi_name == "Defensive":
        return "✅" if state == "Stark" else "❌"
    elif kpi_name == "Spielweise":
        return "✅" if state == "Aggressiv" else "❌"
    elif kpi_name == "Taktik":
        return "✅" if state == "Hoch stehend" else "❌"
    elif kpi_name == "Spielrelevanz":
        return "✅" if state == "Hoch" else "❌"
    elif kpi_name == "Formation":
        return "✅" if state in AGGRESSIVE_FORMATIONS else "❌"
    return "❌"

# ============================================================
# 4. UI (Streamlit-Komponenten)
# ============================================================

def render_team_input(team_name: str, prefix: str) -> dict:
    st.markdown(f"### {team_name}")
    kpis = {}
    cols = st.columns(2)
    for i, kpi in enumerate(KPIS):
        with cols[i % 2]:
            kpis[kpi] = st.selectbox(
                kpi,
                options=KPI_OPTIONS[kpi],
                key=f"{prefix}_{kpi}"
            )
    return kpis

def render_bits(index: int) -> str:
    return format(index, '07b')

def render_calculation_pipeline(match: MatchScenario):
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">🧮 Berechnung</p>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1rem; text-align: center;">
                <div style="color: rgba(255,255,255,0.3); font-size: 0.8rem;">Bits</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{render_bits(match.team_a.index)}</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{render_bits(match.team_b.index)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1rem; text-align: center;">
                <div style="color: rgba(255,255,255,0.3); font-size: 0.8rem;">Index</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{match.team_a.index}</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{match.team_b.index}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1rem; text-align: center;">
                <div style="color: rgba(255,255,255,0.3); font-size: 0.8rem;">Bonus</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{match.team_a.bonus}</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{match.team_b.bonus}</div>
            </div>
        """, unsafe_allow_html=True)

def render_match_analysis(match: MatchScenario):
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📊 Matchanalyse</p>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Team A Bonus", match.team_a.bonus)
    with col2:
        st.metric("Team B Bonus", match.team_b.bonus)
    with col3:
        st.metric("Differenz", f"{match.bonus_diff:+d}")

def render_scenario(match: MatchScenario):
    scenario, reasoning = match.scenario_type
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📌 Szenario</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 700; color: #D4A853;">{scenario}</div>
            <div style="color: rgba(255,255,255,0.5);">{reasoning}</div>
        </div>
    """, unsafe_allow_html=True)

def render_best_guess(match: MatchScenario):
    ga, gb = get_best_guess(match)
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">🏆 Best Guess</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 3rem; font-weight: 800; color: #D4A853;">{ga} : {gb}</div>
        </div>
    """, unsafe_allow_html=True)

def render_possible_results(match: MatchScenario):
    results = get_possible_results(match)
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📋 Alle möglichen Ergebnisse</p>
        </div>
    """, unsafe_allow_html=True)
    data = []
    for ga, gb, score in results:
        data.append({"Ergebnis": f"{ga}:{gb}", "Abweichung": score})
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_kpi_comparison(kpis_a: dict, kpis_b: dict):
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📋 KPI-Vergleich</p>
        </div>
    """, unsafe_allow_html=True)
    data = []
    for kpi in KPIS:
        data.append({
            "KPI": kpi,
            "Team A": kpi_to_checkmark(kpis_a, kpi),
            "Team B": kpi_to_checkmark(kpis_b, kpi)
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_bonus_distribution():
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📊 Bonus-Verteilung</p>
        </div>
    """, unsafe_allow_html=True)
    counts = [bin(i).count("1") for i in range(128)]
    df = pd.DataFrame({"Bonus": counts})
    fig = px.histogram(df, x="Bonus", nbins=8, color_discrete_sequence=["#D4A853"])
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

def render_128_combinations():
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📊 Alle 128 Kombinationen</p>
        </div>
    """, unsafe_allow_html=True)
    combinations = get_all_128_combinations()
    df = pd.DataFrame(combinations, columns=["Index", "Bits", "Tor-Bonus"])
    st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================
# 5. STREAMLIT-STYLING (CSS)
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
    
    .stDataFrame { background: rgba(255, 255, 255, 0.02) !important; backdrop-filter: blur(8px); border-radius: 16px !important; border: 1px solid rgba(255, 255, 255, 0.04) !important; overflow: hidden; margin: 0 auto 1rem auto; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }
    .stDataFrame th { background: rgba(255, 255, 255, 0.03) !important; color: rgba(255, 255, 255, 0.2) !important; font-weight: 500 !important; font-size: 0.6rem !important; text-transform: uppercase !important; letter-spacing: 0.2em !important; text-align: center !important; padding: 0.8rem 1rem !important; border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important; }
    .stDataFrame td { background: transparent !important; color: rgba(255, 255, 255, 0.8) !important; text-align: center !important; padding: 0.7rem 1rem !important; font-size: 0.9rem !important; border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important; }
    .stDataFrame tr:hover td { background: rgba(255, 255, 255, 0.03) !important; }
    .stDataFrame tr:last-child td { border-bottom: none !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 6. APP (HAUPTPROGRAMM)
# ============================================================

st.markdown("""
    <div class="title-wrapper">
        <h1 class="main-title">📊 SZENARIO <span>DASHBOARD</span></h1>
    </div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───
st.sidebar.markdown("### 📖 Die 7 Schritte")
st.sidebar.markdown("""
1. **7 KPIs** – je 2 Zustände
2. **Bits** – stark = 1, schwach = 0
3. **Index** – 0 bis 127
4. **Tor-Bonus** – Anzahl der Bits
5. **Tordifferenz** – Bonus A – Bonus B
6. **Mögliche Ergebnisse** – alle mit dieser Differenz
7. **Best Guess** – minimale Abweichung von den Boni
""")
st.sidebar.markdown("---")
st.sidebar.caption("📅 Szenario Dashboard v2.0")

# ─── TEAM INPUT ───
st.markdown("""
    <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
        <p class="section-headline">⚽ Team-KPIs eingeben</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")

with col1:
    kpis_a = render_team_input("🟡 Team A", "a")

with col2:
    kpis_b = render_team_input("🔵 Team B", "b")

# ─── BERECHNUNG ───
team_a = TeamScenario(kpis_a)
team_b = TeamScenario(kpis_b)
match = MatchScenario(team_a, team_b)

st.markdown("---")

render_calculation_pipeline(match)
render_match_analysis(match)
render_scenario(match)
render_best_guess(match)
render_possible_results(match)

# ─── KPI-VERGLEICH ───
render_kpi_comparison(kpis_a, kpis_b)

# ─── BONUS-VERTEILUNG & 128 KOMBINATIONEN ───
render_bonus_distribution()
render_128_combinations()