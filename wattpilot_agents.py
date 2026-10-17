"""WattPilot's agent workflow.

Deterministic calculator (run_wattpilot) + optional agentic LLM layer
(run_agentic_wattpilot) that calls the calculator as a tool.

All numbers come from Python. The LLM only decides *which* plans to try
and writes reasoning. If no API key is given, the deterministic default
plan is used — the app always works.
"""
import json
import re
import requests
import pandas as pd

CRITICALITY = {"High": 3, "Medium": 2, "Low": 1}


# =====================================================================
# Deterministic core (logic unchanged)
# =====================================================================
def _clean_appliances(df):
    required = ["Appliance", "Power (kW)", "Hours/day", "Flexible hours", "Business critical"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))
    data = df[required].copy()
    data["Appliance"] = data["Appliance"].fillna("").astype(str).str.strip()
    data["Power (kW)"] = pd.to_numeric(data["Power (kW)"], errors="raise").clip(lower=0)
    data["Hours/day"] = pd.to_numeric(data["Hours/day"], errors="raise").clip(lower=0, upper=24)
    data["Flexible hours"] = pd.to_numeric(data["Flexible hours"], errors="raise").clip(lower=0, upper=24)
    data["Flexible hours"] = data[["Flexible hours", "Hours/day"]].min(axis=1)
    data["Business critical"] = data["Business critical"].fillna("Medium")
    data.loc[~data["Business critical"].isin(CRITICALITY), "Business critical"] = "Medium"
    if (data["Appliance"] == "").any():
        raise ValueError("Every appliance needs a name.")
    return data


