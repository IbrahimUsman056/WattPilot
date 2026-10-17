# WattPilot ⚡
**Agentic AI for smarter energy decisions for small businesses in Pakistan**

WattPilot is a hackathon prototype that helps a small business enter appliance usage and an electricity rate, then get an **explainable, constraint-aware energy plan**. It combines a **deterministic calculator** with an **agentic AI layer** that plans, compares candidate strategies, and writes reasoning — so savings are auditable, never hallucinated.

The core app works **without an API key**. With a Gemini API key, it unlocks an agentic mode where the LLM orchestrates plans and can read a shop owner's description in **Urdu or English** to build the appliance table automatically.

---

## 🎯 Problem

Small businesses in Pakistan face brutal commercial electricity rates (often **PKR 60–80/kWh** with taxes and fixed charges), but they have no decision-support tool that:
- Turns their bill and appliance list into **practical actions**
- Explains **why** a plan protects certain appliances
- Works in **Urdu** for low-literacy owners
- Is **transparent** about what it does and doesn't model

Generic LLM chatbots give vague advice without grounded numbers. Enterprise energy tools are too expensive and complex for a bakery or tailor shop. WattPilot sits in the middle: **cheap, explainable, grounded in the owner's own numbers.**

---

## 💡 Solution

WattPilot is a **hybrid agentic system** with two layers:

### 1. Deterministic engine (`run_wattpilot`)
A transparent Python pipeline that:
1. **Intake Agent** — validates appliance details and operating hours
2. **Energy Analyst Agent** — calculates daily kWh and estimated energy cost
3. **Schedule Optimization Agent** — prioritizes flexible, lower-criticality appliance use
4. **Business Impact Agent** — flags operational trade-offs and protects high-criticality appliances
5. **Replanning Agent** — reruns the scenario after a tariff, closing-time, or appliance-availability change

All math is explicit Python. Nothing is invented by the LLM.

### 2. Agentic LLM layer (`run_agentic_wattpilot`, optional)
When a Gemini API key is provided, WattPilot adds:
- **Tool-calling orchestration** — the LLM decides *which* settings to try (e.g. *"try max_shift=2 then max_shift=4"*), calls `run_plan` as a tool, sees the **exact numbers** returned, and picks the best plan.
- **Free-text intake** — a shop owner can type *"میں ایک بیکری چلاتا ہوں جس میں ایک بڑا اوون، فریج، آٹا مشین اور کچھ پنکھے ہیں"* and the LLM extracts the appliance table.
- **Reasoning trace** — every tool call and every decision is shown to the user in a *"See how the AI reasoned"* panel. No black box.
- **Language-aware explanation** — the LLM writes its summary in Urdu or English depending on UI language.

The LLM **never does arithmetic**. It reasons *about* the numbers produced by the deterministic engine.

---

## ⚠️ Important modelling limitation

Moving usage to another time does **not automatically reduce electricity consumption**. This prototype uses an explicitly labelled, **illustrative 15% efficiency opportunity** on selected flexible hours to demonstrate scenario planning. It is **not** a verified prediction of savings, does **not** read smart meters, and does **not** model:

- All taxes, fixed charges, or fuel adjustments
- Time-of-use tariff schedules
- Production output or lost revenue
- Appliance-specific measured efficiency benchmarks

Do not present the estimates as guaranteed savings. All figures are scenario estimates, clearly labelled in the UI.

---

## ✨ Features

### Core
- Editable appliance table (power, hours, flexibility, criticality)
- User-entered PKR/kWh rate
- Appliance criticality and flexibility constraints
- Current vs. optimized estimate + monthly projection
- Scenario changes and re-planning (tariff +15%, earlier close, appliance unavailable)
- CSV export
- Transparent caveats and explainable agent steps

### Agentic (with Gemini API key)
- 🧠 **Tool-calling orchestrator** — the LLM proposes 1–3 plans, calls `run_plan`, compares results, and picks the best
- 📝 **Free-text intake** — describe your shop in **Urdu or English**, and the AI extracts the appliance table
- 🔍 **Reasoning trace** — a UI panel showing every tool call and the LLM's own reasoning
- 🗣️ **Language-aware AI explanation** — Gemini responds in Urdu or English

### Interface
- 🌐 **Bilingual UI** (English / اردو) with full RTL support and Nastaliq font
- 🎨 Custom-styled dashboard with metric cards, section pills, and gradient hero
- 📱 Responsive layout (mobile-friendly)
- 🔒 No API key required — the app gracefully falls back to deterministic mode

---

## 🛠 Tech stack

- **Python 3.10+**
- **Streamlit** — UI
- **Pandas** — data handling
- **Requests** — Gemini REST calls
- **Gemini API** — `gemini-2.5-flash` endpoint, optional (function calling + JSON mode)

No SDKs — Gemini is called directly via REST to keep dependencies minimal.

---

## 🚀 Run locally

1. Install Python 3.10 or newer.

2. Clone or open this folder in a terminal.

3. (Recommended) Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # macOS/Linux
   .venv\Scripts\activate       # Windows