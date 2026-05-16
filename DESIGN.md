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
For a water network map of Alexandria, Egypt, the most appropriate projected coordinate system for accurate measurements of distance, area, and bearing is EGSA 1907 (EPSG:22992).

While WGS84 (EPSG:4326) is commonly used for global positioning and data exchange, it is a geographic coordinate system (latitude/longitude) and not ideal for engineering-grade local measurements required for utility network management. EGSA 1907 is a national projected coordinate system specifically designed for Egypt, making it suitable for precise mapping and analysis within Alexandria.

**Reflection:** [the app worked in a good way]

---

#### Test 2
**Question:** "Generate a PyQGIS script to calculate pipe lengths by material type"  
**Actual response:**  
Here's a PyQGIS script to calculate pipe lengths by material type. This script assumes your pipe network layer is the active layer in QGIS, contains line geometries, and has an attribute field for 'material'.

import qgis.utils
from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsWkbTypes

def calculate_pipe_lengths_by_material():
    """
    Calculates the total length of pipes for each material type
    in the active QGIS layer.

    Assumptions:
    - The active layer is the pipe network layer.
    - The layer contains line geometries representing pipes.
    - There is an attribute field named 'material' (case-sensitive)
      that stores the pipe material type (e.g., 'PVC', 'DI', 'AC').
    - The layer's CRS is a projected coordinate system (e.g., EGSA 1907, EPSG:22992)
      for accurate length calculations in meters. If it's a geographic CRS (like WGS84),
      the length will be in degrees, which is not suitable for engineering analysis.
    """

    layer = qgis.utils.iface.activeLayer()

    if not layer:
        qgis.utils.iface.messageBar().pushMessage(
            "Error", "No active layer selected. Please select your pipe network layer.",
            level=qgis.utils.iface.messageBar().CRITICAL, duration=5
        )
        return

    if layer.wkbType() not in [QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString]:
        qgis.utils.iface.messageBar().pushMessage(
            "Error", f"Layer '{layer.name()}' is not a line layer. Please select a line layer.",
            level=qgis.utils.iface.messageBar().CRITICAL, duration=5
        )
        return

    # Check CRS type
    if layer.crs().isGeographic():
        qgis.utils.iface.messageBar().pushMessage(
            "Warning",
            f"Layer '{layer.name()}' uses a geographic CRS ({layer.crs().authid()}). "
            "Lengths will be calculated in degrees, which is not suitable for engineering. "
            "Please reproject your layer to a projected CRS like EGSA 1907 (EPSG:22992) for accurate results.",
            level=qgis.utils.iface.messageBar().WARNING, duration=10
        )
        # Optionally, you could stop here or attempt a reprojection on the fly,
        # but for precise engineering, reprojecting the source data is best.

    # Define the field name for material type
    material_field_name = 'material' # Adjust this if your field name is different

    if layer.fields().indexOf(material_field_name) == -1:
        qgis.utils.iface.messageBar().pushMessage(
            "Error",
            f"Field '{material_field_name}' not found in layer '{layer.name()}'. "
            "Please ensure the material attribute field exists and is correctly named.",
            level=qgis.utils.iface.messageBar().CRITICAL, duration=7
        )
        return

    pipe_lengths_by_material = {}
    total_pipes_processed = 0
    total_length_all_materials = 0.0

    qgis.utils.iface.messageBar().pushMessage(
        "Info", f"Calculating pipe lengths by material for layer: '{layer.name()}'...",
        level=qgis.utils.iface.messageBar().INFO
    )

    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom.isMultipart():
            # Handle MultiLineString geometries
            for part in geom.asMultiLineString():
                length = QgsGeometry.fromPolylineXY(part).length()
                material = feature[material_field_name]
                pipe_lengths_by_material.setdefault(material, 0.0)
                pipe_lengths_by_material[material] += length
                total_length_all_materials += length
        else:
            # Handle LineString geometries
            length = geom.length()
            material = feature[material_field_name]
            pipe_lengths_by_material.setdefault(material, 0.0)
            pipe_lengths_by_material[material] += length
            total_length_all_materials += length

        total_pipes_processed += 1

    qgis.utils.iface.messageBar().pushMessage(
        "Success", f"Finished processing {total_pipes_processed} pipes.",
        level=qgis.utils.iface.messageBar().SUCCESS, duration=5
    )

    # Output results
    print("\n--- Pipe Lengths by Material Type ---")
    if layer.crs().isGeographic():
        print("Note: Lengths are in degrees due to geographic CRS. Reproject for meters.")
    else:
        print(f"Lengths are in {layer.crs().mapUnits()} (e.g., meters for EGSA 1907).")

    for material, length in sorted(pipe_lengths_by_material.items()):
        print(f"Material: {material:<20} | Total Length: {length:,.2f}")

    print(f"\nTotal Length of all pipes: {total_length_all_materials:,.2f}")
    print("-------------------------------------\n")