def run_wattpilot(edited_df, tariff, business_type, business_name, open_hour, close_hour,
                  target_saving, max_shift, avoid_peak, scenario):
    data = _clean_appliances(edited_df)
    tariff = float(tariff)
    adjusted_tariff = tariff * 1.15 if scenario == "Electricity tariff increases by 15%" else tariff
    adjusted_close = max(open_hour + 1, close_hour - 2) if scenario == "Business closes 2 hours earlier" else close_hour

    agents = [{
        "name": "1. Intake Agent",
        "status": "Complete",
        "finding": f"Reviewed {len(data)} appliances for {business_name} ({business_type}). "
                   f"Operating window is {open_hour}:00–{adjusted_close}:00.",
        "action": "Normalize power, usage hours, flexibility, and criticality before optimizing."
    }]

    data["Current energy (kWh/day)"] = data["Power (kW)"] * data["Hours/day"]
    data["Current cost (PKR/day)"] = data["Current energy (kWh/day)"] * adjusted_tariff
    total_kwh = float(data["Current energy (kWh/day)"].sum())
    before_cost = float(data["Current cost (PKR/day)"].sum())
    agents.append({
        "name": "2. Energy Analyst Agent",
        "status": "Complete",
        "finding": f"Estimated usage is {total_kwh:.1f} kWh/day and energy cost is PKR {before_cost:,.0f}/day, "
                   "based on the values entered.",
        "action": "Rank flexible usage by potential energy impact while keeping essential appliances protected."
    })

    data["Allowed flexible hours"] = data["Flexible hours"].clip(upper=float(max_shift))
    if scenario == "One flexible appliance becomes unavailable":
        candidates = data.index[data["Allowed flexible hours"] > 0].tolist()
        if candidates:
            idx = sorted(candidates, key=lambda i: (CRITICALITY.get(data.loc[i, "Business critical"], 2),
                                                   -data.loc[i, "Allowed flexible hours"]))[0]
            data.loc[idx, "Allowed flexible hours"] = 0
            unavailable_name = data.loc[idx, "Appliance"]
        else:
            unavailable_name = "none (no flexible appliance)"
    else:
        unavailable_name = None

    data["Planned shifted hours"] = 0.0
    for idx, row in data.iterrows():
        flex = float(row["Allowed flexible hours"])
        if row["Business critical"] == "High":
            planned = 0.0
        elif row["Business critical"] == "Medium":
            planned = flex * 0.5
        else:
            planned = flex
        data.loc[idx, "Planned shifted hours"] = planned if avoid_peak else 0.0

    data["Estimated energy saving (kWh/day)"] = (
        data["Power (kW)"] * data["Planned shifted hours"] * 0.15
    )
    data["Estimated cost saving (PKR/day)"] = data["Estimated energy saving (kWh/day)"] * adjusted_tariff
    kwh_saved = float(data["Estimated energy saving (kWh/day)"].sum())
    daily_saving = float(data["Estimated cost saving (PKR/day)"].sum())
    after_cost = max(0.0, before_cost - daily_saving)
    monthly_saving = daily_saving * 30
    agents.append({
        "name": "3. Schedule Optimization Agent",
        "status": "Complete",
        "finding": f"Found {float(data['Planned shifted hours'].sum()):.1f} hours/day of candidate flexible work. "
                   f"The prototype estimates up to {kwh_saved:.2f} kWh/day of efficiency-related reduction; "
                   "schedule changes alone do not guarantee energy savings.",
        "action": "Prioritize flexible, lower-criticality loads and protect high-criticality appliances."
    })

    cautions = [
        "Savings are illustrative estimates based on user-entered values, not guaranteed results.",
        "Moving an appliance to another hour changes timing, not necessarily total kWh. The model assumes a modest 15% efficiency opportunity only on planned flexible hours.",
        "Refrigeration and other high-criticality equipment are protected from schedule changes.",
        "Actual bills may include taxes, fixed charges, fuel adjustments, and time-of-use rates not represented by one flat tariff."
    ]
    if scenario == "Business closes 2 hours earlier":
        cautions.append("Closing earlier may affect sales or production. This prototype does not estimate lost revenue.")
    if scenario == "One flexible appliance becomes unavailable":
        cautions.append(f"Scenario applied: {unavailable_name} was treated as unavailable for flexible scheduling.")
    if scenario == "Electricity tariff increases by 15%":
        cautions.append("The tariff scenario increases the entered per-unit rate by 15% for this analysis.")
    achieved_pct = (daily_saving / before_cost * 100) if before_cost > 0 else 0.0
    if achieved_pct < float(target_saving):
        cautions.append(f"Your requested savings target was {target_saving}%; this illustrative model estimates {achieved_pct:.1f}%, so the target is not met.")
    else:
        cautions.append(f"Your requested savings target was {target_saving}%; the illustrative estimate is {achieved_pct:.1f}%. This is not a guarantee.")
    agents.append({
        "name": "4. Business Impact Agent",
        "status": "Complete",
        "finding": "Checked the plan against appliance criticality and highlighted operational trade-offs.",
        "action": "Keep critical loads running and review any operational change with the business owner."
    })

    agents.append({
        "name": "5. Replanning Agent",
        "status": "Complete",
        "finding": f"Scenario selected: {scenario}. The plan and cost estimate were recalculated using the updated assumption.",
        "action": "Change the scenario and run the workflow again to compare how recommendations respond."
    })

    data["Optimized energy estimate (kWh/day)"] = (data["Current energy (kWh/day)"] -
                                                       data["Estimated energy saving (kWh/day)"]).clip(lower=0)
    data["Optimized cost estimate (PKR/day)"] = data["Optimized energy estimate (kWh/day)"] * adjusted_tariff
    plan = data[[
        "Appliance", "Business critical", "Current energy (kWh/day)", "Current cost (PKR/day)",
        "Allowed flexible hours", "Planned shifted hours", "Estimated energy saving (kWh/day)",
        "Estimated cost saving (PKR/day)", "Optimized cost estimate (PKR/day)"
    ]].copy()
    plan = plan.round(2)
    plan.columns = [
        "Appliance", "Criticality", "Current kWh/day", "Current cost/day (PKR)",
        "Flexible hours allowed", "Suggested shift hours", "Estimated saving (kWh/day)",
        "Estimated saving/day (PKR)", "Optimized cost/day (PKR)"
    ]

    agents.append({
        "name": "Workflow Summary",
        "status": "Ready for review",
        "finding": f"Estimated daily savings: PKR {daily_saving:,.0f}; estimated 30-day savings: PKR {monthly_saving:,.0f}.",
        "action": "Review the plan, adjust the inputs, and compare scenarios before making real operational changes."
    })
    return {
        "daily_cost_before": before_cost,
        "daily_cost_after": after_cost,
        "daily_saving": daily_saving,
        "monthly_saving": monthly_saving,
        "kwh_saved": kwh_saved,
        "plan": plan,
        "agents": agents,
        "cautions": cautions,
        "tariff_used": adjusted_tariff,
        "target_saving_requested": target_saving,
    }


