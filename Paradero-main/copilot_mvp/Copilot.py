##%%writefile copilot.py
import os
os.environ["OPENAI_API_KEY"] = "Por seguridad no pongo el APIKEY"
import json
import streamlit as st
from datetime import datetime
from typing import Dict, List, Tuple, Optional


try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    client = None

# ---------------------------
# 1) Clasificador ligero
# ---------------------------
TOPICS = ["revenue", "staff", "guest", "ops"]

KEYWORDS = {
    "revenue": [
        "ingresos", "revenue", "ventas", "f&b", "food", "bebidas", "upsell",
        "tasa de ocupación", "revpar", "adr", "ancillary", "promoción", "menu"
    ],
    "staff": [
        "equipo", "rotación", "moral", "clima", "turnover", "entrenamiento",
        "capacitación", "roles", "horarios", "cultura", "liderazgo"
    ],
    "guest": [
        "huésped", "guest", "nps", "reviews", "reseñas", "satisfacción",
        "quejas", "servicio al cliente", "experiencia", "check-in", "check out"
    ],
    "ops": [
        "operación", "ops", "inventario", "costos", "mermas", "sop", "estándar",
        "estandarización", "procesos", "eficiencia", "turnos", "housekeeping"
    ],
}

def classify_topic(text: str) -> str:
    t = text.lower()
    scores = {k: 0 for k in TOPICS}
    for topic, kws in KEYWORDS.items():
        for kw in kws:
            if kw in t:
                scores[topic] += 1
    # fallback
    topic = max(scores, key=scores.get)
    return topic if scores[topic] > 0 else "ops"

# ---------------------------
# 2) Prompt composer
# ---------------------------
SYSTEM_PROMPT = """Eres un asesor para hotelería/hospitalidad.
Habla con tono cálido, claro y profesional (hospitality).
Usa prácticas tipo SOP: pasos claros, checklists, responsables y horizontes.

FORMATO DE SALIDA:
1) Resumen (3-4 líneas orientadas a negocio).
2) Acciones recomendadas (exactamente 3), estilo SMART: qué, quién (rol sugerido), cuándo (horizonte en semanas).
3) Riesgos/consideraciones (2-4 bullets).
4) Métricas de éxito (principal y de guardia).
5) Al final, devuelve un JSON válido (SOLO JSON) con:
{
  "tema": "revenue|staff|guest|ops",
  "resumen": "...",
  "acciones": [
    {"titulo":"...", "descripcion":"...", "horizonte":"semanas", "owner_sugerido":"rol"}
  ],
  "riesgos": ["...", "..."],
  "metricas": {"principal":"...", "guardia":"..."},
  "siguiente_paso_agente": "checklist|email|experimento|ninguno"
}

NO incluyas explicaciones fuera del formato anterior. Delimita el JSON con una línea que diga SOLO: ===JSON===
"""

def build_user_prompt(question: str, topic_hint: Optional[str]) -> str:
    topic = topic_hint or classify_topic(question)
    return f"""Contexto:
- Rol del usuario: General Manager (hotel).
- Tema detectado: {topic}.
- Pregunta/objetivo: {question}

Instrucciones:
- Adapta recomendaciones al contexto hotelero.
- Usa ejemplos operativos realistas (F&B, staff scheduling, guest experience, housekeeping, etc.).
- Mantén respuesta concisa y accionable.
"""

# ---------------------------
# 3) LLM call helper
# ---------------------------
def call_openai(messages: List[Dict], model: str = "gpt-4o-mini", temperature: float = 0.4) -> str:
    if client is None:
        raise RuntimeError("OpenAI client no inicializado. Revisa OPENAI_API_KEY e instalación.")
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    return resp.choices[0].message.content

# ---------------------------
# 4) Parseo de salida (markdown + JSON)
# ---------------------------
def split_markdown_and_json(output_text: str) -> Tuple[str, Dict]:
    """
    El modelo devuelve texto con secciones + una línea '===JSON===' y después SOLO JSON.
    """
    if "===JSON===" not in output_text:
        # Intento de rescate si el modelo no respetó la marca
        try:
            # Buscar el primer '{' de JSON válido
            json_start = output_text.find("{")
            json_text = output_text[json_start:]
            data = json.loads(json_text)
            md = output_text[:json_start].strip()
            return md, data
        except Exception:
            return output_text, {}
    else:
        parts = output_text.split("===JSON===")
        md = parts[0].strip()
        json_text = parts[1].strip()
        try:
            data = json.loads(json_text)
        except Exception:
            data = {}
        return md, data