# Run the script
if __name__ == '__main__':
    calculate_pipe_lengths_by_material()
How to use this script:

Open QGIS.
Load your water pipe network layer into the QGIS project.
Select your pipe network layer in the Layers panel (make it the active layer).
Open the Python Console in QGIS (Plugins → Python Console).
Copy and paste the entire script into the console.
Press Enter to run it.
Important Considerations:

material_field_name = 'material': Crucially, adjust this line to match the exact name of the attribute field in your pipe layer that stores the material type (e.g., 'PIPE_MAT', 'TYPE', 'MATERIAL_CODE'). It's case-sensitive.
Coordinate Reference System (CRS): The script includes a warning if your layer is in a geographic CRS (like WGS84, EPSG:4326)

**Reflection:** Does it use processing.run()?
No.
The script correctly avoids processing.run() and instead uses the direct PyQGIS API (layer.getFeatures(), feature.geometry().length(), QgsGeometry, etc.). This is the preferred approach for this task because:

Calculating length by attribute is simple and efficient with direct iteration.
Using processing.run() (e.g., "qgis:statisticsbycategories" or "native:aggregate") would be heavier and less flexible for custom output formatting and multipart handling.
Direct API gives better control over multipart lines and custom messaging.

This is a strength of the response.
Does it handle missing layers?
Yes, very well.

Checks for no active layer → shows clear CRITICAL message.
Validates that the layer is a line layer (LineString or MultiLineString).
Checks for the existence of the material field.
Warns about geographic CRS (very important for Egyptian users working with pipe networks).

---

#### Test 3
**Question:** "What are the main causes of Non-Revenue Water (NRW) in Egyptian cities?"  
**Actual response:**  
Non-Revenue Water (NRW) is a critical challenge for water utilities in Egyptian cities, exacerbated by the arid climate and the need for efficient water resource management. The main causes can be broadly categorized into Physical Losses and Commercial (Apparent) Losses:

1. Physical Losses (Real Losses):

Aging Infrastructure: A significant portion of the water network in older Egyptian cities consists of aging pipes (e.g., Asbestos Cement (AC), Cast Iron, older PVC) that have exceeded their design life. This leads to:
Pipe Leaks: Deterioration, corrosion, and material fatigue cause cracks, joint failures, and pinhole leaks.
Pipe Bursts: Sudden, large-scale failures often due to extreme pressure fluctuations or structural weakness.
High Pressure Zones: Many urban networks, especially in areas with varying topography or where pumps operate to ensure supply, experience high operating pressures. This significantly increases the rate of leakage from existing defects and accelerates pipe deterioration.
Intermittent Supply: While less common in major cities now, historical or localized intermittent supply can cause frequent pressure transients (water hammer), stressing pipes and joints, leading to fatigue and failure.
Poor Installation & Maintenance: Substandard pipe laying practices, inadequate jointing, and insufficient backfilling during initial construction or repairs can create weak points prone to leakage. A lack of proactive leak detection and repair programs also contributes.
Damage by Third Parties: Excavation work by other utilities (telecom, electricity, gas) or construction activities frequently damages water pipelines.
Reservoir and Tank Overflows: Although less common in distribution networks, unmonitored or poorly controlled service reservoirs can lead to significant water loss through overflow.
2. Commercial Losses (Apparent Losses):

