# szenario_dashboard.py
# ============================================================
# ALL-IN-ONE: CONFIG + MODELS + LOGIC + UI + APP
# MIT 9 KPIS, FIFA-RANKING, STÄRKE-DIFFERENZ-MODULATOR (SDM),
# SPIELSTIL-MODULATOR, MODULATION, POISSON & SZENARIO-ENGINE
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
    "Formation",
    "Form",
    "Stärke"
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
    ],
    "Form": ["Top-Form", "Gute Form", "Normal", "Schlechte Form", "Krise"],
    "Stärke": ["Überragend", "Stark", "Normal", "Schwach", "Sehr schwach"]
}

AGGRESSIVE_FORMATIONS = [
    "3-4-3 (sehr aggressiv)",
    "4-3-3 (aggressiv)",
    "3-5-2 (aggressiv/ausgewogen)"
]

# ============================================================
# 1.1 FIFA-RANKING
# ============================================================

FIFA_RANKINGS = {
    "Argentinien": 1,
    "Frankreich": 2,
    "Brasilien": 3,
    "England": 4,
    "Belgien": 5,
    "Portugal": 6,
    "Spanien": 7,
    "Niederlande": 8,
    "Kroatien": 9,
    "Italien": 10,
    "Deutschland": 11,
    "Uruguay": 12,
    "Schweiz": 13,
    "USA": 14,
    "Mexiko": 15,
    "Senegal": 16,
    "Japan": 17,
    "Südkorea": 18,
    "Schweden": 19,
    "Polen": 20,
    "Norwegen": 21,
    "Österreich": 22,
    "Kolumbien": 23,
    "Marokko": 24,
    "Ägypten": 25,
    "Tschechien": 26,
    "Wales": 27,
    "Schottland": 28,
    "Ecuador": 29,
    "Kanada": 30,
    "Australien": 31,
    "Ukraine": 32,
    "Serbien": 33,
    "Kamerun": 34,
    "Nigeria": 35,
    "Ghana": 36,
    "Tunesien": 37,
    "Algerien": 38,
    "Saudi-Arabien": 39,
    "Iran": 40,
    "Irak": 41,
    "Kap Verde": 42,
    "Neuseeland": 43,
    "Panama": 44,
    "Costa Rica": 45,
    "Honduras": 46,
    "Jamaika": 47,
    "Elfenbeinküste": 48,
    "Burkina Faso": 49,
    "Mali": 50,
    "Südafrika": 51,
    "Kongo": 52,
    "Uganda": 53,
    "Jordanien": 54,
    "Usbekistan": 55,
    "Katar": 56,
    "Haiti": 57,
    "Curaçao": 58,
    "Island": 59,
    "Slowakei": 60,
    "Slowenien": 61,
    "Nordirland": 62,
    "Georgien": 63,
    "Armenien": 64,
    "Kasachstan": 65,
    "Aserbaidschan": 66,
    "Israel": 67,
    "Zypern": 68,
    "Grenada": 69,
    "Färöer": 70,
    "Liechtenstein": 71,
}

ALL_TEAMS = list(FIFA_RANKINGS.keys())
ALL_TEAMS.sort()

def get_base_bonus_from_ranking(team_name: str) -> float:
    ranking = FIFA_RANKINGS.get(team_name, 60)
    if ranking <= 10:
        return 3.0
    elif ranking <= 20:
        return 2.5
    elif ranking <= 35:
        return 2.0
    elif ranking <= 60:
        return 1.5
    else:
        return 1.0

# ============================================================
# 1.2 FORM-FAKTOR
# ============================================================

FORM_FACTOR_MAP = {
    "Top-Form": 1.5,
    "Gute Form": 1.2,
    "Normal": 1.0,
    "Schlechte Form": 0.7,
    "Krise": 0.5
}

def get_form_factor(form_state: str) -> float:
    return FORM_FACTOR_MAP.get(form_state, 1.0)

# ============================================================
# 1.3 STÄRKE-ANPASSUNG
# ============================================================

STRENGTH_FACTOR_MAP = {
    "Überragend": 0.8,
    "Stark": 0.4,
    "Normal": 0.0,
    "Schwach": -0.4,
    "Sehr schwach": -0.8
}

def get_strength_factor(strength_state: str) -> float:
    return STRENGTH_FACTOR_MAP.get(strength_state, 0.0)

# ============================================================
# 1.4 LAMBDA
# ============================================================

def get_lambda_from_expected(expected_goals: float) -> float:
    if expected_goals <= 0:
        return 0.0
    return min(max(expected_goals, 0.0), 4.0)

# ============================================================
# 1.5 STÄRKE-DIFFERENZ-MODULATOR (SDM)
# ============================================================

