# szenario_dashboard.py
# ============================================================
# ALL-IN-ONE: CONFIG + MODELS + LOGIC (MIT MODULATION & POISSON) + UI + APP
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass
from typing import List, Tuple, Dict
import math

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

# Feinjustierte Lambda-Map für realistischere Poisson-Erwartungswerte
LAMBDA_MAP = {
    0: 0.0,
    1: 0.64,
    2: 1.20,
    3: 1.76,
    4: 2.40,
    5: 3.04,
    6: 3.52,
    7: 4.00
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
# 3. LOGIC (MIT MODULATION, POISSON, SZENARIO-ENGINE)
# ============================================================

def modulate_kpis(kpis: dict) -> dict:
    """
    Moduliert die KPIs basierend auf Motivation und Spielrelevanz.
    Gibt ein Dictionary mit den effektiven Zuständen zurück.
    """
    offensive = kpis["Offensive"]
    defensive = kpis["Defensive"]
    spielweise = kpis["Spielweise"]
    taktik = kpis["Taktik"]
    motivation = kpis["Motivation"]
    relevanz = kpis["Spielrelevanz"]

    # ─── MODULATION DURCH MOTIVATION ───
    if motivation == "Hoch":
        if offensive == "Stark":
            offensive_eff = "Stark (verstärkt)"
        else:
            offensive_eff = "Mittel (verstärkt)"

        if defensive == "Stark":
            defensive_eff = "Stark (verstärkt)"
        else:
            defensive_eff = "Mittel (verstärkt)"

        if spielweise == "Aggressiv":
            spielweise_eff = "Aggressiv (sehr)"
        else:
            spielweise_eff = "Aggressiv (moderat)"

    else:  # Motivation = Niedrig
        if offensive == "Stark":
            offensive_eff = "Mittel (abgeschwächt)"
        else:
            offensive_eff = "Schwach (abgeschwächt)"

        if defensive == "Stark":
            defensive_eff = "Mittel (abgeschwächt)"
        else:
            defensive_eff = "Schwach (abgeschwächt)"

        if spielweise == "Aggressiv":
            spielweise_eff = "Defensiv (abgeschwächt)"
        else:
            spielweise_eff = "Defensiv (sehr)"

    # ─── MODULATION DURCH SPIELRELEVANZ ───
    if relevanz == "Hoch":
        if "Stark" in defensive_eff or "Mittel" in defensive_eff:
            defensive_eff = "Stark (sehr)"
        else:
            defensive_eff = "Mittel (verstärkt)"

        if "Aggressiv" in spielweise_eff:
            spielweise_eff = "Aggressiv (sehr)"
        else:
            spielweise_eff = "Aggressiv (moderat)"

    else:  # Relevanz = Niedrig
        if "Stark" in offensive_eff or "Mittel" in offensive_eff:
            offensive_eff = "Mittel (abgeschwächt)"
        else:
            offensive_eff = "Schwach (abgeschwächt)"

        if "Aggressiv" in spielweise_eff:
            spielweise_eff = "Defensiv (abgeschwächt)"
        else:
            spielweise_eff = "Defensiv (sehr)"

    return {
        "Offensive": offensive_eff,
        "Defensive": defensive_eff,
        "Spielweise": spielweise_eff,
        "Taktik": taktik,
        "Motivation": motivation,
        "Spielrelevanz": relevanz,
        "Formation": kpis["Formation"]
    }

def analyze_scenario(team_a_kpis: dict, team_b_kpis: dict) -> Dict:
    """
    Erweiterte Szenario-Engine mit vielen Fallunterscheidungen.
    """
    mod_a = modulate_kpis(team_a_kpis)
    mod_b = modulate_kpis(team_b_kpis)

    a_off = mod_a["Offensive"]
    a_def = mod_a["Defensive"]
    a_spiel = mod_a["Spielweise"]
    a_taktik = mod_a["Taktik"]
    a_mot = mod_a["Motivation"]
    a_rel = mod_a["Spielrelevanz"]

    b_off = mod_b["Offensive"]
    b_def = mod_b["Defensive"]
    b_spiel = mod_b["Spielweise"]
    b_taktik = mod_b["Taktik"]
    b_mot = mod_b["Motivation"]
    b_rel = mod_b["Spielrelevanz"]

    # ─── SZENARIO FÜR TEAM A ───
    if "Stark" in a_off and "Schwach" in a_def and "Aggressiv" in a_spiel:
        if a_mot == "Hoch" and a_rel == "Hoch":
            szenario_a = "⚡ Offensiv-Show (extrem)"
            beschreibung_a = "Team A spielt extrem offensiv – Motivation und Relevanz verstärken den Drang nach vorne."
            tendenz_a = "4:2, 5:3"
        elif a_mot == "Niedrig" and a_rel == "Niedrig":
            szenario_a = "📉 Offensiv-Show (abgeschwächt)"
            beschreibung_a = "Team A spielt offensiv, aber ohne echten Druck – Motivation und Relevanz fehlen."
            tendenz_a = "2:1, 1:1"
        else:
            szenario_a = "⚽ Offensiv-Show (normal)"
            beschreibung_a = "Team A spielt offensiv, aber ohne extreme Verstärkung durch Motivation oder Relevanz."
            tendenz_a = "3:2, 2:2"
    elif "Stark" in a_def and "Schwach" in a_off and "Tief stehend" in a_taktik:
        if a_mot == "Hoch" and a_rel == "Hoch":
            szenario_a = "🛡️ Beton-Mauer (extrem)"
            beschreibung_a = "Team A steht extrem tief, verteidigt mit allem – muss unbedingt gewinnen."
            tendenz_a = "0:0, 1:0"
        else:
            szenario_a = "🧱 Beton-Mauer (normal)"
            beschreibung_a = "Team A steht tief und verteidigt kompakt."
            tendenz_a = "0:0, 0:1"
    elif "Stark" in a_def and "Stark" in a_off and "Aggressiv" in a_spiel:
        if a_mot == "Hoch" and a_rel == "Hoch":
            szenario_a = "🔥 Dominant (extrem)"
            beschreibung_a = "Team A dominiert das Spiel – hohe Motivation und Relevanz verstärken die Kontrolle."
            tendenz_a = "3:0, 4:1"
        else:
            szenario_a = "🔥 Dominant (normal)"
            beschreibung_a = "Team A kontrolliert das Spiel, aber ohne extreme Intensität."
            tendenz_a = "2:0, 2:1"
    elif "Schwach" in a_off and "Schwach" in a_def and "Defensiv" in a_spiel:
        if a_mot == "Hoch":
            szenario_a = "🌀 Verzweifelt (hohe Motivation)"
            beschreibung_a = "Team A ist schwach, aber motiviert – kämpft um jeden Ball."
            tendenz_a = "0:0, 1:1"
        else:
            szenario_a = "😴 Harmlos"
            beschreibung_a = "Team A ist weder offensiv noch defensiv überzeugend."
            tendenz_a = "0:2, 0:3"
    elif "Stark" in a_off and "Stark" in a_def and "Defensiv" in a_spiel:
        szenario_a = "⚖️ Kontrollierte Defensive"
        beschreibung_a = "Team A steht hoch, aber spielt defensiv – kontrolliert, nicht aggressiv."
        tendenz_a = "1:0, 2:0"
    elif "Tief stehend" in a_taktik and "Aggressiv" in a_spiel and "Stark" in a_off and "Stark" in a_def:
        szenario_a = "🚀 Aggressiver Konter"
        beschreibung_a = "Team A steht tief, aber schaltet schnell um – gefährlich bei Kontern."
        tendenz_a = "2:1, 1:1"
    elif "Tief stehend" in a_taktik and "Aggressiv" in a_spiel and "Stark" in a_off and "Schwach" in a_def:
        szenario_a = "🔄 Konter-Risiko"
        beschreibung_a = "Aggressiver Konter, aber Defensive anfällig – viele Tore auf beiden Seiten."
        tendenz_a = "3:2, 2:2"
    elif "Hoch stehend" in a_taktik and "Defensiv" in a_spiel and "Stark" in a_off and "Stark" in a_def:
        szenario_a = "⚖️ Kontrollierte Defensive (hoch)"
        beschreibung_a = "Team A steht hoch, aber spielt defensiv – kontrolliert, nicht aggressiv."
        tendenz_a = "1:0, 2:0"
    else:
        szenario_a = "📊 Standard"
        beschreibung_a = "Ausgeglichene Taktik – keine extremen Wechselwirkungen."
        tendenz_a = "1:1, 2:1, 1:2"

    # ─── MATCH-SZENARIO (Kombination) ───
    # Berücksichtige auch Team B
    if "Beton-Mauer" in szenario_a and "Offensiv-Show" in b_off and "Aggressiv" in b_spiel:
        szenario_match = "🔄 Offensiv-Show vs. Beton-Mauer"
        beschreibung_match = "Team B drückt, Team A steht tief. Team B wird viele Chancen haben, aber Team A verteidigt kompakt."
        tendenz_match = "1:0, 2:1 oder 0:0"
    elif "Dominant" in szenario_a and "Konter" in b_off:
        szenario_match = "⚔️ Dominant vs. Konter"
        beschreibung_match = "Team A dominiert, aber Team B lauert auf Konter."
        tendenz_match = "1:0 für A, oder 1:1"
    else:
        szenario_match = szenario_a
        beschreibung_match = beschreibung_a
        tendenz_match = tendenz_a

    return {
        "titel": szenario_match,
        "beschreibung": beschreibung_match,
        "tendenz": tendenz_match,
        "mod_a": mod_a,
        "mod_b": mod_b
    }

def get_poisson_probability(actual_goals: int, expected_goals: float) -> float:
    if expected_goals <= 0:
        return 0.0
    return (pow(expected_goals, actual_goals) * math.exp(-expected_goals)) / math.factorial(actual_goals)

def get_best_guess(match: MatchScenario, max_goals: int = 4) -> Tuple[int, int]:
    lambda_a = LAMBDA_MAP.get(match.team_a.bonus, 1.2)
    lambda_b = LAMBDA_MAP.get(match.team_b.bonus, 1.2)

    best_result = (0, 0)
    best_probability = -1.0

    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            prob_a = get_poisson_probability(ga, lambda_a)
            prob_b = get_poisson_probability(gb, lambda_b)
            total_prob = prob_a * prob_b

            if total_prob > best_probability:
                best_probability = total_prob
                best_result = (ga, gb)

    return best_result

def get_possible_results_with_probabilities(match: MatchScenario, max_goals: int = 4) -> List[Tuple[int, int, float]]:
    lambda_a = LAMBDA_MAP.get(match.team_a.bonus, 1.2)
    lambda_b = LAMBDA_MAP.get(match.team_b.bonus, 1.2)

    results = []
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            prob_a = get_poisson_probability(ga, lambda_a)
            prob_b = get_poisson_probability(gb, lambda_b)
            total_prob = prob_a * prob_b
            if total_prob > 0:
                results.append((ga, gb, round(total_prob, 4)))
    return sorted(results, key=lambda x: x[2], reverse=True)

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

def get_modulated_kpi_values(mod_kpis: dict) -> dict:
    """
    Extrahiert numerische Werte für die modulierten KPIs (für Grafik).
    """
    mapping = {
        "Schwach (abgeschwächt)": 1,
        "Schwach": 2,
        "Mittel (abgeschwächt)": 3,
        "Mittel": 4,
        "Mittel (verstärkt)": 5,
        "Stark (verstärkt)": 6,
        "Stark (sehr)": 7,
        "Aggressiv (moderat)": 6,
        "Aggressiv (sehr)": 7,
        "Defensiv (abgeschwächt)": 3,
        "Defensiv (sehr)": 2,
        "Hoch stehend": 8,
        "Tief stehend": 2,
        "Hoch": 9,
        "Niedrig": 2,
        "3-4-3 (sehr aggressiv)": 9,
        "4-3-3 (aggressiv)": 8,
        "3-5-2 (aggressiv/ausgewogen)": 7,
        "4-2-3-1 (ausgewogen)": 6,
        "4-4-2 (defensiv)": 4,
        "5-3-2 (sehr defensiv)": 2
    }
    numeric = {}
    for kpi, value in mod_kpis.items():
        numeric[kpi] = mapping.get(value, 5)
    return numeric

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
            <p class="section-headline">📌 Basis-Szenario</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 700; color: #D4A853;">{scenario}</div>
            <div style="color: rgba(255,255,255,0.5);">{reasoning}</div>
        </div>
    """, unsafe_allow_html=True)

def render_scenario_analysis(match: MatchScenario):
    scenario = analyze_scenario(match.team_a.kpis, match.team_b.kpis)
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">🧠 Modulierte Szenario-Analyse</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 700; color: #D4A853;">{scenario['titel']}</div>
            <div style="color: rgba(255,255,255,0.7); margin-top: 0.3rem;">{scenario['beschreibung']}</div>
            <div style="color: rgba(255,255,255,0.4); margin-top: 0.3rem;">Tendenz: {scenario['tendenz']}</div>
        </div>
    """, unsafe_allow_html=True)

    # ─── MODULIERTE KPIS TABELLE ───
    st.markdown("### 📊 Modulierte KPIs (effektiv)")
    mod_a = scenario['mod_a']
    mod_b = scenario['mod_b']
    mod_data = []
    for kpi in KPIS:
        mod_data.append({
            "KPI": kpi,
            "Team A (effektiv)": mod_a.get(kpi, "—"),
            "Team B (effektiv)": mod_b.get(kpi, "—")
        })
    df_mod = pd.DataFrame(mod_data)
    st.dataframe(df_mod, use_container_width=True, hide_index=True)

    # ─── GRAFIK DER MODULIERTEN KPIS ───
    render_modulated_kpi_chart(mod_a, mod_b)