Illegal Connections and Water Theft: This is a substantial issue, particularly in informal settlements or areas with socio-economic disparities. Unauthorized connections bypass meters entirely, leading to unbilled consumption.
Inaccurate Metering:
Old/Worn-out Meters: Water meters have a finite lifespan, and their accuracy degrades over time due to wear and tear, especially in areas with high sediment content.
Damaged Meters: Physical damage, tampering, or exposure to harsh conditions can render meters inaccurate or non-functional.
Incorrect Meter Sizing: Mismatched meter sizes for actual flow rates can lead to under-registration, especially at low flows.
Lack of Calibration/Maintenance: Insufficient programs for meter testing, calibration, and replacement.
Data Handling and Billing Errors:
Incorrect Customer Data: Errors in customer records, property addresses, or meter locations.
Manual Reading Errors: Mistakes during manual meter reading or data entry into billing systems.
Billing System Malfunctions: Software glitches or incorrect tariff applications.
Unregistered Connections: Connections that exist but are not formally recorded in the utility's customer database or billing system.
Unbilled Authorized Consumption: While not strictly a "loss" in the sense of waste, this refers to water consumed for public services (e.g., firefighting, street cleaning, public fountains) that is not metered or accounted for in revenue, thus contributing to the NRW percentage.
Addressing NRW in Egyptian cities requires a multi-faceted approach, integrating robust GIS for asset management (e.g., using ArcGIS Utility Network), advanced leak detection technologies, comprehensive metering programs, and improved data management practices. 
**Reflection:** Regionally accurate? Yes. The response correctly highlights the main causes of NRW in Egyptian cities (aging AC/CI pipes, high pressure, illegal connections, inaccurate meters, etc.).
Suggests GIS-based detection methods? Partially. It briefly mentions using GIS for asset management but does not detail practical GIS applications (e.g., DMA mapping, leak clustering, pressure analysis).
Overall: Good, well-structured answer with solid Egyptian context. Could be improved by making the GIS part more specific and actionable.

---

#### Test 4
**Question:** "How do I model pressure zones in ArcGIS Utility Network?"  
**Actual response:**  
Modeling pressure zones in ArcGIS Utility Network is a fundamental aspect of water utility management, allowing for precise isolation, tracing, and analysis of distinct hydraulic areas. The Utility Network doesn't calculate pressure values (that's for hydraulic modeling software like EPANET, WaterGEMS, or InfoWater Pro), but it provides the robust framework to define and manage these zones based on connectivity and controlling devices.

Here's how to model pressure zones in ArcGIS Utility Network, focusing on the core concepts and steps:

Core Concept: Subnetworks
In the Utility Network, pressure zones are modeled as subnetworks. A subnetwork represents a connected portion of the network that operates under a specific set of conditions, typically defined by a controller (e.g., a pump, a tank, or a pressure-regulating valve).

Key Components for Pressure Zone Modeling:
Subnetwork Controllers: These are the devices that define the origin or "source" of a pressure zone. For water, common controllers include:

Pumps: The outlet of a pump can define the start of a pressure zone.
Tanks/Reservoirs: The outlet of a tank/reservoir, providing gravity feed, defines a pressure zone.
Pressure Reducing Valves (PRVs): The downstream side of a PRV acts as a controller for the lower pressure zone it creates.
Pressure Sustaining Valves (PSVs): The upstream side of a PSV acts as a controller for the higher pressure zone it maintains.
Network Categories: Ensure your asset types have appropriate network categories assigned. For pressure zones, critical categories include:

Subnetwork Controller (for pumps, tanks, PRVs, PSVs).
Isolation Valve (for all valves that can isolate parts of the network).
Pressure Regulating Valve (for PRVs and PSVs, if you want specific behavior).
Terminal Configurations: For devices like pumps, PRVs, and PSVs, you need to define their terminal configurations
  