def apply_strength_difference_modulator(lambda_a: float, lambda_b: float) -> Tuple[float, float]:
    if lambda_a >= lambda_b:
        strong_lambda = lambda_a
        weak_lambda = lambda_b
        is_a_stronger = True
    else:
        strong_lambda = lambda_b
        weak_lambda = lambda_a
        is_a_stronger = False

    diff = strong_lambda - weak_lambda
    sdm_factor = 1.0 + (strong_lambda / 4.0) * 1.0

    strong_goals = strong_lambda + (diff * sdm_factor * 0.35)
    weak_goals = max(0.1, weak_lambda - (diff * sdm_factor * 0.25))

    strong_goals = min(strong_goals, 5.0)
    weak_goals = min(weak_goals, 5.0)

    if is_a_stronger:
        return strong_goals, weak_goals
    else:
        return weak_goals, strong_goals

# ============================================================
# 2. MODELS
# ============================================================

@dataclass
class TeamScenario:
    team_name: str
    kpis: Dict[str, str]
    bits: List[int] = None
    index: int = None
    bonus: int = None
    base_bonus: float = None
    expected_goals: float = None

    def __post_init__(self):
        self.bits = self.create_bits()
        self.index = self.calculate_index()
        self.bonus = self.calculate_bonus()
        self.base_bonus = get_base_bonus_from_ranking(self.team_name)
        self.expected_goals = self.calculate_expected_goals()

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

    def calculate_expected_goals(self) -> float:
        base_bonus = get_base_bonus_from_ranking(self.team_name)
        strength_state = self.kpis.get("Stärke", "Normal")
        strength_factor = get_strength_factor(strength_state)
        adjusted_base = base_bonus + strength_factor

        if adjusted_base >= 3.5:
            team_factor = 1.0
        elif adjusted_base >= 2.5:
            team_factor = 0.9
        elif adjusted_base >= 1.8:
            team_factor = 0.8
        elif adjusted_base >= 1.2:
            team_factor = 0.7
        else:
            team_factor = 0.6

        form_state = self.kpis.get("Form", "Normal")
        form_factor = get_form_factor(form_state)

        expected = (self.bonus * team_factor) + (adjusted_base * 0.5)
        expected *= form_factor

        spielweise = self.kpis["Spielweise"]
        taktik = self.kpis["Taktik"]

        if spielweise == "Defensiv" and taktik == "Tief stehend":
            expected *= 0.5
        elif spielweise == "Aggressiv" and taktik == "Hoch stehend":
            expected *= 1.3
        elif spielweise == "Defensiv" and taktik == "Hoch stehend":
            expected *= 0.8
        elif spielweise == "Aggressiv" and taktik == "Tief stehend":
            expected *= 1.0

        if self.kpis["Defensive"] == "Schwach" and spielweise == "Defensiv":
            expected *= 0.9

        return max(0.0, min(expected, 4.0))

@dataclass
class MatchScenario:
    team_a: TeamScenario
    team_b: TeamScenario

    @property
    def lambda_a(self) -> float:
        return get_lambda_from_expected(self.team_a.expected_goals)

    @property
    def lambda_b(self) -> float:
        return get_lambda_from_expected(self.team_b.expected_goals)

    @property
    def lambda_a_modulated(self) -> float:
        a, b = apply_strength_difference_modulator(self.lambda_a, self.lambda_b)
        return a

    @property
    def lambda_b_modulated(self) -> float:
        a, b = apply_strength_difference_modulator(self.lambda_a, self.lambda_b)
        return b

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

    def get_best_guess_with_sdm(self, max_goals: int = 5) -> Tuple[int, int]:
        lam_a = self.lambda_a_modulated
        lam_b = self.lambda_b_modulated

        best_result = (0, 0)
        best_probability = -1.0

        for ga in range(max_goals + 1):
            for gb in range(max_goals + 1):
                prob_a = get_poisson_probability(ga, lam_a)
                prob_b = get_poisson_probability(gb, lam_b)
                total_prob = prob_a * prob_b

                if total_prob > best_probability:
                    best_probability = total_prob
                    best_result = (ga, gb)

        return best_result

# ============================================================
# 3. LOGIC
# ============================================================

def get_poisson_probability(actual_goals: int, expected_goals: float) -> float:
    if expected_goals <= 0:
        return 0.0 if actual_goals > 0 else 1.0
    return (pow(expected_goals, actual_goals) * math.exp(-expected_goals)) / math.factorial(actual_goals)

def get_possible_results_with_probabilities(match: MatchScenario, max_goals: int = 5) -> List[Tuple[int, int, float]]:
    lam_a = match.lambda_a_modulated
    lam_b = match.lambda_b_modulated

    results = []
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            prob_a = get_poisson_probability(ga, lam_a)
            prob_b = get_poisson_probability(gb, lam_b)
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

