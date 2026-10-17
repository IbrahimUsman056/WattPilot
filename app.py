import os
import re
import pandas as pd
import streamlit as st
from wattpilot_agents import (
    run_wattpilot,
    run_agentic_wattpilot,
    parse_business_description,
    ask_gemini,
)

st.set_page_config(page_title="WattPilot | Energy Agent", page_icon="⚡", layout="wide")

# =====================================================================
# LANGUAGE DICTIONARY (UI chrome)
# =====================================================================
LANG = {
    "English": {
        "lang_label": "Language",
        "hero_title": "⚡ WattPilot",
        "hero_sub": "Smart energy advisor for your small business — powered by AI agents.",
        "caption_note": "Estimate only — not an official bill or tariff quote.",
        "sidebar_setup": "🏪 Your Business",
        "business_type": "What type of business?",
        "business_name": "Business name",
        "tariff": "Electricity cost (PKR per unit)",
        "tariff_help": "Check your bill for the per-unit cost.",
        "open_hour": "Opening time",
        "close_hour": "Closing time",
        "close_warning": "Closing time must be later than opening time.",
        "ai_section": "🤖 AI & Agent Settings",
        "api_key": "Gemini API key",
        "api_caption": "With a key, WattPilot uses an AI agent that plans and reasons. Without it, uses the built-in deterministic plan.",
        "intake_title": "How would you like to start?",
        "intake_describe": "📝 Describe my business (AI reads it)",
        "intake_manual": "🔢 Fill the appliance table myself",
        "describe_prompt": "Describe your shop in one or two sentences (Urdu or English):",
        "describe_btn": "🤖 Understand my business",
        "describe_ok": "AI extracted your appliances. Review below 👇",
        "describe_fail": "Couldn't parse — fill the table manually below.",
        "appliances_title": "1 · Your Appliances",
        "appliances_help": "Enter each appliance, its power (kW), daily hours, and how many hours can be moved.",
        "goals_title": "2 · What Matters to You",
        "target_saving": "Target savings (%)",
        "max_shift": "Max shiftable hours per appliance",
        "avoid_peak": "Avoid peak hours",
        "scenario_title": "3 · Test a Scenario",
        "scenario_help": "See how the plan adapts to a change.",
        "scenario_label": "What changed?",
        "scenario_none": "No change",
        "scenario_close": "Business closes 2 hours earlier",
        "scenario_tariff": "Electricity price +15%",
        "scenario_unavailable": "One flexible appliance unavailable",
        "goal_label": "Your goal in your own words (optional):",
        "goal_placeholder": "e.g. Save as much as possible without touching my fridge",
        "run_btn": "⚡ Analyze & Optimize",
        "error_close": "Closing hour must be later than opening hour.",
        "error_empty": "Add at least one appliance.",
        "error_values": "Please check your appliance values:",
        "report_title": "WattPilot's Report",
        "metric_daily_before": "Current Daily Cost",
        "metric_daily_after": "Optimized Daily Cost",
        "metric_monthly": "Monthly Savings",
        "metric_energy": "Energy Saved",
        "trace_title": "🧠 See how the AI reasoned",
        "workflow_title": "Agent Workflow",
        "plan_title": "Recommended Plan",
        "chart_title": "Daily Cost Comparison",
        "chart_current": "Current",
        "chart_optimized": "Optimized",
        "impact_title": "Impact & Cautions",
        "ai_btn": "✨ Generate AI Explanation",
        "ai_result_title": "Plain-Language Explanation",
        "download_btn": "⬇️ Download Report (CSV)",
        "footer": "Prototype only. Verify safety and your actual tariff before making changes.",
        "action_label": "Action",
        "pk": "PKR",
        "kwh": "kWh/day",
    },
    "اردو": {
        "lang_label": "زبان",
        "hero_title": "⚡ واٹ پائلٹ",
        "hero_sub": "آپ کے چھوٹے کاروبار کے لیے اسمارٹ انرجی مشیر — AI ایجنٹس کی مدد سے۔",
        "caption_note": "صرف اندازہ — سرکاری بل یا ٹیرف نہیں۔",
        "sidebar_setup": "🏪 آپ کا کاروبار",
        "business_type": "کاروبار کی قسم؟",
        "business_name": "کاروبار کا نام",
        "tariff": "بجلی کی قیمت (روپے فی یونٹ)",
        "tariff_help": "بل سے فی یونٹ قیمت دیکھیں۔",
        "open_hour": "کھلنے کا وقت",
        "close_hour": "بند ہونے کا وقت",
        "close_warning": "بند ہونے کا وقت کھلنے کے بعد ہونا چاہیے۔",
        "ai_section": "🤖 AI اور ایجنٹ سیٹنگز",
        "api_key": "Gemini API key",
        "api_caption": "key کے ساتھ، واٹ پائلٹ ایک AI ایجنٹ استعمال کرتا ہے جو منصوبہ بناتا اور سوچتا ہے۔ key کے بغیر بلٹ اِن منصوبہ۔",
        "intake_title": "آپ کیسے شروع کرنا چاہیں گے؟",
        "intake_describe": "📝 اپنے کاروبار کی تفصیل لکھیں (AI پڑھے گا)",
        "intake_manual": "🔢 میں خود آلہ ٹیبل بھروں گا",
        "describe_prompt": "اپنی دکان کے بارے میں ایک دو جملے لکھیں (اردو یا انگریزی):",
        "describe_btn": "🤖 میرا کاروبار سمجھیں",
        "describe_ok": "AI نے آپ کے آلات نکال لیے۔ نیچے دیکھیں 👇",
        "describe_fail": "سمجھ نہیں سکا — نیچے ٹیبل خود بھریں۔",
        "appliances_title": "1 · آپ کے آلات",
        "appliances_help": "ہر آلے کی طاقت (kW)، روزانہ گھنٹے، اور منتقل ہو سکنے والے گھنٹے بتائیں۔",
        "goals_title": "2 · آپ کے لیے کیا اہم ہے",
        "target_saving": "بچت کا ہدف (%)",
        "max_shift": "فی آلہ زیادہ سے زیادہ منتقلی گھنٹے",
        "avoid_peak": "پیک اوقات سے بچیں",
        "scenario_title": "3 · منظرنامہ آزمائیں",
        "scenario_help": "دیکھیں کہ تبدیلی پر منصوبہ کیسے بدلتا ہے۔",
        "scenario_label": "کیا بدلا؟",
        "scenario_none": "کوئی تبدیلی نہیں",
        "scenario_close": "کاروبار 2 گھنٹے پہلے بند",
        "scenario_tariff": "بجلی کی قیمت +15%",
        "scenario_unavailable": "ایک لچکدار آلہ دستیاب نہیں",
        "goal_label": "اپنے الفاظ میں ہدف (اختیاری):",
        "goal_placeholder": "مثلاً: زیادہ سے زیادہ بچت کریں لیکن فریج نہ چھیڑیں",
        "run_btn": "⚡ تجزیہ اور بہتری",
        "error_close": "بند ہونے کا وقت کھلنے کے بعد ہونا چاہیے۔",
        "error_empty": "کم از کم ایک آلہ شامل کریں۔",
        "error_values": "آلات کی معلومات چیک کریں:",
        "report_title": "واٹ پائلٹ کی رپورٹ",
        "metric_daily_before": "موجودہ روزانہ لاگت",
        "metric_daily_after": "بہتر روزانہ لاگت",
        "metric_monthly": "ماہانہ بچت",
        "metric_energy": "بچت شدہ توانائی",
        "trace_title": "🧠 دیکھیں AI نے کیسے سوچا",
        "workflow_title": "ایجنٹ ورک فلو",
        "plan_title": "تجویز کردہ منصوبہ",
        "chart_title": "روزانہ لاگت کا موازنہ",
        "chart_current": "موجودہ",
        "chart_optimized": "بہتر",
        "impact_title": "اثرات اور احتیاطیں",
        "ai_btn": "✨ AI وضاحت حاصل کریں",
        "ai_result_title": "آسان زبان میں وضاحت",
        "download_btn": "⬇️ رپورٹ ڈاؤن لوڈ کریں",
        "footer": "صرف پروٹوٹائپ۔ تبدیلی سے پہلے حفاظت اور ٹیرف چیک کریں۔",
        "action_label": "اقدام",
        "pk": "روپے",
        "kwh": "کلوواٹ گھنٹہ/دن",
    }
}