**Reflection:** Does the answer distinguish Utility Network from old Geometric Network?
No.
The response explains pressure zones well using the modern Utility Network (subnetworks, controllers, terminals, etc.), but it makes no mention of the old Geometric Network. It does not clarify that this method applies only to ArcGIS Utility Network (the current standard) and is fundamentally different from how pressure zones were modeled in the legacy Geometric Network.
Overall: Technically good content, but misses an important clarification for users who might be migrating from the old system.

---

#### Test 5
**Question:** "Explain the difference between topology rules and connectivity rules in a water network"  
**Actual response:**  
In the context of a water network, particularly when working with Esri's Geodatabase and ArcGIS Utility Network, "topology rules" and "connectivity rules" serve distinct but complementary purposes.

1. Topology Rules (Geodatabase Topology)
Focus: Geometric integrity and spatial relationships of features. Purpose: To ensure that features are geographically correct, maintain defined spatial relationships, and prevent common drawing or data entry errors. They enforce data quality at a geometric level.

How they work:

Defined on a Geodatabase Topology dataset, which includes one or more feature classes.
They specify how features from one or more feature classes should relate to each other spatially (e.g., "Pipes must not overlap," "Valves must be covered by Pipes").
Enforcement is typically through a validation process. Errors are flagged and must be manually reviewed and fixed.
Examples in a Water Network:

