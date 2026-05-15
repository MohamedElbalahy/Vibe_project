# 🌊 Water Utility Network GIS Assistant

An AI-powered assistant for GIS engineers working with water utility networks,
satellite imagery analysis, and QGIS automation in the MENA region.

Built with Streamlit + Gemini 2.5 Flash + Groq Llama 3.3 70B.

---

## Features

- 🌊 **Specialized persona** for water utility network management (MENA region)
- 🛰️ **Satellite image analysis** via Gemini's vision capabilities
- 🐍 **PyQGIS script generation** with modern API enforcement
- 📍 **Egyptian address parsing** (Arabic + English, mixed)
- ⚡ **Multi-provider support**: Gemini (vision) + Groq (fast text)
- 🌡️ **Temperature & token control** for different task types
- 💬 **Streaming responses** with chat history
- 📥 **Export chat to Markdown**

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/MohamedElbalahy/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your keys
```

Or set them directly in the app's sidebar.

### 4. Run

```bash
streamlit run app.py
```

---

## Get API Keys (all free)

| Provider | Link | Free Tier |
|----------|------|-----------|
| **Gemini** | [aistudio.google.com](https://aistudio.google.com) | 15 RPM, 1000 RPD |
| **Groq** | [console.groq.com](https://console.groq.com) | 30 RPM, 14.4K RPD |

---

## Screenshots

[Add screenshots here after running the app]

---

## Project structure

```
.
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── DESIGN.md           # Design document (graded)
├── .env.example        # API key template
└── .gitignore
```

---

## Tech stack

- **Frontend:** Streamlit
- **AI Providers:** Google Gemini 2.5 Flash/Pro, Groq Llama 3.3 70B
- **Image handling:** Pillow (PIL)
- **Language:** Python 3.10+

---

*ITI Gen AI Course · GIS Track · Day 3 Lab Assignment*