def render_modulated_kpi_chart(mod_a: dict, mod_b: dict):
    """Zeigt ein Balkendiagramm der modulierten KPIs."""
    st.markdown("### 📈 Modulationseffekt (grafisch)")
    kpis = ["Offensive", "Defensive", "Spielweise", "Taktik", "Motivation", "Spielrelevanz", "Formation"]
    values_a = get_modulated_kpi_values(mod_a)
    values_b = get_modulated_kpi_values(mod_b)

    df_chart = pd.DataFrame({
        "KPI": kpis,
        "Team A": [values_a[k] for k in kpis],
        "Team B": [values_b[k] for k in kpis]
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_chart["KPI"],
        y=df_chart["Team A"],
        name="Team A",
        marker_color="#D4A853"
    ))
    fig.add_trace(go.Bar(
        x=df_chart["KPI"],
        y=df_chart["Team B"],
        name="Team B",
        marker_color="#F5D98E"
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_best_guess(match: MatchScenario):
    ga, gb = get_best_guess(match)
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">🏆 Best Guess (Poisson)</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 3rem; font-weight: 800; color: #D4A853;">{ga} : {gb}</div>
        </div>
    """, unsafe_allow_html=True)

def render_possible_results(match: MatchScenario):
    results = get_possible_results_with_probabilities(match)
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📋 Alle möglichen Ergebnisse (Poisson)</p>
        </div>
    """, unsafe_allow_html=True)
    data = []
    for ga, gb, prob in results:
        data.append({"Ergebnis": f"{ga}:{gb}", "Wahrscheinlichkeit": f"{prob*100:.2f} %"})
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_kpi_comparison(kpis_a: dict, kpis_b: dict):
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📋 KPI-Vergleich (Original)</p>
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
6. **Modulation** – Motivation + Spielrelevanz modulieren die KPIs
7. **Poisson** – Wahrscheinlichkeiten für Ergebnisse
""")
st.sidebar.markdown("---")
st.sidebar.caption("📅 Szenario Dashboard v2.0 (Modulation + Poisson + Grafik)")

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
render_scenario_analysis(match)   # Mit Grafik + Tabelle
render_best_guess(match)
render_possible_results(match)

# ─── KPI-VERGLEICH ───
render_kpi_comparison(kpis_a, kpis_b)

# ─── BONUS-VERTEILUNG & 128 KOMBINATIONEN ───
render_bonus_distribution()
render_128_combinations()