"Pipes must not overlap": Prevents duplicate pipe segments, which could lead to incorrect length calculations or flow modeling.
"Valves must be covered by Pipes": Ensures that a valve feature is always located directly on top of a pipe segment, indicating it controls that pipe.
"Junctions (e.g., fittings, hydrants) must be at endpoints of Pipes": Ensures that point features intended to connect pipes are correctly snapped to the pipe ends, establishing geometric connectivity.
"Pipes must not have dangles (except at dead ends)": Identifies pipe segments that are not connected at both ends, potentially indicating missing connections or errors (unless it's a legitimate dead-end service lateral).
"Pipes must not self-overlap": Prevents a single pipe feature from crossing over itself.
Analogy: Think of topology rules as the "grammar" for how your map features are drawn. They ensure the map is geometrically sound and free from spatial inconsistencies.

2. Connectivity Rules (ArcGIS Utility Network)
Focus: Logical connections and valid attachments between network features, defining how resources flow through the network. Purpose: To define the permissible ways that network features (assets) can connect and interact with each other, enabling network tracing, analysis, and ensuring the network behaves as expected hydraulically. They enforce data quality at a logical and functional level.

How they work:

Defined directly within the ArcGIS Utility Network dataset.
They specify which asset types (e.g., 'Distribution Main', 'Service Line', 'Gate Valve') can connect to which other asset types, and under what conditions (e.g., at a specific terminal for devices).
Enforcement is automatic and real-time during editing. If an editor attempts to make an invalid connection, the Utility Network prevents it.
Types of Connectivity Rules:

Junction-Edge Rules: Define which junction features can connect to which edge features (e.g., "A Hydrant (junction) can connect to a Distribution Main (edge)").
Edge-Junction-Edge Rules: Define how two edge features can connect through a junction feature (e.g., "A Distribution Main (edge) can connect to another Distribution Main (edge) through a Fitting (junction)").
Junction-Junction Rules: Define how two junction features can connect directly less common in water, but possible for complex 
**Reflection:** [Is the explanation technically accurate? Is it appropriate for a GIS engineer?] yes it is.

---

### Edge Cases (3 cases)

#### Test 6 — Out-of-scope question
**Question:** "Can you help me write a job application email?"  
**Actual response:**  
Okay, I can definitely help you draft a professional and impactful job application email, leveraging your specific expertise as a GIS Engineer specializing in water utility networks in the MENA region.

This template is designed to be concise, highlight your key skills, and show your understanding of the industry. Remember to customize the bracketed [ ] sections thoroughly for each application.

Subject: Application for [Job Title] - [Your Name]

Dear [Hiring Manager Name or "Hiring Team"],

I am writing to express my keen interest in the [Job Title] position, as advertised on [Platform where you saw the ad, e.g., LinkedIn, company website]. My extensive experience as a GIS Engineer specializing in water utility network management, particularly within the MENA region, aligns perfectly with the requirements outlined.

With [X years, e.g., 7+ years] of experience, I possess deep expertise in Esri's ArcGIS platform, including ArcGIS Pro, Enterprise, and critically, the ArcGIS Utility Network. My background includes comprehensive water utility network management, from data model design and implementation to advanced spatial analysis. I am proficient in PyQGIS and Python scripting for automation and custom tool development, enhancing efficiency in GIS workflows.

I have a strong understanding of the unique challenges facing water infrastructure in arid regions, such as high pressure zones, seasonal demand variability, and Non-Revenue Water (NRW) detection and reduction strategies. My experience extends to leveraging GIS for asset management, network analysis, and supporting hydraulic modeling efforts. I am also familiar with regional coordinate systems like EGSA 1907 (EPSG:22992), ensuring data accuracy and consistency.

I am particularly drawn to [Company Name]'s commitment to [mention something specific about the company, e.g., sustainable water management, innovative solutions, their projects in the region]. I am confident that my technical skills and regional understanding would enable me to contribute significantly to your team's objectives in [mention specific area, e.g., optimizing network performance, reducing NRW, implementing new GIS solutions].

Thank you for considering my application. I have attached my resume/CV and a detailed cover letter for your review. I am eager to discuss how my qualifications can benefit [Company Name] further and welcome the opportunity for an interview.

Sincerely,

[Your Full Name] [Your Phone Number] [Your Email Address] [Your LinkedIn Profile URL (Optional, but recommended)]

Key Customization Points & Tips:

[Job Title]: Be precise.
[Platform where you saw the ad]: Always include this.
[Hiring Manager Name or "Hiring Team"]: Try your best to find a specific name. If not, "Dear Hiring Team" or "Dear [Company Name] Recruitment Team" is acceptable.
[X years]: Quantify your experience.
[Company Name]: Research the company! Mentioning something specific shows genuine interest and that you've done your homework.
 
**Reflection:** [Does the model refuse, redirect, or just answer? What's the right behavior?]
Does the model refuse, redirect, or just answer?
The model just answers directly and provides a complete, well-written response.
What's the right behavior?
This is the correct and excellent behavior. Not only does it answer helpfully, but it also personalizes the email using the user’s actual background (GIS Engineer, water utilities, ArcGIS Utility Network, PyQGIS, NRW, EGSA 1907, MENA region). This adds significant value. Refusing this type of request would be inappropriate.

---

#### Test 7 — Ambiguous question
**Question:** "How do I buffer this?"  
**Actual response:**  
To buffer a layer in PyQGIS, you'll use the processing framework, which provides access to all QGIS geoprocessing tools.

First, let's understand why you might buffer in a water network context:

Exclusion Zones: Define areas where no construction or excavation should occur near critical pipelines.
Impact Assessment: Identify properties or environmental features within a certain distance of a potential pipe burst or contamination event.
Right-of-Way: Delineate the legal or operational corridor for pipelines.
Proximity Analysis: Find all assets (e.g., other utilities, buildings) within a specified distance of your water mains.
Here's a PyQGIS script to buffer the active layer, with important considerations for water utility data: 

**Reflection:** [Does the model ask for clarification or make assumptions? What layer? What distance? What CRS?]
Reflection:
Does the model ask for clarification or make assumptions?
The model makes assumptions without asking for clarification.
What layer? What distance? What CRS?
It assumes the user wants to buffer the active layer in a water network context, but does not ask for:

Which layer to buffer
The buffer distance
The unit or CRS (critical for accurate buffering)
Whether to dissolve, include attributes, etc.

Overall: The response jumps straight into code and context without seeking necessary details. It should have asked clarifying questions first, as "How do I buffer this?" is highly ambiguous.
---

#### Test 8 — Arabic-language query
**Question:** "ما هو أفضل نظام إسقاط للخرائط في مصر؟"  
**Actual response:**  
لخرائط المياه وشبكات المرافق في مصر، أفضل نظام إسقاط (Projected Coordinate System) هو:

EGSA 1907 (EPSG:22992)

لماذا EGSA 1907 هو الأفضل؟

نظام إحداثيات وطني: تم تصميم EGSA 1907 خصيصًا لمصر، مما يجعله الأكثر دقة للقياسات المحلية للمسافات والمساحات والاتجاهات داخل البلاد.
نظام إسقاطي (Projected): على عكس أنظمة الإحداثيات الجغرافية (مثل WGS84)، فإن EGSA 1907 هو نظام إسقاطي، مما يعني أنه يحول الإحداثيات الكروية إلى إحداثيات مستوية (س، ص) بوحدات قياس خطية (مثل المتر). هذا ضروري جدًا لأعمال الهندسة المدنية وإدارة الشبكات التي تتطلب دقة عالية في القياسات.
الدقة الهندسية: لمهندس GIS المتخصص في شبكات المياه، فإن الدقة في حساب أطوال الأنابيب، ومواقع الصمامات، ومساحات مناطق الخدمة، أمر بالغ الأهمية. يوفر EGSA 1907 هذه الدقة المطلوبة.
ملاحظة حول WGS84 (EPSG:4326):

بينما يُستخدم WGS84 (EPSG:4326) على نطاق واسع عالميًا لبيانات GPS وتبادل البيانات، فإنه نظام إحداثيات جغرافي (خطوط طول وعرض). هذا يعني أن وحدات القياس تكون بالدرجات، وهي غير مناسبة على الإطلاق لإجراء قياسات هندسية دقيقة للمسافات والمساحات. لذلك، يجب دائمًا إعادة إسقاط البيانات إلى EGSA 1907 عند العمل على مشاريع شبكات المياه داخل مصر. 
**Reflection:** [Did the model answer in Arabic? Did it cite the correct EPSG codes?]
**Reflection:**

**Did the model answer in Arabic?**  
**Yes.** The entire response is written in clear, professional Arabic.

**Did it cite the correct EPSG codes?**  
**Yes.** It correctly identifies EGSA 1907 as EPSG:22992 and WGS84 as EPSG:4326.

**Overall:** Excellent response. It is regionally accurate, technically correct, and properly matches the user’s language.
---

### Adversarial Cases (2 cases)

#### Test 9 — Asking for wrong information
**Question:** "Use EPSG:9999 for my Egyptian water network project"  
**Actual response:**  
I must strongly advise against using EPSG:9999 for your Egyptian water network project.

EPSG:9999 is a placeholder code and does not represent a valid, defined, or recognized Coordinate Reference System (CRS). Using it would lead to:

Data Inaccuracy: Your spatial data would lack a proper georeference, making all distance, area, and bearing calculations incorrect or meaningless.
Interoperability Issues: You would be unable to share your data effectively with other systems, stakeholders, or hydraulic modeling software, as they would not understand the spatial context.
Project Failure: Any engineering analysis, design, or construction based on data with an undefined CRS would be fundamentally flawed.
For an Egyptian water network project, it is absolutely critical to use a well-defined and appropriate projected coordinate system. As previously discussed, the recommended CRS for accurate engineering-grade measurements in Egypt is:

EGSA 1907 (EPSG:22992)
This system is specifically designed for Egypt, provides accurate linear measurements (in meters), and is essential for precise utility network management, hydraulic analysis, and construction.

If you are encountering issues with your current CRS or have specific requirements, please clarify, and I can guide you on how to properly define or reproject your data. However, EPSG:9999 is never a solution for a production-level GIS project. 
**Reflection:** [Did the model push back and correct the invalid EPSG code? Or did it agree?]
**Reflection:**

**Did the model push back and correct the invalid EPSG code? Or did it agree?**  
**Yes, it pushed back strongly and correctly.**

The model firmly refused the invalid EPSG:9999, explained why it is problematic, and clearly recommended the proper alternative (EGSA 1907 – EPSG:22992). It maintained a professional yet assertive tone suitable for technical advice.

**Overall:** Excellent response. This is the correct behavior when a user requests something technically wrong or harmful to their project.

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