# ---------------------------
# 5) Bonus: agente/acción sugerida
# ---------------------------
def agent_followup(data: Dict, question: str, model: str = "gpt-4o-mini") -> Optional[str]:
    next_step = data.get("siguiente_paso_agente", "ninguno")
    tema = data.get("tema", "ops")
    acciones = data.get("acciones", [])
    if next_step == "ninguno":
        return None

    if next_step == "checklist":
        prompt = f"""Genera un checklist operativo breve (8-12 ítems) para el tema '{tema}' basado en estas acciones:
{json.dumps(acciones, ensure_ascii=False, indent=2)}
Contexto del GM: {question}
Formato: bullets simples con verbo de acción al inicio."""
    elif next_step == "email":
        prompt = f"""Redacta un borrador de email breve (120-160 palabras) al equipo, tono hospitality,
con call-to-action y fecha objetivo, basado en estas acciones:
{json.dumps(acciones, ensure_ascii=False, indent=2)}
Asunto: Iniciativa prioritaria ({tema})."""
    elif next_step == "experimento":
        prompt = f"""Esboza un mini experimento A/B para '{tema}' con:
- Hipótesis, variante A/B, muestra, duración (semanas), métrica principal y de guardia,
- Criterios de éxito y siguiente paso.
Basado en estas acciones:
{json.dumps(acciones, ensure_ascii=False, indent=2)}"""
    else:
        return None

    messages = [
        {"role": "system", "content": "Eres un asistente de operaciones hoteleras. Sé conciso y práctico."},
        {"role": "user", "content": prompt},
    ]
    try:
        return call_openai(messages, model=model, temperature=0.3)
    except Exception as e:
        return f"*No se pudo generar el artefacto del agente:* {e}"

# ---------------------------
# 6) Streamlit UI
# ---------------------------
st.set_page_config(page_title="Hotel Co-Pilot MVP", page_icon="🏨", layout="centered")

st.title("🏨 Co-Pilot MVP — Hospitality")
st.caption("MVP: input del GM → recomendación LLM con tono hospitality + SOP. Bonus: agente para checklist/email/experimento.")

with st.sidebar:
    st.header("⚙️ Configuración")
    model = st.selectbox("Modelo (OpenAI)", ["gpt-4o-mini", "gpt-4o"], index=0)
    temperature = st.slider("Creatividad (temperature)", 0.0, 1.0, 0.4, 0.1)
    topic_override = st.selectbox("Tema (opcional)", ["auto"] + TOPICS, index=0)
    st.markdown("---")
    st.markdown("**API key**: usa la variable `OPENAI_API_KEY`.")
    st.markdown("**Registro local**: guarda interacciones en memoria de sesión.")

st.subheader("1) Pregunta del GM")
question = st.text_area(
    "Escribe tu pregunta/objetivo (p.ej., “¿Cómo aumentar ingresos F&B en 6 semanas manteniendo NPS?”)",
    height=120,
    placeholder="Ejemplos: mejorar moral del equipo, subir ADR sin afectar ocupación, reducir mermas en bar, etc.",
)

col1, col2 = st.columns([1, 1])
with col1:
    run = st.button("Obtener recomendación", type="primary", use_container_width=True)
with col2:
    clear = st.button("Limpiar", use_container_width=True)

if clear:
    st.session_state.clear()
    st.experimental_rerun()

if "history" not in st.session_state:
    st.session_state["history"] = []

if run:
    if not question.strip():
        st.warning("Escribe una pregunta primero.")
    else:
        hint = None if topic_override == "auto" else topic_override
        user_prompt = build_user_prompt(question, hint)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = call_openai(messages, model=model, temperature=temperature)
            md, data = split_markdown_and_json(raw)
        except Exception as e:
            st.error(f"Error llamando al modelo: {e}")
            md, data = "", {}

        # Mostrar resultado principal
        st.subheader("2) Recomendación")
        if md:
            st.markdown(md)
        else:
            st.info("No se pudo formatear la respuesta. Reintenta con otra redacción.")

        # Bonus: agente
        artifact = None
        if data:
            artifact = agent_followup(data, question, model=model)

        if artifact:
            st.subheader("3) Acción sugerida (Bonus)")
            st.markdown(artifact)

        # Telemetría mínima en memoria
        st.session_state["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "topic": data.get("tema") if data else classify_topic(question),
            "model": model,
            "temperature": temperature,
            "result_preview": md[:200]
        })

# Historial simple
if st.session_state["history"]:
    st.markdown("---")
    st.subheader("🔎 Historial (sesión)")
    for h in reversed(st.session_state["history"][-5:]):
        st.markdown(
            f"- **{h['timestamp']}Z** · *{h['topic']}* · {h['model']} · “{h['question'][:80]}…”"
        )

# Footer
st.markdown("---")
st.caption("Construido para el caso de estudio: MVP simple con grounding Hospitality/SOP + bonus de agente.")

