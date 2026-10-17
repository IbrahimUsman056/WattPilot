# WattPilot ⚡

**Agentic AI for smarter energy decisions — built for Pakistan's small businesses.**

WattPilot is a hackathon prototype that helps a small business owner enter their appliances and electricity rate, then get a clear, explainable energy plan with estimated savings. It combines a **deterministic Python calculator** with an **optional Gemini AI agent** that reasons about strategies and explains results in **English or Urdu**.

---

## Problem

Small businesses in Pakistan — bakeries, tailors, grocers, restaurants — face some of the highest commercial electricity rates in the world (often **PKR 60–80 per kWh** once taxes and fixed charges are added). Yet most owners have **no practical tool** that:

- Turns their bill and appliance list into **actionable decisions**
- Explains **why** a plan protects some appliances and shifts others
- Works in **Urdu**, which many owners prefer
- Is **honest** about what it does and doesn't model

Generic AI chatbots give vague advice with hallucinated numbers. Enterprise energy tools are too expensive and complex for a small shop. WattPilot fills that gap: **cheap, explainable, grounded in the owner's own numbers.**

---

## Solution

WattPilot is a **hybrid agentic system** with two layers working together.

### 1. Deterministic Engine (Python)

A transparent five-stage pipeline:

1. **Intake Agent** — validates appliance details and operating hours.
2. **Energy Analyst Agent** — calculates daily kWh and estimated cost.
3. **Schedule Optimization Agent** — prioritises flexible, lower-criticality appliance use.
4. **Business Impact Agent** — flags trade-offs and protects high-criticality appliances (e.g., refrigeration).
5. **Replanning Agent** — reruns the plan after a scenario change (tariff +15%, earlier closing, appliance unavailable).

### 2. Optional Gemini AI Agent

With an API key, the LLM:

- **Orchestrates** which scenarios to try by calling the calculator as a tool.
- **Reads free-text descriptions** in Urdu or English to build the appliance table.
- **Compares plans** and writes a plain-language recommendation.
- Shows a **visible reasoning trace** so users can audit every decision.

All numbers come from Python. The LLM only reasons *about* those numbers — it never does arithmetic.

---

## Features

- 📝 **Free-text intake** — describe your shop in Urdu or English, and AI builds the appliance list.
- 🔢 **Manual appliance editor** — enter power (kW), daily hours, flexible hours, and criticality.
- ⚡ **PKR/kWh tariff input** — works with any commercial rate.
- 🔀 **Scenario testing** — tariff +15%, business closes earlier, or an appliance becomes unavailable.
- 🧠 **AI reasoning trace** — every tool call and decision is visible to the user.
- 🌐 **Bilingual UI** — full English / اردو support with proper RTL rendering.
- 📊 **Dashboard report** — current vs. optimised cost, monthly savings, and energy saved.
- 📥 **CSV export** — download the plan for records or verification.
- 🔒 **Works without an API key** — automatically falls back to the deterministic plan.

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **Pandas** — data handling and appliance table
- **Requests** — direct REST calls to the Gemini API (no SDK required)
- **Google Gemini API** — optional, for the agentic layer

---

## AI / API Usage

### How AI Is Used

| Component | Model | Role |
|---|---|---|
| **Reasoning agent** | `gemini-2.5-flash-lite` or a currently active Gemini Flash model | Decides which plans to try, calls the calculator, compares results, and writes recommendations |
| **Free-text intake** | Same model, with JSON response mode | Extracts appliance names, power, hours, and criticality from Urdu/English descriptions |
| **Explanation generator** | Same model | Produces a short, plain-language summary of the plan in the UI language |

### Why the LLM Does NOT Do the Math

Cost tools cannot afford to hallucinate. WattPilot uses a **constrained-agent design**:

- The LLM calls `run_wattpilot()` as a tool — a plain Python function.
- It receives back **exact numbers**, including daily savings, monthly savings, and costs before and after optimisation.
- It compares those results and picks the best plan.
- It never invents a number; it only reasons about the returned results.

This follows a common tool-using AI architecture: **calculations happen in Python, while the model reasons about the results.**

### API Key Handling

- The Gemini API key can be entered at runtime in the sidebar or provided through the `GEMINI_API_KEY` environment variable.
- **No API keys should be committed to this repository.**
- The app runs without a key in deterministic mode.
- When deployed, keys should be provided as platform secrets, never hardcoded in source code.

### Known Limitation

The prototype uses an **explicitly labelled, illustrative 15% efficiency assumption** on flexible hours to demonstrate scenario planning.