# =====================================================================
# Display-only translation tables
# =====================================================================
BUSINESS_TYPES_EN = ["Bakery", "Small grocery store", "Restaurant", "Tailor shop", "Home business", "Other"]
BUSINESS_TYPES_UR = ["بیکری", "چھوٹا گروسری اسٹور", "ریستوران", "درزی کی دکان", "گھریلو کاروبار", "دیگر"]

APPLIANCE_COLS_EN = ["Appliance", "Power (kW)", "Hours/day", "Flexible hours", "Business critical"]
APPLIANCE_COLS_UR = ["آلہ", "طاقت (kW)", "گھنٹے/دن", "لچکدار گھنٹے", "اہمیت"]

CRIT_EN = ["High", "Medium", "Low"]
CRIT_UR = ["زیادہ", "درمیانہ", "کم"]

DEFAULT_APPLIANCE_NAMES_EN = ["Oven", "Refrigerator", "Dough mixer", "Lights and fans"]
DEFAULT_APPLIANCE_NAMES_UR = ["اوون", "فریج", "آٹا مشین", "لائٹس اور پنکھے"]

PLAN_COLS_UR = {
    "Appliance": "آلہ",
    "Criticality": "اہمیت",
    "Current kWh/day": "موجودہ kWh/دن",
    "Current cost/day (PKR)": "موجودہ لاگت/دن (روپے)",
    "Flexible hours allowed": "لچکدار گھنٹے",
    "Suggested shift hours": "تجویز کردہ منتقلی گھنٹے",
    "Estimated saving (kWh/day)": "تخمینی بچت (kWh/دن)",
    "Estimated saving/day (PKR)": "تخمینی بچت/دن (روپے)",
    "Optimized cost/day (PKR)": "بہتر لاگت/دن (روپے)",
}