def modulate_kpis(kpis: dict) -> dict:
    offensive = kpis["Offensive"]
    defensive = kpis["Defensive"]
    spielweise = kpis["Spielweise"]
    taktik = kpis["Taktik"]
    motivation = kpis["Motivation"]
    relevanz = kpis["Spielrelevanz"]

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

    else:
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

    if relevanz == "Hoch":
        if "Stark" in defensive_eff or "Mittel" in defensive_eff:
            defensive_eff = "Stark (sehr)"
        else:
            defensive_eff = "Mittel (verstärkt)"

        if "Aggressiv" in spielweise_eff:
            spielweise_eff = "Aggressiv (sehr)"
        else:
            spielweise_eff = "Aggressiv (moderat)"

    else:
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
        "Formation": kpis["Formation"],
        "Form": kpis["Form"],
        "Stärke": kpis["Stärke"]
    }

def analyze_scenario(team_a_kpis: dict, team_b_kpis: dict) -> Dict:
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
    else:
        szenario_a = "📊 Standard"
        beschreibung_a = "Ausgeglichene Taktik – keine extremen Wechselwirkungen."
        tendenz_a = "1:1, 2:1, 1:2"

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
    elif kpi_name == "Form":
        if state in ["Top-Form", "Gute Form"]:
            return "✅"
        elif state in ["Schlechte Form", "Krise"]:
            return "❌"
        else:
            return "➖"
    elif kpi_name == "Stärke":
        if state in ["Überragend", "Stark"]:
            return "✅"
        elif state in ["Schwach", "Sehr schwach"]:
            return "❌"
        else:
            return "➖"
    return "❌"

def get_modulated_kpi_values(mod_kpis: dict) -> dict:
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
        "5-3-2 (sehr defensiv)": 2,
        "Top-Form": 10,
        "Gute Form": 8,
        "Normal": 6,
        "Schlechte Form": 3,
        "Krise": 1,
        "Überragend": 11,
        "Stark": 9,
        "Normal": 6,
        "Schwach": 3,
        "Sehr schwach": 1
    }
    numeric = {}
    for kpi, value in mod_kpis.items():
        numeric[kpi] = mapping.get(value, 5)
    return numeric

# ============================================================
# 4. UI (Streamlit-Komponenten)
# ============================================================

