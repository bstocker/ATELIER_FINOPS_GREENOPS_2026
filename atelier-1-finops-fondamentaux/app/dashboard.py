"""
Atelier 1 — Dashboard FinOps showback complété (Exercice 5).
Lancer : streamlit run app/dashboard.py
"""

import json
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="FinOps Showback", layout="wide", page_icon="💰")

CUR_PATH = Path(__file__).parent.parent.parent / "ressources" / "datasets" / "cur_sample.csv"
BUDGET_PATH = Path(__file__).parent.parent.parent / "ressources" / "datasets" / "budgets.json"

ACCOUNT_LABELS = {
    "111111111111": "prod",
    "222222222222": "staging",
    "333333333333": "dev",
    "444444444444": "sandbox",
}


@st.cache_data
def load_data():
    df = pd.read_csv(CUR_PATH, parse_dates=["usage_date"])
    df["account_name"] = df["account_id"].map(ACCOUNT_LABELS)
    return df


@st.cache_data
def load_budgets():
    with open(BUDGET_PATH) as f:
        return json.load(f)["monthly_budgets_usd"]


df = load_data()
budgets = load_budgets()

# ─── Header ─────────────────────────────────────────────────────────
st.title("💰 FinOps Showback Dashboard")
st.caption("Atelier 1 — données synthétiques, période de 90 jours")

# ─── KPI couverture tagging (Exercice 5.1) ──────────────────────────
total_cost = df.unblended_cost.sum()
tag_coverage = {
    "tag_team":    df[df.tag_team    != ""].unblended_cost.sum() / total_cost * 100,
    "tag_env":     df[df.tag_env     != ""].unblended_cost.sum() / total_cost * 100,
    "tag_project": df[df.tag_project != ""].unblended_cost.sum() / total_cost * 100,
}
st.markdown("### 🏷️ Couverture tagging (sur 100% des coûts)")
tc1, tc2, tc3 = st.columns(3)
tc1.metric("tag_team",    f"{tag_coverage['tag_team']:.1f}%",    delta="objectif 100%")
tc2.metric("tag_env",     f"{tag_coverage['tag_env']:.1f}%",     delta="objectif 100%")
tc3.metric("tag_project", f"{tag_coverage['tag_project']:.1f}%", delta="objectif 100%")

# ─── Filtres ────────────────────────────────────────────────────────
st.markdown("### 🔍 Filtres")
col1, col2, col3 = st.columns(3)

with col1:
    date_range = st.date_input(
        "Période",
        value=(df.usage_date.min().date(), df.usage_date.max().date()),
        min_value=df.usage_date.min().date(),
        max_value=df.usage_date.max().date(),
    )

with col2:
    teams = ["(toutes)"] + sorted(df.tag_team.fillna("").replace("", "(non-taggé)").unique().tolist())
    team = st.selectbox("Équipe", teams)

with col3:
    accounts = ["(tous)"] + sorted(df.account_name.unique().tolist())
    account = st.selectbox("Compte", accounts)

# Appliquer les filtres
mask = (df.usage_date.dt.date >= date_range[0]) & (df.usage_date.dt.date <= date_range[1])
if team != "(toutes)":
    team_filter = "" if team == "(non-taggé)" else team
    mask &= df.tag_team == team_filter
if account != "(tous)":
    mask &= df.account_name == account
filtered = df[mask]

# ─── KPIs principaux ────────────────────────────────────────────────
st.markdown("### 📊 Indicateurs clés")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Coût total", f"${filtered.unblended_cost.sum():,.0f}")
k2.metric("Coût moyen / jour", f"${filtered.groupby('usage_date').unblended_cost.sum().mean():,.0f}")
k3.metric("Nombre de services", filtered.service.nunique())
k4.metric("Couverture tagging", f"{(filtered.tag_team != '').mean() * 100:.1f}%")

# ─── Graphique tendance + forecast (Exercice 5 bonus) ───────────────
st.markdown("### 📈 Tendance journalière + forecast 30 jours")
daily = filtered.groupby("usage_date").unblended_cost.sum().reset_index()
daily["day_num"] = (daily.usage_date - daily.usage_date.min()).dt.days

coeffs = np.polyfit(daily.day_num, daily.unblended_cost, 1)
future_days = pd.DataFrame({
    "day_num": range(daily.day_num.max() + 1, daily.day_num.max() + 31)
})
future_days["usage_date"] = daily.usage_date.max() + pd.to_timedelta(
    future_days.day_num - daily.day_num.max(), unit="D"
)
future_days["unblended_cost"] = np.polyval(coeffs, future_days.day_num)
future_days["type"] = "Forecast"
daily["type"] = "Réel"

combined = pd.concat([daily[["usage_date", "unblended_cost", "type"]],
                      future_days[["usage_date", "unblended_cost", "type"]]])
fig = px.line(combined, x="usage_date", y="unblended_cost", color="type",
              color_discrete_map={"Réel": "#1f77b4", "Forecast": "#ff7f0e"},
              labels={"unblended_cost": "Coût ($)", "usage_date": "Date"})
st.plotly_chart(fig, use_container_width=True)

# ─── Budget vs Réel (Exercice 5.2 + 5.3) ───────────────────────────
st.markdown("### 💼 Budget vs Réel par équipe")
n_months = (df.usage_date.max() - df.usage_date.min()).days / 30
team_cost = (
    df[df.tag_team != ""].groupby("tag_team").unblended_cost.sum() / n_months
).reset_index()
team_cost.columns = ["equipe", "cout_mensuel_moyen"]
team_cost["budget"] = team_cost["equipe"].map(budgets)
team_cost["pct_budget"] = (team_cost.cout_mensuel_moyen / team_cost.budget * 100).round(1)
team_cost["statut"] = team_cost.pct_budget.apply(
    lambda x: "🔴 Dépassement" if x > 110 else ("🟡 Proche" if x > 90 else "🟢 OK")
)

fig2 = go.Figure()
fig2.add_bar(name="Budget", x=team_cost.equipe, y=team_cost.budget,
             marker_color="lightgrey")
fig2.add_bar(name="Réel moyen/mois", x=team_cost.equipe, y=team_cost.cout_mensuel_moyen,
             marker_color=team_cost.pct_budget.apply(
                 lambda x: "#d62728" if x > 110 else ("#ff7f0e" if x > 90 else "#2ca02c")
             ))
fig2.update_layout(barmode="group", yaxis_title="Coût ($)")
st.plotly_chart(fig2, use_container_width=True)

# Alertes (Exercice 5.3)
alerts = team_cost[team_cost.pct_budget > 110]
if not alerts.empty:
    for _, row in alerts.iterrows():
        st.error(
            f"⚠️ **{row.equipe}** dépasse son budget mensuel : "
            f"${row.cout_mensuel_moyen:,.0f} / budget ${row.budget:,.0f} "
            f"({row.pct_budget:.0f}%)"
        )
else:
    st.success("✅ Toutes les équipes sont dans leur budget mensuel.")

st.dataframe(
    team_cost[["equipe", "budget", "cout_mensuel_moyen", "pct_budget", "statut"]],
    use_container_width=True
)

# ─── Tableau top usages ─────────────────────────────────────────────
st.markdown("### 🏆 Top 10 usages les plus coûteux")
top = (
    filtered.groupby(["service", "usage_type"]).unblended_cost.sum()
    .sort_values(ascending=False).head(10).reset_index()
)
st.dataframe(top, use_container_width=True)