AGENT_NAMES_UR = {
    "1. Intake Agent": "1. انٹیک ایجنٹ",
    "2. Energy Analyst Agent": "2. توانائی تجزیہ ایجنٹ",
    "3. Schedule Optimization Agent": "3. شیڈول بہتری ایجنٹ",
    "4. Business Impact Agent": "4. کاروباری اثرات ایجنٹ",
    "5. Replanning Agent": "5. دوبارہ منصوبہ بندی ایجنٹ",
    "Workflow Summary": "ورک فلو خلاصہ",
}
STATUS_UR = {
    "Complete": "مکمل",
    "Ready for review": "جائزے کے لیے تیار",
    "Done": "مکمل",
    "OK": "ٹھیک",
    "Warning": "انتباہ",
    "Active": "فعال",
}

# =====================================================================
# Runtime text translation (regex on top of agent output)
# =====================================================================
def tr_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    s = text

    s = re.sub(
        r"Reviewed (\d+) appliances for (.+?) \((.+?)\)\. Operating window is (\d+):00[–-](\d+):00\.",
        lambda m: f"{m.group(2)} ({m.group(3)}) کے لیے {m.group(1)} آلات کا جائزہ لیا۔ "
                  f"کام کا دورانیہ {m.group(4)}:00 سے {m.group(5)}:00 تک ہے۔",
        s,
    )
    s = s.replace("Normalize power, usage hours, flexibility, and criticality before optimizing.",
                  "بہتری سے پہلے طاقت، استعمال کے گھنٹے، لچک اور اہمیت معمول کے مطابق کریں۔")
    s = re.sub(
        r"Estimated usage is ([\d.,]+) kWh/day and energy cost is PKR ([\d.,]+)/day, based on the values entered\.",
        lambda m: f"اندازے کے مطابق استعمال {m.group(1)} kWh/دن ہے اور توانائی کی لاگت "
                  f"روپے {m.group(2)}/دن ہے — آپ کی دی گئی معلومات کی بنیاد پر۔",
        s,
    )
    s = s.replace("Rank flexible usage by potential energy impact while keeping essential appliances protected.",
                  "لچکدار استعمال کو ممکنہ توانائی کے اثر کے مطابق ترتیب دیں جبکہ اہم آلات محفوظ رکھیں۔")
    s = re.sub(
        r"Found ([\d.,]+) hours/day of candidate flexible work\. The prototype estimates up to ([\d.,]+) kWh/day of efficiency-related reduction; schedule changes alone do not guarantee energy savings\.",
        lambda m: f"روزانہ {m.group(1)} گھنٹے لچکدار کام کے امیدوار ملے۔ پروٹوٹائپ اندازہ لگاتا ہے کہ "
                  f"کارکردگی سے {m.group(2)} kWh/دن تک کمی ممکن ہے؛ صرف شیڈول تبدیل کرنا توانائی کی بچت کی ضمانت نہیں۔",
        s,
    )
    s = s.replace("Prioritize flexible, lower-criticality loads and protect high-criticality appliances.",
                  "لچکدار، کم اہمیت والے بوجھ کو ترجیح دیں اور زیادہ اہمیت والے آلات محفوظ رکھیں۔")
    s = s.replace("Checked the plan against appliance criticality and highlighted operational trade-offs.",
                  "منصوبے کو آلات کی اہمیت کے مطابق جانچا اور کاروباری trade-offs نمایاں کیے۔")
    s = s.replace("Keep critical loads running and review any operational change with the business owner.",
                  "اہم بوجھ جاری رکھیں اور کسی بھی تبدیلی کا کاروبار کے مالک کے ساتھ جائزہ لیں۔")
    s = re.sub(
        r"Scenario selected: (.+?)\. The plan and cost estimate were recalculated using the updated assumption\.",
        lambda m: f"منتخب منظرنامہ: {tr_scenario(m.group(1))}۔ منصوبہ اور لاگت کا اندازہ نئی مفروضے کے ساتھ دوبارہ شمار کیا گیا۔",
        s,
    )
    s = s.replace("Change the scenario and run the workflow again to compare how recommendations respond.",
                  "منظرنامہ تبدیل کریں اور ورک فلو دوبارہ چلائیں تاکہ تجاویز کا موازنہ ہو سکے۔")
    s = re.sub(
        r"Estimated daily savings: PKR ([\d.,]+); estimated 30-day savings: PKR ([\d.,]+)\.",
        lambda m: f"تخمینی روزانہ بچت: روپے {m.group(1)}؛ تخمینی 30 دن کی بچت: روپے {m.group(2)}۔",
        s,
    )
    s = s.replace("Review the plan, adjust the inputs, and compare scenarios before making real operational changes.",
                  "حقیقی تبدیلی سے پہلے منصوبہ دیکھیں، معلومات تبدیل کریں، اور منظرناموں کا موازنہ کریں۔")

    # Cautions
    s = s.replace("Savings are illustrative estimates based on user-entered values, not guaranteed results.",
                  "بچت صرف مثال کے طور پر اندازہ ہے — آپ کی دی گئی معلومات پر مبنی، ضمانت نہیں۔")
    s = s.replace("Moving an appliance to another hour changes timing, not necessarily total kWh. The model assumes a modest 15% efficiency opportunity only on planned flexible hours.",
                  "آلہ دوسرے وقت پر منتقل کرنے سے وقت بدلتا ہے، کل kWh ضروری نہیں۔ ماڈل صرف منصوبہ شدہ لچکدار گھنٹوں پر 15% کارکردگی کا معمولی امکان فرض کرتا ہے۔")
    s = s.replace("Refrigeration and other high-criticality equipment are protected from schedule changes.",
                  "ریفریجریشن اور دیگر زیادہ اہمیت والے آلات شیڈول تبدیلیوں سے محفوظ ہیں۔")
    s = s.replace("Actual bills may include taxes, fixed charges, fuel adjustments, and time-of-use rates not represented by one flat tariff.",
                  "اصل بلوں میں ٹیکس، فکسڈ چارجز، فیول ایڈجسٹمنٹ اور وقت کے مطابق ریٹ شامل ہو سکتے ہیں جو ایک فلیٹ ٹیرف میں شامل نہیں۔")
    s = s.replace("Closing earlier may affect sales or production. This prototype does not estimate lost revenue.",
                  "جلدی بند کرنا فروخت یا پیداوار کو متاثر کر سکتا ہے۔ یہ پروٹوٹائپ ضائع شدہ آمدنی کا اندازہ نہیں لگاتا۔")
    s = re.sub(
        r"Scenario applied: (.+?) was treated as unavailable for flexible scheduling\.",
        lambda m: f"منظرنامہ لاگو: {tr_appliance(m.group(1))} کو لچکدار شیڈولنگ کے لیے دستیاب نہیں سمجھا گیا۔",
        s,
    )
    s = s.replace("The tariff scenario increases the entered per-unit rate by 15% for this analysis.",
                  "ٹیرف منظرنامے میں اس تجزیے کے لیے درج فی یونٹ ریٹ 15% بڑھایا گیا ہے۔")
    s = re.sub(
        r"Your requested savings target was ([\d.]+)%; this illustrative model estimates ([\d.]+)%, so the target is not met\.",
        lambda m: f"آپ کا مطلوبہ بچت ہدف {m.group(1)}% تھا؛ یہ مثالی ماڈل {m.group(2)}% کا اندازہ لگاتا ہے، اس لیے ہدف پورا نہیں ہوا۔",
        s,
    )
    s = re.sub(
        r"Your requested savings target was ([\d.]+)%; the illustrative estimate is ([\d.]+)%\. This is not a guarantee\.",
        lambda m: f"آپ کا مطلوبہ بچت ہدف {m.group(1)}% تھا؛ مثالی اندازہ {m.group(2)}% ہے۔ یہ ضمانت نہیں۔",
        s,
    )
    return s