def render_team_input(team_name_label: str, prefix: str, default_team: str = "Frankreich") -> Tuple[str, dict]:
    st.markdown(f"### {team_name_label}")
    
    team = st.selectbox(
        "Team",
        options=ALL_TEAMS,
        key=f"{prefix}_team",
        index=ALL_TEAMS.index(default_team) if default_team in ALL_TEAMS else 0
    )
    
    kpis = {}
    cols = st.columns(2)
    for i, kpi in enumerate(KPIS):
        with cols[i % 2]:
            if kpi == "Form":
                kpis[kpi] = st.selectbox(
                    kpi,
                    options=KPI_OPTIONS[kpi],
                    key=f"{prefix}_{kpi}",
                    help="Top-Form: 1.5x Tore, Krise: 0.5x Tore"
                )
            elif kpi == "Stärke":
                kpis[kpi] = st.selectbox(
                    kpi,
                    options=KPI_OPTIONS[kpi],
                    key=f"{prefix}_{kpi}",
                    help="Überragend: +0.8, Stark: +0.4, Normal: 0, Schwach: -0.4, Sehr schwach: -0.8"
                )
            else:
                kpis[kpi] = st.selectbox(
                    kpi,
                    options=KPI_OPTIONS[kpi],
                    key=f"{prefix}_{kpi}"
                )
    return team, kpis

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
                <div style="color: rgba(255,255,255,0.3); font-size: 0.8rem;">KPI-Bonus</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{match.team_a.bonus}</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #D4A853;">{match.team_b.bonus}</div>
                <div style="color: rgba(255,255,255,0.3); font-size: 0.6rem; margin-top: 0.3rem;">
                    Basis: {match.team_a.base_bonus:.1f} / {match.team_b.base_bonus:.1f}
                </div>
            </div>
        """, unsafe_allow_html=True)

def render_match_analysis(match: MatchScenario):
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📊 Matchanalyse</p>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Team A KPI-Bonus", match.team_a.bonus)
    with col2:
        st.metric("Team B KPI-Bonus", match.team_b.bonus)
    with col3:
        st.metric("Differenz", f"{match.bonus_diff:+d}")
    with col4:
        st.metric("Erwartete Tore (λ)", f"{match.lambda_a_modulated:.2f} – {match.lambda_b_modulated:.2f}")

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

    st.markdown("### 📊 Modulierte KPIs (effektiv)")
    mod_a = scenario['mod_a']
    mod_b = scenario['mod_b']
    mod_data = []
    for kpi in KPIS:
        mod_data.append({
            "KPI": kpi,
            f"{match.team_a.team_name} (effektiv)": mod_a.get(kpi, "—"),
            f"{match.team_b.team_name} (effektiv)": mod_b.get(kpi, "—")
        })
    df_mod = pd.DataFrame(mod_data)
    st.dataframe(df_mod, use_container_width=True, hide_index=True)

    render_modulated_kpi_chart(mod_a, mod_b, match.team_a.team_name, match.team_b.team_name)

def render_modulated_kpi_chart(mod_a: dict, mod_b: dict, name_a: str, name_b: str):
    st.markdown("### 📈 Modulationseffekt (grafisch)")
    kpis = ["Offensive", "Defensive", "Spielweise", "Taktik", "Motivation", "Spielrelevanz", "Formation", "Form", "Stärke"]
    values_a = get_modulated_kpi_values(mod_a)
    values_b = get_modulated_kpi_values(mod_b)

    df_chart = pd.DataFrame({
        "KPI": kpis,
        name_a: [values_a[k] for k in kpis],
        name_b: [values_b[k] for k in kpis]
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_chart["KPI"],
        y=df_chart[name_a],
        name=name_a,
        marker_color="#D4A853"
    ))
    fig.add_trace(go.Bar(
        x=df_chart["KPI"],
        y=df_chart[name_b],
        name=name_b,
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
    ga, gb = match.get_best_guess_with_sdm()
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">🏆 Best Guess (mit SDM)</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 3rem; font-weight: 800; color: #D4A853;">{ga} : {gb}</div>
            <div style="color: rgba(255,255,255,0.3); font-size: 0.8rem;">
                λ (moduliert): {match.lambda_a_modulated:.2f} – {match.lambda_b_modulated:.2f}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_possible_results(match: MatchScenario):
    results = get_possible_results_with_probabilities(match)
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📋 Alle möglichen Ergebnisse (Poisson + SDM)</p>
        </div>
    """, unsafe_allow_html=True)
    data = []
    for ga, gb, prob in results:
        data.append({"Ergebnis": f"{ga}:{gb}", "Wahrscheinlichkeit": f"{prob*100:.2f} %"})
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_kpi_comparison(kpis_a: dict, kpis_b: dict, name_a: str, name_b: str):
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📋 KPI-Vergleich (Original)</p>
        </div>
    """, unsafe_allow_html=True)
    data = []
    for kpi in KPIS:
        data.append({
            "KPI": kpi,
            name_a: kpi_to_checkmark(kpis_a, kpi),
            name_b: kpi_to_checkmark(kpis_b, kpi)
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_bonus_distribution():
    st.markdown("""
        <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
            <p class="section-headline">📊 Bonus-Verteilung (128 Kombinationen)</p>
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

st.sidebar.markdown("### 📖 Die 9 Schritte")
st.sidebar.markdown("""
1. **Team** – wähle ein WM-Team
2. **9 KPIs** – je 2 Zustände (Form: 5, Stärke: 5)
3. **Bits** – stark = 1, schwach = 0 (Form & Stärke nicht in Bits)
4. **KPI-Bonus** – Anzahl der Bits (0–7)
5. **Basis-Bonus** – aus FIFA-Ranking (1.0–3.0)
6. **Stärke-Anpassung** – manuell (±0.8)
7. **Form-Faktor** – aus KPI (0.5–1.5)
8. **Spielstil-Modulator** – defensiv+tief → ×0.5, aggressiv+hoch → ×1.3
9. **SDM** – Stärke-Differenz-Modulator verstärkt die Tore des stärkeren Teams
10. **Poisson** – Wahrscheinlichkeiten für Ergebnisse
""")
st.sidebar.markdown("---")
st.sidebar.caption("📅 Szenario Dashboard v6.0 (mit SDM)")

st.markdown("""
    <div style="display: flex; justify-content: center; width: 100%; margin: 0.1rem 0 1.5rem 0;">
        <p class="section-headline">⚽ Team-KPIs eingeben</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")

with col1:
    team_a, kpis_a = render_team_input("🟡 Team A", "a", default_team="Frankreich")

with col2:
    team_b, kpis_b = render_team_input("🔵 Team B", "b", default_team="Curaçao")

# ─── BERECHNUNG ───
team_a_obj = TeamScenario(team_a, kpis_a)
team_b_obj = TeamScenario(team_b, kpis_b)
match = MatchScenario(team_a_obj, team_b_obj)

st.markdown("---")

render_calculation_pipeline(match)
render_match_analysis(match)
render_scenario(match)
render_scenario_analysis(match)
render_best_guess(match)
render_possible_results(match)

render_kpi_comparison(kpis_a, kpis_b, team_a, team_b)

render_bonus_distribution()
render_128_combinations()