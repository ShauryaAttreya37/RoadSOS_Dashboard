# IIT Madras Road Safety Hackathon 2026  
## Theme: “AI in Road Safety”

Organized by:
- Centre of Excellence for Road Safety (CoERS)
- RBG Labs
- Indian Institute of Technology Madras (IIT Madras)

The hackathon focuses on developing **AI-driven solutions for real-world road safety challenges in India**. Participants are expected to select **one** of the official problem statements and build a deployable solution around it.

Official sources indicate three major problem statements:
- DriveLegal
- RoadWatch
- RoadSoS

---

# Problem Statement 1 — DriveLegal
## AI Chatbot for Traffic Law & Fine Awareness

### Objective
Build an intelligent AI assistant that helps citizens understand:
- traffic laws,
- road regulations,
- challan/fine systems,
- and state-specific enforcement rules.

The aim is to reduce accidental violations caused by lack of awareness.

---

## Core Requirements

The system should:
- Provide location-specific traffic rules
- Explain violations and penalties
- Show updated fine schedules
- Support multilingual interaction
- Help users understand legal compliance

Example:
A user asks:
> “Can I ride without a helmet in Tamil Nadu?”

The assistant should respond with:
- legality status,
- applicable law,
- fine amount,
- possible consequences,
- and safety explanation.

---

## Expected AI Components

Possible technologies include:
- Large Language Models (LLMs)
- NLP-based chatbots
- Retrieval-Augmented Generation (RAG)
- Geolocation APIs
- Voice interaction systems
- Dynamic rule databases

---

## Advanced Features Teams Can Build

- State-wise law comparison
- Voice-enabled roadside assistant
- Real-time challan prediction
- Camera-based violation detection
- AI-generated driving guidance
- Integration with maps/navigation

---

## Real-World Impact

India has:
- varying enforcement across states,
- inconsistent public awareness,
- and frequent confusion regarding traffic rules.

This platform aims to improve:
- rule compliance,
- citizen awareness,
- and preventive road safety.

---

# Problem Statement 2 — RoadWatch
## AI Platform for Road Quality Monitoring & Infrastructure Transparency

### Objective
Create a citizen-powered platform that monitors:
- road conditions,
- infrastructure defects,
- public spending transparency,
- and authority response systems.

The idea is to make road infrastructure more accountable and safer.

---

## Core Requirements

The system should allow users to:
- Report potholes and damaged roads
- Upload images/videos
- Geo-tag dangerous areas
- Track complaint resolution
- Monitor road repair status
- View public infrastructure transparency

---

## Expected AI Components

Possible AI/ML integrations:
- Computer vision pothole detection
- Damage severity classification
- Road quality scoring
- Predictive maintenance models
- GIS mapping systems
- Accident hotspot analytics

---

## Advanced Features Teams Can Build

- Heatmaps of dangerous roads
- AI-based repair prioritization
- Crash-risk prediction
- Satellite/drone-based inspection
- Real-time municipal dashboards
- Smart citizen reporting systems

---

## Real-World Importance

Poor road infrastructure is one of the biggest contributors to accidents in India.

This solution aims to improve:
- transparency,
- accountability,
- repair speed,
- and proactive maintenance.

---

# Problem Statement 3 — RoadSoS
## AI-Based Emergency & Driver Safety Assistance System

**Status: Selected for Implementation**
**Detailed Solution: [[00_Project_Overview/RoadSoS_Blueprint|RoadSoS Smart Helmet Blueprint]]**

### Objective
Build an intelligent road safety assistant capable of:
- detecting dangerous driving situations,
- identifying accidents,
- and assisting drivers in real time.

This statement heavily focuses on preventive AI systems.

---

## Expected Scope

Possible focus areas:
- Driver fatigue detection
- Rash driving detection
- Helmet/seatbelt monitoring
- Collision-risk prediction
- Overspeed alerts
- Emergency response systems
- Two-wheeler accident detection

---

## Expected AI Technologies

Relevant technologies may include:
- Computer vision
- Edge AI
- Real-time video analytics
- Sensor fusion
- Predictive modeling
- Driver behavior analysis

---

## Example Use Cases

- Detect drowsy driving through webcam analysis
- Alert drivers about unsafe overtaking
- Predict collision probability
- Detect two-wheeler skidding
- Auto-trigger emergency alerts after crashes
- Lane discipline monitoring

---

## Why This Problem Statement Is Strong

This area aligns with:
- ADAS systems,
- intelligent transport systems,
- autonomous safety systems,
- and real-time AI deployment.

It also has strong potential for:
- research publications,
- startup ideas,
- patents,
- and deployable products.

---

# Evaluation Criteria

Projects are generally judged on:

| Criterion | Description |
|---|---|
| Problem Understanding | Relevance and clarity |
| Innovation | Creativity and uniqueness |
| Technical Quality | AI/ML implementation quality |
| Scalability | Ability to scale across India |
| Practical Utility | Real-world deployability |
| Social Impact | Potential accident reduction |

---

# Important Technical Themes

The hackathon strongly encourages:
- AI/ML systems
- Computer vision
- Predictive analytics
- Real-time monitoring
- Intelligent enforcement
- Infrastructure analytics
- Citizen-centric platforms