def tr_scenario(name: str) -> str:
    return {
        "No change": "کوئی تبدیلی نہیں",
        "Business closes 2 hours earlier": "کاروبار 2 گھنٹے پہلے بند",
        "Electricity tariff increases by 15%": "بجلی کی قیمت 15% بڑھ گئی",
        "One flexible appliance becomes unavailable": "ایک لچکدار آلہ دستیاب نہیں",
    }.get(name, name)


def tr_appliance(name: str) -> str:
    return {
        "Oven": "اوون", "Refrigerator": "فریج",
        "Dough mixer": "آٹا مشین", "Lights and fans": "لائٹس اور پنکھے",
    }.get(name, name)


def tr_agent(name: str) -> str:
    return AGENT_NAMES_UR.get(name, name)


def tr_status(name: str) -> str:
    return STATUS_UR.get(name, name)


def localize_plan(df):
    out = df.copy()
    if "Appliance" in out.columns:
        out["Appliance"] = out["Appliance"].astype(str).apply(tr_appliance)
    if "Criticality" in out.columns:
        out["Criticality"] = out["Criticality"].map(
            lambda v: {"High": "زیادہ", "Medium": "درمیانہ", "Low": "کم"}.get(v, v)
        )
    out = out.rename(columns=PLAN_COLS_UR)
    return out