This is **not a verified savings prediction**. Moving an appliance to another hour does not automatically reduce its energy consumption. Real savings depend on time-of-use tariffs, appliance-specific efficiency, and operational constraints. These limitations are listed in the app's cautions section.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/IbrahimUsman056/WattPilot.git
cd WattPilot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` does not exist yet, install the dependencies manually:

```bash
pip install streamlit pandas requests
```

### 3. Configure Your Gemini API Key (Optional)

Never commit a real API key to the repository.

**Option A: Environment variable (recommended)**

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your-key-here"
```

macOS / Linux:

```bash
export GEMINI_API_KEY="your-key-here"
```

**Option B: Enter the key at runtime**

Open the application and enter your Gemini API key in the sidebar, if that option is enabled in the app.

If you skip this step, WattPilot will run in deterministic mode. The calculator, planning features, and other implemented functionality will remain available, while AI-dependent features will be unavailable.

### 4. Run the Application

```bash
streamlit run app.py
```

Open the following URL in your browser:

http://localhost:8501

---

## Screenshots

1. **Home screen (English)** — hero section, intake mode, and appliance editor.
<img width="959" height="539" alt="image" src="https://github.com/user-attachments/assets/e938c503-f8c2-40aa-a819-e6d831fa164e" />

2. **Home screen (اردو)** — full right-to-left layout.
<img width="959" height="440" alt="image" src="https://github.com/user-attachments/assets/1677acf5-069f-4450-a9c4-e2f79e37a9d5" />

3. **AI reasoning trace** — the "🧠 See how the AI reasoned" panel showing tool calls.
<img width="735" height="435" alt="image" src="https://github.com/user-attachments/assets/92ec2359-d936-4b18-8168-01f26852f513" />

4. **Report dashboard** — metric cards, plan table, and chart.
<img width="876" height="435" alt="image" src="https://github.com/user-attachments/assets/7f44d5f7-2163-46a8-b2ed-bb0a9afba1e1" />

5. **Free-text intake** — an Urdu description being parsed into an appliance table.
<img width="667" height="413" alt="image" src="https://github.com/user-attachments/assets/aedda8bf-61a2-49a3-adb4-4de8cc0ca921" />


---

## Team Contributions

- **Ibrahim Usman** — Architecture, deterministic engine, Streamlit UI, Bilingual layout, Gemini integration, agentic orchestration, Prompt design, Testing, user research, Pitch deck, Documentation, deployment, and demo preparation.

---

## Deployment

The app can be deployed using Streamlit Community Cloud.

**Live demo:** https://wattpilot-nylpaihackathon.streamlit.app/

### Deployment Steps

1. Visit [Streamlit Community Cloud](https://share.streamlit.io/).
2. Connect this GitHub repository.
3. Set `app.py` as the main application file.
4. Add `GEMINI_API_KEY` under the app's Secrets settings if AI features are required.
5. Deploy the application.

Without the API key, the app should operate in deterministic mode, provided the application is configured to support that fallback.

---

## Known Limitations / Roadmap

### Current Limitations

- **Single flat tariff:** No time-of-use tariff modelling.
- **Illustrative 15% efficiency assumption:** Savings are not measured or verified.
- **No smart meter integration:** Electricity usage is not automatically collected from smart meters.
- **No historical bill import:** Users must provide their own inputs.
- **Optional AI dependency:** Gemini-powered features require a valid API key and an available supported model.

### Future Roadmap

- ⚡ **Time-of-use tariffs** — support real peak/off-peak rates, which can be especially useful in Pakistan.
- 📊 **Measured usage** — integrate smart plugs or manual meter readings.
- 🧊 **Verified appliance efficiency benchmarks** — use benchmarks sourced from published studies.
- 🗣️ **Improved Urdu AI intake** — validate free-text parsing with real shop owners.
- 🔌 **Bill PDF import and utility account linking** — simplify data entry and support more accurate analysis.

---

## License & Acknowledgements

Built with:

- [Streamlit](https://streamlit.io/) — Apache License 2.0
- [Pandas](https://pandas.pydata.org/) — BSD 3-Clause License
- [Requests](https://requests.readthedocs.io/) — Apache License 2.0
- [Google Gemini API](https://ai.google.dev/) — subject to Google's terms
- [Noto Nastaliq Urdu](https://fonts.google.com/noto/specimen/Noto+Nastaliq+Urdu) — SIL Open Font License

---

**WattPilot ⚡ — Smarter energy decisions, grounded in your numbers.**
