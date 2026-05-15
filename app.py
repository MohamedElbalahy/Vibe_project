"""
🌊 Water Utility Network AI Assistant
An AI-powered GIS assistant specialized in water utility networks,
satellite imagery analysis, and QGIS automation for the MENA region.
"""

import streamlit as st
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
import os
import json
import time
from PIL import Image

# ─────────────────────────────────────────
# APP IDENTITY — Customize for your specialty
# ─────────────────────────────────────────
APP_TITLE = "🌊 Water Network GIS Assistant"
APP_ICON = "🌊"

SYSTEM_PROMPTS = {
    "🌊 Water Utility Network Analyst": (
        "You are a senior GIS engineer specializing in water utility network management "
        "in the MENA region, with deep expertise in Esri Water Utility Network solutions, "
        "ArcGIS Utility Network, and QGIS-based network analysis. "
        "You understand the unique challenges of water infrastructure in arid regions: "
        "high pressure zones, seasonal demand variability, and NRW (Non-Revenue Water) detection. "
        "When discussing projections or coordinate systems, always cite the EPSG code. "
        "For Egypt specifically, you're familiar with EGSA 1907 (EPSG:22992) and WGS84 (EPSG:4326). "
        "Your audience is GIS engineers — be precise, technical, and concise. "
        "When asked for PyQGIS or Python code, use modern APIs: processing.run() for geoprocessing, "
        "never legacy QGIS 2 methods."
    ),
    "🛰️ Remote Sensing Analyst (MENA)": (
        "You are a remote sensing analyst specializing in satellite imagery of arid and "
        "semi-arid regions in the MENA area (Egypt, Saudi Arabia, UAE, Jordan). "
        "You work with Sentinel-2, Landsat-8/9, and high-resolution commercial imagery. "
        "You are skilled in: NDVI, NDWI, NDBI indices; land cover classification; "
        "urban growth detection; and agricultural monitoring in delta regions (especially the Nile Delta). "
        "Always mention EPSG codes when discussing projections. "
        "Be concise and scientific. Your audience is experienced GIS professionals."
    ),
    "🐍 PyQGIS Script Expert": (
        "You are an expert PyQGIS developer who writes modern, clean, and robust scripts "
        "for QGIS automation. "
        "Rules you always follow: "
        "1. Use processing.run() for all geoprocessing — never legacy QgsGeometry methods for analysis "
        "2. Always check if layers exist before using them "
        "3. Include proper error handling with try/except "
        "4. Add clear docstrings and inline comments "
        "5. Assume scripts run in the QGIS Python Console "
        "6. Never use ArcPy — this is PyQGIS "
        "7. After generating code, note any CRS assumptions "
        "Output ONLY Python code when asked for scripts — no markdown fences."
    ),
    "📍 Egyptian Address Parser": (
        "You are an expert in Egyptian addressing systems, handling mixed Arabic-English "
        "address strings from field surveys, cadastral records, and urban planning documents. "
        "You understand Egyptian governorates, districts (مراكز), and sub-districts. "
        "You normalize abbreviations: ش → شارع, م → ميدان, ك → كيلو. "
        "You handle landmarks as address components (e.g., 'بجوار مسجد' = 'next to mosque'). "
        "When asked to parse addresses, return structured JSON. "
        "If asked a general GIS question, answer it naturally in the same language the user used."
    ),
    "🌍 General GIS Assistant": (
        "You are a knowledgeable GIS assistant with broad expertise in spatial analysis, "
        "cartography, remote sensing, and GIS software (QGIS, ArcGIS Pro, GDAL, GeoPandas). "
        "You are familiar with open data sources, EPSG codes, and spatial statistics. "
        "Always cite EPSG codes when discussing coordinate reference systems. "
        "Adapt your technical depth to the user's apparent expertise level."
    ),
}

MODELS = {
    "Gemini 2.5 Flash ⚡ (Fast + Vision)": ("gemini", "gemini-2.5-flash"),
    "Gemini 2.5 Pro 🧠 (Smartest + Vision)": ("gemini", "gemini-2.5-pro"),
    "Groq Llama 3.3 70B ⚡ (Fastest Text)": ("groq", "llama-3.3-70b-versatile"),
    "Groq Llama 3.1 8B 🔥 (Ultra Fast)": ("groq", "llama-3.1-8b-instant"),
}

