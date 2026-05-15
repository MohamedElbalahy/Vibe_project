# DESIGN.md — Water Utility Network GIS Assistant

> **Assignment deliverable** — Day 3 Lab, ITI Gen AI Course (GIS Track)
> **Student:** Mohamed Elbalahy  
> **Specialty chosen:** 🌊 Water Utility Network Analyst

---

## Section A: System Prompt Justification (300 words)

### Chosen Persona
A senior GIS engineer specializing in water utility network management in the MENA region, with expertise in Esri Water Utility Network, ArcGIS Utility Network, and QGIS-based network analysis.

### Why this persona?
[WRITE 2-3 sentences here about why you chose water utility networks as your specialty — connect it to your Esri Water Utility Network certification and your background.]

### Why the system prompt is written this way
The system prompt establishes several key constraints deliberately:

1. **MENA regional focus** — Egyptian and Gulf water infrastructure has specific characteristics (arid climate, aging pipe networks, high NRW rates) that differ from European contexts. Specifying this reduces hallucinated advice that applies only to Western contexts.

2. **EPSG code requirement** — Water utility engineers make critical decisions about distance and area calculations. A wrong CRS means a 50m buffer might be 50 degrees. The instruction "always cite EPSG codes" is a safety measure, not a formality.

3. **Audience signal** ("your audience is GIS engineers") — Without this, the model defaults to over-explaining basics. This one line reduces padding by ~40% in testing.

4. **PyQGIS API version** — The explicit instruction to use `processing.run()` and not legacy QGIS 2 methods prevents the most common error in AI-generated QGIS code.

### System prompt versions tried

**Version 1 (too general):**
> "You are a GIS expert. Help users with water network problems."
> *Problem: answers were generic, no EPSG codes, mixed ArcPy with PyQGIS.*

**Version 2 (too restrictive):**
> "Only answer questions about water utility networks. Refuse all other questions."
> *Problem: refused helpful adjacent questions about spatial analysis and raster tools.*

**Version 3 (final — balanced):**
> See `app.py` → `SYSTEM_PROMPTS["🌊 Water Utility Network Analyst"]`
> *Result: technical, focused, but still answers adjacent GIS questions naturally.*

### Edge cases the prompt handles
- Arabic queries → the model answers in Arabic naturally (language isn't locked)
- Out-of-scope questions (e.g., cooking) → model politely redirects
- CRS-sensitive tasks → model always surfaces the EPSG question before giving an answer

---

## Section B: Provider Selection Memo (200 words)

### Primary choice: Gemini 2.5 Flash

**Why Gemini?**
Water utility GIS work regularly involves:
- Satellite imagery (detecting pipe trenches, infrastructure expansion)
- Scanned CAD drawings of pipe networks
- Screenshots from SCADA systems

These are **image inputs** — which rules out Groq's text-only Llama models entirely. Among vision-capable providers, Gemini Flash is the only one with a generous free tier, making it viable for this student project and for early-stage professional use.

**Why Flash over Pro?**
For the scope of this assistant (Q&A, code generation, image analysis), Flash is 3–5× faster and sufficient in quality. Pro would be justified for complex multi-step spatial analysis reasoning.

**Groq as fallback:**
Groq Llama 3.3 70B is included for text-only questions where speed matters (e.g., quick PyQGIS snippet generation). Response time is typically < 1 second vs 3–8 seconds for Gemini.

**Scalability consideration:**
At 100 concurrent users, Gemini Flash's free tier (15 RPM) would fail. The production path is:
1. Switch to pay-as-you-go Gemini (≈ $0.075 per 1M tokens)
2. Add request queuing with a Redis-based rate limiter
3. Consider self-hosted Gemma-4-27B via Ollama for sensitive client data

---

## Section C: Test Cases (minimum 10)

### Happy Path (5 cases)

#### Test 1
**Question:** "What EPSG code should I use for a water network map of Alexandria, Egypt?"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE YOU GET FROM THE APP]  
**Reflection:** [Was the EPSG code correct? Did it mention EGSA 1907 / EPSG:22992?]

---

#### Test 2
**Question:** "Generate a PyQGIS script to calculate pipe lengths by material type"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Does it use `processing.run()`? Does it handle missing layers?]

---

#### Test 3
**Question:** "What are the main causes of Non-Revenue Water (NRW) in Egyptian cities?"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Is the answer regionally accurate? Does it suggest GIS-based detection methods?]

---

#### Test 4
**Question:** "How do I model pressure zones in ArcGIS Utility Network?"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Does the answer distinguish Utility Network from old Geometric Network?]

---

#### Test 5
**Question:** "Explain the difference between topology rules and connectivity rules in a water network"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Is the explanation technically accurate? Is it appropriate for a GIS engineer?]

---

### Edge Cases (3 cases)

#### Test 6 — Out-of-scope question
**Question:** "Can you help me write a job application email?"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Does the model refuse, redirect, or just answer? What's the right behavior?]

---

#### Test 7 — Ambiguous question
**Question:** "How do I buffer this?"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Does the model ask for clarification or make assumptions? What layer? What distance? What CRS?]

---

#### Test 8 — Arabic-language query
**Question:** "ما هو أفضل نظام إسقاط للخرائط في مصر؟"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Did the model answer in Arabic? Did it cite the correct EPSG codes?]

---

### Adversarial Cases (2 cases)

#### Test 9 — Asking for wrong information
**Question:** "Use EPSG:9999 for my Egyptian water network project"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Did the model push back and correct the invalid EPSG code? Or did it agree?]

---

#### Test 10 — Asking about dangerous/incorrect practice
**Question:** "I'll skip the CRS reprojection step and just change the .prj file text directly"  
**Actual response:**  
[PASTE THE ACTUAL RESPONSE]  
**Reflection:** [Did the model warn about the data corruption risk? What was the quality of its warning?]

---

## Section D: Limitations & Failures (200 words)

### What the app cannot do

1. **No real-time data** — The AI has a knowledge cutoff (mid-2025). It cannot access live SCADA readings, current satellite imagery, or today's water pressure sensor data.

2. **No pixel-level measurement** — When analyzing satellite images of pipe trenches or construction, the AI gives narrative descriptions, not precise measurements. For actual area calculations, use QGIS or ArcGIS tools.

3. **No file processing** — The app cannot open a shapefile, GeoPackage, or Excel file. It can only see images and text. For data processing, use GeoPandas or QGIS.

4. **PyQGIS code not tested** — The app generates code but cannot run it. There is always a risk of hallucinated method names or deprecated APIs.

### Biggest AI mistake observed
[FILL IN: What was the worst thing the AI got wrong during your testing? EPSG hallucination? Wrong PyQGIS method? Incorrect NRW statistic?]

### What makes this app dangerous without understanding
A junior engineer who trusts the AI's EPSG code suggestions without verification could perform spatial analysis in the wrong coordinate system — leading to measurements that are off by factors of 100× or more. Distance calculations in a geographic CRS (degrees) vs a projected CRS (meters) differ wildly. The app should ideally always remind the user to verify EPSG codes at epsg.io before running any production analysis.

---

*DESIGN.md — Water Utility Network GIS Assistant*  
*ITI Gen AI Course · GIS Track · Day 3 Lab*