# =====================================================================
# Gemini REST helpers
# =====================================================================
def ask_gemini(api_key, result, business_name, business_type, language="english"):
    """Optional Gemini explanation; local fallback if unavailable."""
    if not api_key:
        return ("No Gemini key was provided, so this explanation uses the local workflow results. "
                f"For {business_name}, the estimate is PKR {result['daily_saving']:,.0f}/day "
                f"(about PKR {result['monthly_saving']:,.0f} over 30 days). Treat this as a scenario estimate, "
                "not a guaranteed bill reduction. Confirm appliance requirements and your real tariff.")
    lang_hint = "Respond in Urdu (اردو)." if language == "urdu" else "Respond in English."
    prompt = (
        "You are WattPilot, an energy planning assistant for small businesses in Pakistan. "
        "Explain the following prototype results in simple language. Do not invent facts or guarantee savings. "
        "Mention assumptions and one practical next step. Keep it under 140 words. " + lang_hint + "\n"
        f"Business: {business_name} ({business_type})\n"
        f"Daily cost before: PKR {result['daily_cost_before']:.2f}\n"
        f"Daily cost after estimate: PKR {result['daily_cost_after']:.2f}\n"
        f"Estimated daily saving: PKR {result['daily_saving']:.2f}\n"
        f"Estimated monthly saving: PKR {result['monthly_saving']:.2f}\n"
        f"Estimated kWh saved per day: {result['kwh_saved']:.2f}\n"
        f"Assumptions: { '; '.join(result['cautions']) }"
    )
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.3, "maxOutputTokens": 400}},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return ("Gemini explanation could not be generated, so here is the local result: "
                f"estimated savings are PKR {result['daily_saving']:,.0f}/day. "
                "Check your API key/model access and try again. No savings are guaranteed.")


# =====================================================================
# NEW: Agentic layer (tool-calling)
# =====================================================================
def _gemini_chat(api_key, messages, tools=None, temperature=0.3, max_tokens=800):
    """Thin wrapper around Gemini generateContent with optional function calling."""
    body = {
        "contents": messages,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if tools:
        body["tools"] = [{"functionDeclarations": tools}]
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
        params={"key": api_key},
        json=body,
        timeout=45,
    )
    r.raise_for_status()
    return r.json()


WATTPILOT_TOOLS = [
    {
        "name": "run_plan",
        "description": (
            "Run WattPilot's deterministic energy calculator on the current appliances "
            "with specific settings. Returns exact daily/monthly savings, cost before/after, "
            "and cautions. You MUST call this to obtain any numbers. Never compute costs yourself."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "target_saving": {"type": "NUMBER", "description": "Target savings percentage, 0-50."},
                "max_shift": {"type": "NUMBER", "description": "Max shiftable hours per appliance, 0-8."},
                "avoid_peak": {"type": "BOOLEAN", "description": "Prefer moving flexible work away from peak."},
                "scenario": {
                    "type": "STRING",
                    "enum": [
                        "No change",
                        "Business closes 2 hours earlier",
                        "Electricity tariff increases by 15%",
                        "One flexible appliance becomes unavailable",
                    ],
                },
            },
            "required": ["target_saving", "max_shift", "avoid_peak", "scenario"],
        },
    },
]


def parse_business_description(api_key, free_text, language="english"):
    """Turn free-text (Urdu or English) into an appliance DataFrame. Returns None on failure."""
    if not api_key or not free_text or not free_text.strip():
        return None
    lang_hint = "Keep appliance names in the same language as the description." if language == "urdu" else ""
    prompt = (
        "Extract the appliances from this business owner's description. "
        "For each appliance estimate power in kW, hours/day, flexible hours, and criticality "
        "(High/Medium/Low). If unknown, use reasonable defaults. " + lang_hint + "\n\n"
        f"Description: {free_text}\n\n"
        "Return ONLY valid JSON with this exact shape:\n"
        '{"appliances":[{"Appliance":"...","Power (kW)":0.0,"Hours/day":0.0,'
        '"Flexible hours":0.0,"Business critical":"High|Medium|Low"}]}'
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",
        },
    }
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
            params={"key": api_key},
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        obj = json.loads(txt)
        rows = obj.get("appliances", [])
        if not rows:
            return None
        df = pd.DataFrame(rows)
        for c in ["Appliance", "Power (kW)", "Hours/day", "Flexible hours", "Business critical"]:
            if c not in df.columns:
                df[c] = 0
        df["Power (kW)"] = pd.to_numeric(df["Power (kW)"], errors="coerce").fillna(0.5)
        df["Hours/day"] = pd.to_numeric(df["Hours/day"], errors="coerce").fillna(2).clip(0, 24)
        df["Flexible hours"] = pd.to_numeric(df["Flexible hours"], errors="coerce").fillna(0).clip(0, 24)
        df["Business critical"] = df["Business critical"].where(
            df["Business critical"].isin(["High", "Medium", "Low"]), "Medium"
        )
        return df[["Appliance", "Power (kW)", "Hours/day", "Flexible hours", "Business critical"]]
    except Exception:
        return None