PRESET_PROMPTS = {
    "🌊 Water Network": [
        "Generate a PyQGIS script to calculate pipe lengths by material type from a 'pipes' layer",
        "What are the best practices for modeling pressure zones in ArcGIS Utility Network?",
        "Explain the difference between Geometric Network and Utility Network in Esri products",
        "How do I detect potential leakage locations using GIS and SCADA data integration?",
        "What EPSG code should I use for a water network map of Alexandria, Egypt?",
    ],
    "🛰️ Remote Sensing": [
        "How do I calculate NDWI from Sentinel-2 to detect water bodies in the Nile Delta?",
        "What band combinations are best for detecting urban heat islands in Cairo?",
        "Explain supervised vs unsupervised classification for land cover mapping",
        "How can I detect illegal agricultural expansion in desert areas using satellite imagery?",
    ],
    "🐍 PyQGIS": [
        "Write a PyQGIS script to batch reproject all shapefiles in a folder to EPSG:32636",
        "How do I create a spatial join between two layers using PyQGIS?",
        "Generate a script to calculate zonal statistics from a raster using polygon zones",
    ],
}


# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a clean, professional look
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    .main .block-container { padding-top: 2rem; }
    
    [data-testid="stSidebar"] { background-color: #1e293b; }
    
    h1 { 
        color: #38bdf8 !important; 
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    
    .stSelectbox label, .stTextInput label, .stTextArea label, .stSlider label {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    .token-badge {
        background: #1e3a5f;
        border: 1px solid #38bdf8;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.75rem;
        color: #38bdf8;
        display: inline-block;
        margin: 2px;
    }
    
    .preset-info {
        background: #1e293b;
        border-left: 3px solid #38bdf8;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }
    
    .stChatMessage { background-color: #1e293b !important; }
    
    .stButton button {
        background-color: #0369a1 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
    }
    
    .stButton button:hover {
        background-color: #0284c7 !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "current_image" not in st.session_state:
    st.session_state.current_image = None


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.divider()

    # API Keys
    st.markdown("**API Keys**")
    gemini_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="Get free at aistudio.google.com",
    )
    groq_key = st.text_input(
        "Groq API Key (optional)",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Get free at console.groq.com",
    )

    st.divider()

    # Model & Specialty
    model_label = st.selectbox("Model", list(MODELS.keys()))
    provider, model_id = MODELS[model_label]

    preset = st.selectbox("Specialty Preset", list(SYSTEM_PROMPTS.keys()))
    system_prompt = st.text_area(
        "System Prompt (editable)",
        value=SYSTEM_PROMPTS[preset],
        height=150,
        help="This shapes how the AI behaves. Customize for your use case.",
    )

    st.divider()

    # Parameters
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.4,
        step=0.1,
        help="0 = deterministic (code/extraction). 0.7 = balanced. 1+ = creative.",
    )
    max_tokens = st.select_slider(
        "Max Tokens",
        options=[256, 512, 1000, 2000, 4000],
        value=2000,
        help="Max response length. Higher = slower + more expensive.",
    )

    st.divider()

    # Image upload (for vision models)
    if provider == "gemini":
        st.markdown("**📸 Image Input** (vision)")
        uploaded_file = st.file_uploader(
            "Upload satellite image / map",
            type=["png", "jpg", "jpeg"],
            help="Attach an image to ask questions about it",
        )
        if uploaded_file:
            st.session_state.current_image = Image.open(uploaded_file)
            st.image(st.session_state.current_image, use_container_width=True)
        elif st.session_state.current_image:
            st.image(st.session_state.current_image,
                     caption="Current image", use_container_width=True)

        if st.session_state.current_image and st.button("🗑️ Remove Image"):
            st.session_state.current_image = None
            st.rerun()

    st.divider()

    # Stats & Actions
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()

    st.markdown(
        f'<span class="token-badge">~{st.session_state.total_tokens:,} tokens used</span>',
        unsafe_allow_html=True,
    )

    # Export chat
    if st.session_state.messages:
        chat_md = f"# Chat Export — {APP_TITLE}\n\n"
        chat_md += f"**System Prompt:** {system_prompt}\n\n---\n\n"
        for m in st.session_state.messages:
            role = "**You**" if m["role"] == "user" else "**Assistant**"
            chat_md += f"{role}\n\n{m['content']}\n\n---\n\n"
        st.download_button(
            "📥 Export Chat (.md)",
            data=chat_md,
            file_name="chat_export.md",
            mime="text/markdown",
        )


# ─────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────
st.title(APP_TITLE)

# Specialty selector determines which preset prompts to show
specialty_key = None
for k in PRESET_PROMPTS:
    if k[:2] in preset:
        specialty_key = k
        break
if not specialty_key:
    specialty_key = list(PRESET_PROMPTS.keys())[0]

# Preset prompt buttons
st.markdown('<div class="preset-info">💡 <strong>Quick prompts</strong> — click to send instantly:</div>', unsafe_allow_html=True)
preset_cols = st.columns(min(len(PRESET_PROMPTS[specialty_key]), 3))
for i, p in enumerate(PRESET_PROMPTS[specialty_key]):
    with preset_cols[i % 3]:
        short_label = p[:42] + "…" if len(p) > 42 else p
        if st.button(short_label, key=f"preset_{i}", use_container_width=True):
            st.session_state["pending_prompt"] = p

st.divider()

# Chat history display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ─────────────────────────────────────────
# HELPER: Call the right provider
# ─────────────────────────────────────────
def call_gemini(user_text, history, sys_prompt, img, temp, max_tok, model):
    genai.configure(api_key=gemini_key)
    gemini_model = genai.GenerativeModel(model, system_instruction=sys_prompt)

    gemini_history = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = gemini_model.start_chat(history=gemini_history)

    content = [user_text]
    if img:
        content.append(img)

    response = chat.send_message(
        content,
        generation_config=genai.GenerationConfig(
            temperature=temp,
            max_output_tokens=max_tok,
        ),
        stream=True,
    )
    return response


def call_groq(user_text, history, sys_prompt, temp, max_tok, model):
    client = Groq(api_key=groq_key)
    messages = [{"role": "system", "content": sys_prompt}]
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temp,
        max_tokens=max_tok,
        stream=True,
    )
    return response


# ─────────────────────────────────────────
# CHAT INPUT & RESPONSE
# ─────────────────────────────────────────
# Handle preset prompt injection
if "pending_prompt" in st.session_state:
    pending = st.session_state.pop("pending_prompt")
    st.session_state.messages.append({"role": "user", "content": pending})
    with st.chat_message("user"):
        st.markdown(pending)

    user_text = pending
    run_inference = True
else:
    user_text = st.chat_input("Ask your GIS question…")
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)
        run_inference = True
    else:
        run_inference = False

if run_inference:
    # Validate keys
    if provider == "gemini" and not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
        st.stop()
    if provider == "groq" and not groq_key:
        st.error("⚠️ Please enter your Groq API Key in the sidebar.")
        st.stop()

    history_for_api = st.session_state.messages[:-1]  # all but current

    with st.chat_message("assistant"):
        try:
            if provider == "gemini":
                response = call_gemini(
                    user_text,
                    history_for_api,
                    system_prompt,
                    st.session_state.current_image,
                    temperature,
                    max_tokens,
                    model_id,
                )
                full_response = st.write_stream(
                    chunk.text for chunk in response if chunk.text
                )

            elif provider == "groq":
                if st.session_state.current_image:
                    st.warning(
                        "⚠️ Groq models are text-only. Image will be ignored. "
                        "Switch to a Gemini model for vision tasks."
                    )
                response = call_groq(
                    user_text,
                    history_for_api,
                    system_prompt,
                    temperature,
                    max_tokens,
                    model_id,
                )
                full_response = st.write_stream(
                    chunk.choices[0].delta.content or ""
                    for chunk in response
                )

            # Estimate tokens (rough: 1 token ≈ 4 chars for English, 2 chars for Arabic)
            estimated_tokens = (len(user_text) + len(full_response)) // 3
            st.session_state.total_tokens += estimated_tokens

            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                st.error("⚠️ Rate limit reached. Wait a moment and try again, or switch to a different model.")
            elif "401" in error_msg or "PermissionDenied" in error_msg:
                st.error("⚠️ API key invalid or expired. Please check your key in the sidebar.")
            elif "503" in error_msg:
                st.error("⚠️ Provider is temporarily unavailable. Try another model.")
            else:
                st.error(f"⚠️ Error: {error_msg}")