# =====================================================================
# Theme CSS
# =====================================================================
st.markdown("""
<style>
:root{
  --ink:#111827; --muted:#6b7280; --line:#e5e7eb; --card:#ffffff;
  --r1:#ef4444; --r2:#f97316; --r3:#eab308; --r4:#22c55e; --r5:#06b6d4; --r6:#3b82f6; --r7:#8b5cf6; --r8:#ec4899;
  --rainbow:linear-gradient(90deg,#ef4444,#f97316,#eab308,#22c55e,#06b6d4,#3b82f6,#8b5cf6,#ec4899);
  --radius:18px;
  --shadow-sm:0 1px 2px rgba(17,24,39,.05),0 2px 6px rgba(17,24,39,.06);
  --shadow-md:0 12px 28px -10px rgba(99,102,241,.35);
}
@keyframes flow{0%{background-position:0% 50%}100%{background-position:200% 50%}}

.stApp{
  background:
    radial-gradient(900px 500px at 0% 0%,rgba(239,68,68,.07),transparent 60%),
    radial-gradient(900px 500px at 100% 0%,rgba(139,92,246,.09),transparent 60%),
    radial-gradient(900px 600px at 50% 100%,rgba(6,182,212,.08),transparent 60%),
    #fafbff;
}
.stApp::before{content:"";position:fixed;top:0;left:0;right:0;height:5px;z-index:9999;
  background:var(--rainbow);background-size:200% 100%;animation:flow 8s linear infinite;}
.block-container{padding-top:1.4rem;max-width:1180px;padding-bottom:3rem;}
section[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid var(--line);}
section[data-testid="stSidebar"]::before{content:"";display:block;height:4px;background:var(--rainbow);}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
html,body,[class*="css"]{color:var(--ink);
  font-family:"Inter","Noto Nastaliq Urdu","Segoe UI",system-ui,sans-serif;font-size:15px;}
h1,h2,h3{color:var(--ink);font-weight:800;letter-spacing:-.01em;}
h2{font-size:1.4rem!important;} h3{font-size:1.1rem!important;}

/* Hero */
.hero{position:relative;overflow:hidden;padding:2.3rem 2.4rem;border-radius:24px;margin-bottom:1rem;
  background:linear-gradient(135deg,#0b1020 0%,#151a3a 60%,#1e1b4b 100%);color:#fff;
  box-shadow:0 24px 50px -22px rgba(79,70,229,.6);}
.hero::before{content:"";position:absolute;inset:0;border-radius:24px;padding:2px;
  background:var(--rainbow);background-size:200% 100%;animation:flow 6s linear infinite;
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);
  -webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;}
.hero::after{content:"";position:absolute;right:-80px;top:-80px;width:320px;height:320px;border-radius:50%;
  background:conic-gradient(from 0deg,#ef4444,#f97316,#eab308,#22c55e,#06b6d4,#3b82f6,#8b5cf6,#ec4899,#ef4444);
  filter:blur(70px);opacity:.35;}
.hero h1{position:relative;z-index:1;font-size:2.7rem!important;margin:0;font-weight:900;
  background:var(--rainbow);background-size:200% 100%;animation:flow 6s linear infinite;
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;}
.hero p{position:relative;z-index:1;font-size:1.05rem;margin:.45rem 0 0 0;color:#c7d2fe;}

.note-banner{display:flex;align-items:center;gap:.55rem;background:#fff;color:#374151;
  border:1px solid var(--line);border-left:4px solid var(--r3);border-radius:12px;
  padding:.65rem .9rem;font-size:.86rem;margin-bottom:1.1rem;box-shadow:var(--shadow-sm);}

/* Section headers */
.sec{display:flex;align-items:center;gap:.65rem;margin:1.5rem 0 .6rem 0;}
.sec .num{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;font-size:.85rem;
  font-weight:800;color:#fff;background:var(--rainbow);background-size:200% 100%;
  animation:flow 7s linear infinite;box-shadow:var(--shadow-sm);}
.sec .title{font-size:1.1rem;font-weight:800;color:var(--ink);}

/* Metric cards */
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:.9rem 0 1.3rem 0;}
.metric{position:relative;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:1.1rem 1.15rem;box-shadow:var(--shadow-sm);overflow:hidden;transition:transform .18s,box-shadow .18s;}
.metric::before{content:"";position:absolute;left:0;right:0;top:0;height:5px;background:var(--r1);}
.metric:nth-child(1)::before{background:linear-gradient(90deg,var(--r1),var(--r2));}
.metric:nth-child(2)::before{background:linear-gradient(90deg,var(--r3),var(--r4));}
.metric:nth-child(3)::before{background:linear-gradient(90deg,var(--r5),var(--r6));}
.metric:nth-child(4)::before{background:linear-gradient(90deg,var(--r7),var(--r8));}
.metric:hover{transform:translateY(-3px);box-shadow:var(--shadow-md);}
.metric .label{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;font-weight:700;}
.metric .value{font-size:1.5rem;font-weight:850;color:var(--ink);margin-top:.4rem;}
.metric .delta{display:inline-block;margin-top:.45rem;font-size:.8rem;font-weight:700;
  padding:.2rem .55rem;border-radius:999px;background:#dcfce7;color:#15803d;}
.metric.accent{background:linear-gradient(135deg,#f0fdf4,#ecfeff);border-color:#bbf7d0;}
.metric.accent .value{color:#047857;}

/* Buttons */
.stButton>button,.stDownloadButton>button{border-radius:12px!important;font-weight:700!important;
  padding:.62rem 1.15rem!important;border:1px solid var(--line)!important;transition:all .2s!important;}
.stButton>button[kind="primary"],.stDownloadButton>button{
  background:linear-gradient(90deg,#ef4444,#f97316,#eab308,#22c55e,#06b6d4,#3b82f6,#8b5cf6,#ec4899,#ef4444)!important;
  background-size:300% 100%!important;animation:flow 10s linear infinite!important;
  border:none!important;color:#fff!important;text-shadow:0 1px 2px rgba(0,0,0,.25);
  box-shadow:0 12px 24px -12px rgba(139,92,246,.8)!important;}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button:hover{
  transform:translateY(-2px)!important;box-shadow:0 16px 28px -12px rgba(236,72,153,.8)!important;}
.stButton>button[kind="secondary"]:hover{border-color:var(--r7)!important;color:var(--r7)!important;}

/* Expanders: each agent gets its own rainbow stripe */
div[data-testid="stExpander"]{border:1px solid var(--line)!important;border-left:5px solid var(--r6)!important;
  border-radius:14px!important;background:#fff!important;box-shadow:var(--shadow-sm);
  margin-bottom:.65rem;overflow:hidden;}
div[data-testid="stExpander"]:nth-of-type(7n+1){border-left-color:var(--r1)!important;}
div[data-testid="stExpander"]:nth-of-type(7n+2){border-left-color:var(--r2)!important;}
div[data-testid="stExpander"]:nth-of-type(7n+3){border-left-color:var(--r3)!important;}
div[data-testid="stExpander"]:nth-of-type(7n+4){border-left-color:var(--r4)!important;}
div[data-testid="stExpander"]:nth-of-type(7n+5){border-left-color:var(--r5)!important;}
div[data-testid="stExpander"]:nth-of-type(7n+6){border-left-color:var(--r6)!important;}
div[data-testid="stExpander"]:nth-of-type(7n+7){border-left-color:var(--r7)!important;}
div[data-testid="stExpander"] summary{font-weight:700;padding:.7rem .95rem!important;}

/* Tables, containers, inputs */
div[data-testid="stDataFrame"],.stDataFrameGlideDataEditor{border-radius:14px!important;overflow:hidden;
  border:1px solid var(--line)!important;box-shadow:var(--shadow-sm);}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px!important;background:#fff;}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,textarea{border-radius:10px!important;}
div[data-testid="stSlider"] [role="slider"]{background:var(--r7)!important;}
hr{border:none;height:3px;border-radius:3px;background:var(--rainbow);opacity:.5;margin:1.2rem 0;}

/* Footer */
.footnote{color:var(--muted);font-size:.82rem;text-align:center;margin-top:2rem;padding-top:1rem;
  border-top:3px solid transparent;border-image:var(--rainbow) 1;}
.footnote b{background:var(--rainbow);-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;font-weight:800;}

/* RTL (Urdu) */
[dir="rtl"] .hero,[dir="rtl"] .metric,[dir="rtl"] .sec,[dir="rtl"] .note-banner{
  text-align:right;flex-direction:row-reverse;}
[dir="rtl"] div[data-testid="stExpander"] summary{text-align:right;}
[dir="rtl"] body,[dir="rtl"] p,[dir="rtl"] div{
  font-family:"Noto Nastaliq Urdu","Jameel Noori Nastaleeq",system-ui,sans-serif;}
@media (max-width:900px){.metrics{grid-template-columns:repeat(2,1fr);}.hero h1{font-size:2rem!important;}}
</style>
""", unsafe_allow_html=True)

