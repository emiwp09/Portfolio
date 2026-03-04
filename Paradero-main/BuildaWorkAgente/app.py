import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SalesActivator – MICE (US)", layout="wide")

# =========================
# Helpers
# =========================
def normalize_domain(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", str(name).strip().lower()).strip("-")
    return (base if base else "example") + ".com"

def guess_contacts(row):
    dom = row.get("domain", "example.com")
    contacts = [
        {"full_name": "Alex Carter", "role": "Director of Sales", "email": f"alex.carter@{dom}"},
        {"full_name": "Jordan Lee", "role": "Events Manager", "email": f"jordan.lee@{dom}"},
    ]
    return contacts

def score_company(row):
    score = 50
    seg_bonus = {
        "Resort": 15,
        "Hotel Chain (Upscale)": 20,
        "Boutique Hotel": 10,
        "Convention Center": 25,
        "Conference Center": 18,
        "Event Planner/Agency": 12,
        "Incentives Agency": 12,
        "Lodge": 8,
    }
    score += seg_bonus.get(row.get("segment", ""), 0)
    if row.get("state") in ["CA", "NY", "FL", "MA", "IL", "TX"]:
        score += 8
    return min(score, 100)

def outreach_sequence(company_name, contact_name, segment):
    return [
        {
            "step": 1,
            "channel": "Email",
            "subject": f"Offsites/Grupos – ¿Encaja {company_name} con Paradero?",
            "body": (
                f"Hola {contact_name},\n\n"
                f"Soy Emiliano. Trabajo con Paradero para diseñar experiencias MICE en México. "
                f"Vi que {company_name} opera en el segmento '{segment}' y pensé en propuestas para sus clientes corporativos "
                f"(retreats, incentivos, board meetings).\n\n"
                f"¿Te interesa una llamada de 15 min para explorar fechas, tarifas corporativas y beneficios?\n\n"
                f"Saludos,\nEmiliano"
            ),
        },
        {
            "step": 2,
            "channel": "Email (follow-up)",
            "subject": "¿Te viene bien esta semana o la próxima?",
            "body": (
                f"Hola {contact_name},\n\n"
                f"Retomando mi nota anterior sobre opciones MICE en Paradero. "
                f"Puedo compartir un par de itinerarios de ejemplo (3d/2n) y políticas para grupos. "
                f"¿Agenda abierta esta o la próxima semana?\n\n"
                f"Gracias,\nEmiliano"
            ),
        },
        {
            "step": 3,
            "channel": "LinkedIn/Call",
            "subject": "Touchpoint rápido",
            "body": (
                f"Hola {contact_name},\n\n"
                f"¿Podemos coordinar un touchpoint rápido? También puedo enviar un one-pager con espacios, "
                f"capacidades y perks para planners.\n\n"
                f"Saludos"
            ),
        },
    ]

# =========================
# Data loader (robusto)
# =========================
BASE = Path(__file__).resolve().parent

@st.cache_data
def load_seed() -> pd.DataFrame:
    file_path = BASE / "data" / "companies_seed.csv"
    if file_path.exists():
        st.success(f"✅ Datos cargados desde: {file_path}")
        return pd.read_csv(file_path)
    else:
        st.error(f"❌ No encontré el archivo en: {file_path}\n\nSube el CSV o crea la carpeta data/ y colócalo ahí.")
        uploaded = st.file_uploader("Sube companies_seed.csv", type=["csv"])
        if uploaded is not None:
            st.success("✅ Datos cargados desde archivo subido.")
            return pd.read_csv(uploaded)
        st.stop()

# =========================
# App
# =========================
st.title("SalesActivator – MICE (US Direct Segment)")
st.caption("Demo funcional que replica 3 semanas de trabajo: prospección → enriquecimiento → outreach → dashboard")

df = load_seed()

# Normaliza columnas esperadas
expected_cols = ["company_name", "segment", "city", "state", "website"]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    st.error(f"Faltan columnas en tu CSV: {missing}. Debe incluir {expected_cols}.")
    st.stop()

# Limpiezas básicas → forzamos a string para evitar errores
for col in ["website", "company_name", "segment", "city", "state"]:
    df[col] = df[col].fillna("").astype(str)

df["state"] = df["state"].str.upper()

# Enrichment seguro
df["domain"] = df.apply(
    lambda row: row["website"].strip() if len(row["website"].strip()) > 0 else normalize_domain(row["company_name"]),
    axis=1
)
df["score"] = df.apply(score_company, axis=1)
df["contacts"] = df.apply(guess_contacts, axis=1)

# Sidebar filtros
with st.sidebar:
    st.header("Filtros")
    states = sorted([s for s in df["state"].dropna().unique().tolist() if s])
    segs = sorted([s for s in df["segment"].dropna().unique().tolist() if s])
    ss = st.multiselect("Estados", states, default=states)
    sg = st.multiselect("Segmentos", segs, default=segs)
    min_score = st.slider("Score mínimo", 0, 100, 60, 5)
    st.divider()
    st.write("Exporta resultados filtrados a CSV")

# Filtrado
filtered = df[
    (df["state"].isin(ss) if ss else True) &
    (df["segment"].isin(sg) if sg else True) &
    (df["score"] >= min_score)
].copy()

# Dashboard top metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Empresas encontradas", len(df))
c2.metric("Empresas calificadas (filtro)", len(filtered))
total_contacts = int(sum(len(x) for x in filtered["contacts"])) if len(filtered) else 0
c3.metric("Contactos generados", total_contacts)
c4.metric("Score promedio", round(filtered["score"].mean(), 1) if len(filtered) > 0 else 0)

st.subheader("Tabla de empresas calificadas")
st.dataframe(filtered[["company_name", "segment", "city", "state", "domain", "score"]], use_container_width=True)

st.subheader("Contactos y secuencia de outreach")
for _, row in filtered.iterrows():
    with st.expander(f"{row['company_name']} • {row['segment']} • {row['city']}, {row['state']} • Score {row['score']}"):
        contacts = row["contacts"]
        for c in contacts:
            st.markdown(f"**{c['full_name']}** — {c['role']}  \\ `{c['email']}`")
            seq = outreach_sequence(row["company_name"], c["full_name"].split()[0], row["segment"])
            for s in seq:
                st.markdown(f"- **Paso {s['step']} ({s['channel']})** — *{s['subject']}*")
                st.code(s["body"], language="markdown")

st.download_button(
    "Descargar CSV filtrado",
    data=filtered.to_csv(index=False),
    file_name="mice_prospects_filtered.csv",
    mime="text/csv",
)

st.caption("© Demo para proceso de reclutamiento – Lógica simplificada, datos de ejemplo. Actualizado " + datetime.now().strftime("%Y-%m-%d %H:%M"))