def run_agentic_wattpilot(api_key, edited_df, tariff, business_type, business_name,
                          open_hour, close_hour, user_goal="", language="english",
                          max_steps=4):
    """LLM orchestrator: decides settings, calls run_plan, compares, returns best plan + trace."""
    if not api_key:
        result = run_wattpilot(
            edited_df, tariff, business_type, business_name, open_hour, close_hour,
            target_saving=15, max_shift=2, avoid_peak=True, scenario="No change",
        )
        result["agent_trace"] = ["No API key — using deterministic default plan."]
        result["chosen_by_llm"] = False
        return result

    lang_hint = "Respond in Urdu (اردو)." if language == "urdu" else "Respond in English."
    system_prompt = (
        "You are WattPilot, an energy-planning agent for small businesses in Pakistan. "
        "You do NOT calculate numbers yourself. To obtain any number you MUST call run_plan. "
        "Your job: propose 1-3 sensible settings (vary max_shift, avoid_peak, or scenario), "
        "call run_plan for each, compare the returned daily_saving values, and pick the best "
        "plan for the owner's goal. Never claim savings that run_plan did not return. "
        + lang_hint
    )

    messages = [{
        "role": "user",
        "parts": [{"text": (
            f"{system_prompt}\n\n"
            f"Business: {business_name} ({business_type}).\n"
            f"Owner's goal (free text): {user_goal or 'reduce bills safely'}.\n"
            f"Tariff: PKR {tariff}/kWh. Open {open_hour}:00, close {close_hour}:00.\n"
            f"Appliances:\n{edited_df.to_string(index=False)}\n\n"
            "Try up to 3 candidate plans by calling run_plan with different settings, "
            "then state which plan you recommend and why (mention the daily saving)."
        )}],
    }]

    trace = []
    candidates = []

    for _ in range(max_steps):
        try:
            data = _gemini_chat(api_key, messages, tools=WATTPILOT_TOOLS)
        except Exception as exc:
            trace.append(f"⚠️ LLM call failed: {exc}")
            break

        cand = data.get("candidates", [{}])[0]
        parts = cand.get("content", {}).get("parts", [])
        messages.append({"role": "model", "parts": parts})

        fn_calls = [p["functionCall"] for p in parts if "functionCall" in p]
        text_parts = [p["text"] for p in parts if "text" in p]

        if text_parts:
            trace.append("🧠 " + " ".join(text_parts).strip())

        if not fn_calls:
            break

        tool_responses = []
        for fc in fn_calls:
            name = fc.get("name")
            args = fc.get("args", {}) or {}
            if name != "run_plan":
                tool_responses.append({
                    "functionResponse": {"name": name, "response": {"error": "unknown tool"}}
                })
                continue

            try:
                res = run_wattpilot(
                    edited_df=edited_df,
                    tariff=tariff,
                    business_type=business_type,
                    business_name=business_name,
                    open_hour=open_hour,
                    close_hour=close_hour,
                    target_saving=float(args.get("target_saving", 15)),
                    max_shift=float(args.get("max_shift", 2)),
                    avoid_peak=bool(args.get("avoid_peak", True)),
                    scenario=args.get("scenario", "No change"),
                )
                candidates.append(res)
                trace.append(
                    f"🛠 run_plan(target_saving={args.get('target_saving')}, "
                    f"max_shift={args.get('max_shift')}, "
                    f"avoid_peak={args.get('avoid_peak')}, "
                    f"scenario={args.get('scenario')!r}) → "
                    f"PKR {res['daily_saving']:,.0f}/day saved"
                )
                tool_responses.append({
                    "functionResponse": {
                        "name": "run_plan",
                        "response": {
                            "daily_saving": res["daily_saving"],
                            "monthly_saving": res["monthly_saving"],
                            "kwh_saved": res["kwh_saved"],
                            "daily_cost_before": res["daily_cost_before"],
                            "daily_cost_after": res["daily_cost_after"],
                            "cautions": res["cautions"][:2],
                        },
                    }
                })
            except Exception as exc:
                trace.append(f"⚠️ run_plan error: {exc}")
                tool_responses.append({
                    "functionResponse": {"name": "run_plan", "response": {"error": str(exc)}}
                })

        messages.append({"role": "user", "parts": tool_responses})

    if candidates:
        chosen = max(candidates, key=lambda r: r["daily_saving"])
    else:
        chosen = run_wattpilot(
            edited_df, tariff, business_type, business_name, open_hour, close_hour,
            target_saving=15, max_shift=2, avoid_peak=True, scenario="No change",
        )
        trace.append("⚠️ No successful tool call — fell back to default plan.")

    chosen["agent_trace"] = trace
    chosen["chosen_by_llm"] = True
    return chosen