# ---------- Language selector ----------
st.markdown('<div style="display:flex;justify-content:flex-end;">', unsafe_allow_html=True)
lang_choice = st.selectbox(
    LANG["English"]["lang_label"], ["English", "اردو"],
    label_visibility="collapsed", key="lang",
)
st.markdown('</div>', unsafe_allow_html=True)
t = LANG[lang_choice]
is_ur = lang_choice == "اردو"

if is_ur:
    st.markdown('<div dir="rtl">', unsafe_allow_html=True)

# ---------- Hero ----------
st.markdown(f"""
<div class="hero"><h1>{t['hero_title']}</h1><p>{t['hero_sub']}</p></div>
<div class="note-banner">ℹ️ {t['caption_note']}</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"### {t['sidebar_setup']}")
    bt_options = BUSINESS_TYPES_UR if is_ur else BUSINESS_TYPES_EN
    bt_index = st.selectbox(
        t["business_type"], list(range(len(bt_options))),
        format_func=lambda i: bt_options[i], index=0,
    )
    business_type = BUSINESS_TYPES_EN[bt_index]
    business_name = st.text_input(
        t["business_name"], "Multan Bakery" if not is_ur else "ملتان بیکری",
    )
    tariff = st.number_input(
        t["tariff"], min_value=1.0, max_value=500.0, value=65.0, step=1.0,
        help=t["tariff_help"],
    )
    open_hour = st.slider(t["open_hour"], 0, 23, 8)
    close_hour = st.slider(t["close_hour"], 1, 24, 20)
    if close_hour <= open_hour:
        st.warning(t["close_warning"])
    st.divider()
    st.markdown(f"### {t['ai_section']}")
    api_key = st.text_input(
        t["api_key"], type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
    )
    st.caption(t["api_caption"])

# ---------- Intake mode ----------
st.markdown(f"### {t['intake_title']}")
mode = st.radio(
    t["intake_title"], [t["intake_describe"], t["intake_manual"]],
    horizontal=True, label_visibility="collapsed",
)

if mode == t["intake_describe"]:
    free_text = st.text_area(
        t["describe_prompt"],
        placeholder=(
            "مثال: میری بیکری میں ایک بڑا اوون، ایک فریج، ایک آٹا مشین، اور کچھ لائٹس اور پنکھے ہیں۔"
            if is_ur else
            "e.g. My bakery has one large oven, one refrigerator, one dough mixer, and some lights and fans."
        ),
        height=110,
    )
    if st.button(t["describe_btn"], type="secondary", disabled=not api_key):
        parsed = parse_business_description(
            api_key, free_text, language="urdu" if is_ur else "english",
        )
        if parsed is not None and not parsed.empty:
            st.session_state["appliances_df"] = parsed
            st.success(t["describe_ok"])
        else:
            st.warning(t["describe_fail"])
    if not api_key:
        st.caption("🔒 AI intake needs a Gemini API key. Add one in the sidebar, or use manual mode.")

# ---------- Section 1: Appliances ----------
st.markdown(f'<div class="sec"><div class="num">1</div><div class="title">{t["appliances_title"]}</div></div>', unsafe_allow_html=True)
st.markdown(f'<div style="color:#64748b;font-size:.85rem;margin:-.3rem 0 .7rem 0;">{t["appliances_help"]}</div>', unsafe_allow_html=True)

default_names = DEFAULT_APPLIANCE_NAMES_UR if is_ur else DEFAULT_APPLIANCE_NAMES_EN
default_df_en = pd.DataFrame([
    {"Appliance": default_names[0], "Power (kW)": 3.0, "Hours/day": 5.0, "Flexible hours": 2.0, "Business critical": "High"},
    {"Appliance": default_names[1], "Power (kW)": 0.4, "Hours/day": 24.0, "Flexible hours": 0.0, "Business critical": "High"},
    {"Appliance": default_names[2], "Power (kW)": 1.2, "Hours/day": 1.0, "Flexible hours": 1.0, "Business critical": "Medium"},
    {"Appliance": default_names[3], "Power (kW)": 0.8, "Hours/day": 10.0, "Flexible hours": 2.0, "Business critical": "Medium"},
])

base_df = st.session_state.get("appliances_df", default_df_en)

if is_ur:
    display_df = base_df.rename(columns=dict(zip(APPLIANCE_COLS_EN, APPLIANCE_COLS_UR)))
    display_df["اہمیت"] = display_df["اہمیت"].map(dict(zip(CRIT_EN, CRIT_UR)))
else:
    display_df = base_df

edited_display = st.data_editor(
    display_df, num_rows="dynamic", width="stretch",
    key="appliance_editor_" + lang_choice,
    column_config={
        (APPLIANCE_COLS_UR[1] if is_ur else "Power (kW)"): st.column_config.NumberColumn(
            min_value=0.0, max_value=1000.0, step=0.1),
        (APPLIANCE_COLS_UR[2] if is_ur else "Hours/day"): st.column_config.NumberColumn(
            min_value=0.0, max_value=24.0, step=0.5),
        (APPLIANCE_COLS_UR[3] if is_ur else "Flexible hours"): st.column_config.NumberColumn(
            min_value=0.0, max_value=24.0, step=0.5),
        (APPLIANCE_COLS_UR[4] if is_ur else "Business critical"): st.column_config.SelectboxColumn(
            options=(CRIT_UR if is_ur else CRIT_EN)),
    },
)

if is_ur:
    edited_df = edited_display.rename(columns=dict(zip(APPLIANCE_COLS_UR, APPLIANCE_COLS_EN)))
    edited_df["Business critical"] = edited_df["Business critical"].map(dict(zip(CRIT_UR, CRIT_EN)))
    inv = {ur: en for ur, en in zip(DEFAULT_APPLIANCE_NAMES_UR, DEFAULT_APPLIANCE_NAMES_EN)}
    edited_df["Appliance"] = edited_df["Appliance"].replace(inv)
else:
    edited_df = edited_display

# ---------- Section 2 & 3 ----------
left, right = st.columns(2, gap="large")
with left:
    st.markdown(f'<div class="sec"><div class="num">2</div><div class="title">{t["goals_title"]}</div></div>', unsafe_allow_html=True)
    with st.container(border=True):
        target_saving = st.slider(t["target_saving"], 0, 50, 15)
        max_shift = st.slider(t["max_shift"], 0, 8, 2)
        avoid_peak = st.checkbox(t["avoid_peak"], value=True)
        user_goal = st.text_input(
            t["goal_label"], placeholder=t["goal_placeholder"], key="user_goal_input",
        )

with right:
    st.markdown(f'<div class="sec"><div class="num">3</div><div class="title">{t["scenario_title"]}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#64748b;font-size:.85rem;margin:-.3rem 0 .7rem 0;">{t["scenario_help"]}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        sc_options = [t["scenario_none"], t["scenario_close"], t["scenario_tariff"], t["scenario_unavailable"]]
        scenario = st.selectbox(t["scenario_label"], sc_options)

scenario_map = {
    t["scenario_none"]: "No change",
    t["scenario_close"]: "Business closes 2 hours earlier",
    t["scenario_tariff"]: "Electricity tariff increases by 15%",
    t["scenario_unavailable"]: "One flexible appliance becomes unavailable",
}
scenario_internal = scenario_map[scenario]

st.write("")
run = st.button(t["run_btn"], type="primary", width="stretch")

# ---------- Run logic ----------
if run:
    if close_hour <= open_hour:
        st.error(t["error_close"]); st.stop()
    if edited_df.empty:
        st.error(t["error_empty"]); st.stop()
    try:
        if api_key:
            result = run_agentic_wattpilot(
                api_key=api_key,
                edited_df=edited_df,
                tariff=tariff,
                business_type=business_type,
                business_name=business_name,
                open_hour=open_hour,
                close_hour=close_hour,
                user_goal=user_goal,
                language="urdu" if is_ur else "english",
            )
        else:
            result = run_wattpilot(
                edited_df=edited_df, tariff=tariff, business_type=business_type,
                business_name=business_name, open_hour=open_hour, close_hour=close_hour,
                target_saving=target_saving, max_shift=max_shift,
                avoid_peak=avoid_peak, scenario=scenario_internal,
            )
            result["agent_trace"] = ["Deterministic mode — no API key provided."]
            result["chosen_by_llm"] = False
    except (ValueError, TypeError) as exc:
        st.error(f"{t['error_values']} {exc}"); st.stop()

    st.session_state["wattpilot_result"] = result
    st.session_state["wattpilot_api_key"] = api_key

# ---------- Results ----------
if "wattpilot_result" in st.session_state:
    result = st.session_state["wattpilot_result"]
    st.divider()
    st.markdown(f"## ⚡ {t['report_title']}")

    st.markdown(f"""
    <div class="metrics">
      <div class="metric">
        <div class="label">{t['metric_daily_before']}</div>
        <div class="value">{t['pk']} {result['daily_cost_before']:,.0f}</div>
      </div>
      <div class="metric accent">
        <div class="label">{t['metric_daily_after']}</div>
        <div class="value">{t['pk']} {result['daily_cost_after']:,.0f}</div>
        <div class="delta">▼ {t['pk']} {result['daily_saving']:,.0f}</div>
      </div>
      <div class="metric">
        <div class="label">{t['metric_monthly']}</div>
        <div class="value">{t['pk']} {result['monthly_saving']:,.0f}</div>
      </div>
      <div class="metric">
        <div class="label">{t['metric_energy']}</div>
        <div class="value">{result['kwh_saved']:.1f} {t['kwh']}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    trace = result.get("agent_trace") or []
    if trace:
        with st.expander(t["trace_title"], expanded=False):
            for line in trace:
                st.markdown(f"- {line}")

    st.markdown(f"### 🤖 {t['workflow_title']}")
    for agent in result["agents"]:
        name = tr_agent(agent["name"]) if is_ur else agent["name"]
        status = tr_status(agent["status"]) if is_ur else agent["status"]
        finding = tr_text(agent["finding"]) if is_ur else agent["finding"]
        action = tr_text(agent["action"]) if is_ur else agent["action"]
        with st.expander(f"{name} — {status}", expanded=True):
            st.write(finding)
            st.write(f"**{t['action_label']}:** " + action)

    st.markdown(f"### 📋 {t['plan_title']}")
    plan_display = localize_plan(result["plan"]) if is_ur else result["plan"]
    st.dataframe(plan_display, width="stretch", hide_index=True)

    st.markdown(f"### 💰 {t['chart_title']}")
    chart_data = pd.DataFrame({
        "Scenario": [t["chart_current"], t["chart_optimized"]],
        "Cost (PKR)": [result["daily_cost_before"], result["daily_cost_after"]],
    }).set_index("Scenario")
    st.bar_chart(chart_data)

    st.markdown(f"### 💡 {t['impact_title']}")
    for item in result["cautions"]:
        st.markdown(f"- {tr_text(item) if is_ur else item}")

    if st.button(t["ai_btn"], key="ai_explain"):
        key = st.session_state.get("wattpilot_api_key", "")
        explanation = ask_gemini(
            key, result, business_name, business_type,
            language="urdu" if is_ur else "english",
        )
        st.session_state["wattpilot_explanation"] = explanation
    if st.session_state.get("wattpilot_explanation"):
        st.markdown(f"#### {t['ai_result_title']}")
        st.write(st.session_state["wattpilot_explanation"])

    st.download_button(
        t["download_btn"],
        (localize_plan(result["plan"]) if is_ur else result["plan"])
            .to_csv(index=False).encode("utf-8-sig"),
        file_name="wattpilot_recommendations.csv",
        mime="text/csv",
    )

if is_ur:
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="footnote">{t["footer"]}<br>'
    f'Made by <b>Ibrahim Usman</b> for the <b>NYLP AI HACKATHON 2026</b></div>',
    unsafe_allow_html=True,
)