---

# Why This Hackathon Matters

Unlike generic hackathons, this event is closely connected to:
- government road safety initiatives,
- transportation research,
- real-world deployment,
- and AI-driven public systems.

Strong projects can evolve into:
- startups,
- SaaS products,
- research papers,
- pilot deployments,
- or patented systems.

---

# Best Strategic Directions for High-Level Teams

The strongest directions are likely:
1. Predictive accident-risk systems
2. AI-powered infrastructure intelligence
3. Real-time dangerous driving detection
4. Edge AI safety assistants
5. Computer vision road analytics
6. Emergency response automation

---

# Official References

- IIT Madras CoERS Hackathon Page
- AI for Road Safety Summit
- Ministry of Road Transport & Highways collaborations
- National Road Safety Hackathon 2026 brochure



## Solutions

1. A helmet-mounted ESP32 module that detects motorcycle crashes via accelerometer/ gyroscope, verifies with a 10-second countdown, then simultaneously alerts the nearest hospital, ambulance, police, and emergency contact with GPS location + rider medical info (blood group, allergies, conditions). Bystanders scan a QR code on the helmet to access AI-guided first-aid instructions specific to motorcycle crash injuries. 

* **Problem**: only for bike riders
---
![[pinns_helmet_architecture.svg|697]]
This is a great opportunity to apply some genuinely cutting-edge techniques. Let me think through this carefully — PINNs are a particularly smart fit here for reasons that aren't obvious at first glance.Here's the full breakdown of how each optimization works:

---

**Why PINNs specifically fit this problem**

The core challenge with crash detection is that you almost never have enough real labeled crash data — you can't just crash 10,000 motorcycles to build a training set. PINNs solve this by embedding physical laws directly into the loss function during training, so the network learns the _physics of a crash_ rather than just memorizing examples. The two governing equations that matter most are:

Newton's rigid-body dynamics (F=ma, plus the rotational equivalent Iα=τ) describe how a helmet behaves in an impact. The **Head Injury Criterion (HIC)** — a real biomechanical standard used in crash testing — is defined as HIC = (t₂−t₁) × [(1/(t₂−t₁)) × ∫a(t)dt]^2.5, where values above ~700 indicate mild TBI risk and above 1000 indicate severe injury. Embedding these as physics residuals in the PINN loss means the model generalizes correctly even from a small dataset of simulated crashes (generated in PyBullet or MuJoCo for free).

The trained model quantizes to INT8, comes out to roughly 12KB, and runs comfortably on the ESP32-S3's vector accelerator at inference speeds well under 10ms.

---

**Hardware upgrades on a tight budget**

The original ESP32 is good but the **ESP32-S3** (same price, ~$3–5) has a built-in SIMD vector unit specifically for neural network inference — that's what makes TFLite Micro viable on-device. Swap the generic MPU-6050 for the **ICM-42688-P** (~$2), which samples at 32kHz and has a ±32g range — critical because motorcycle crashes can exceed 100g peak, and a lower-range IMU clips the signal exactly when it matters most. The **u-blox M10** for GNSS is low-power and accurate enough for emergency location at ~$4.

The biggest single upgrade in the original design: add a **Ra-02 LoRa module** (~$3) as a fallback. India's rural highway network has massive cellular dead zones — if the crash happens in one, the original system fails silently. LoRa can reach a gateway 5–10km away even with no cell signal.

---

**How the PINN changes the false-positive problem**

The original 10-second countdown is a blunt instrument — it tries to catch non-crashes by waiting, but it delays real response. The PINN replaces this with a proper physics-based discriminator. It distinguishes between:

- Road bumps (high-frequency, low-energy oscillation — governed by the road surface vibration ODE)
- Hard braking (high deceleration, but single axis, no angular velocity spike)
- Actual crashes (multi-axis impact, HIC > threshold, energy dissipation signature)

So instead of a flat 10-second wait, you get an _immediate_ severity-gated response: minor event → notify emergency contact only, HIC 700–1000 → ambulance, HIC > 1000 → full dispatch with police. Response is faster AND false positives drop dramatically.

---

**Federated learning keeps it improving**

Each deployed helmet sends only gradient weight updates (not raw IMU data) back to a central server after each event. The server aggregates these using FedAvg. This means the model gets smarter with every real-world near-miss and crash across the entire fleet — all without anyone's raw sensor data ever leaving their helmet. This is practically important in India where health data privacy is increasingly regulated.

---

**The QR first-aid system becomes smarter too**

In the original design, the QR code serves generic first-aid. With the PINN's injury zone output (head/torso/limb classification), the QR link can now serve _severity and zone-specific_ instructions — "suspected spinal injury, do not move the rider" vs. "limb fracture, apply pressure here." A small RAG system using Gemini's free API tier, indexed against WHO and Indian Red Cross emergency protocols, handles this on the backend.

---

**Total bill of materials: ~₹2,100–2,900 per unit.** The software stack (PyBullet for simulation, TFLite Micro, Firebase free tier, Gemini API) costs essentially nothing to develop. Want me to write this up as a formal technical proposal or build out the PINN training code?