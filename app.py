import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# Try to use the real watsonx-powered generator. If credentials aren't set
# yet or the call fails, fall back to a rule-based schedule so the app
# always works end to end regardless of account setup status.
try:
    from generate_timetable import generate_timetable as ai_generate_timetable
    WATSONX_AVAILABLE = True
except Exception:
    WATSONX_AVAILABLE = False

DATA_FILE = "app_data.json"


# ---------- fallback rule-based generator (used if watsonx isn't ready) ----------
def add_minutes(time_str, minutes):
    t = datetime.strptime(time_str, "%H:%M") + timedelta(minutes=minutes)
    return t.strftime("%H:%M")


def rule_based_timetable(survey):
    wake = "06:00" if "morning" in survey["chronotype"] else "09:00"
    blocks = []
    current = [wake]

    def add_block(duration_min, activity, category):
        end = add_minutes(current[0], duration_min)
        blocks.append({"start": current[0], "end": end, "activity": activity, "category": category})
        current[0] = end

    add_block(30, "Morning routine", "other")
    add_block(30, "Breakfast", "food")
    for category, hours in survey["goals"].items():
        add_block(max(15, int(float(hours) * 60)), category.title(), category)
    add_block(30, "Wind down", "rest")
    return blocks


# ---------- data persistence ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"survey": None, "timetable": [], "log": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def seed_fake_history(data):
    """Seeds a few past days of completion history so the streak and goal
    meter aren't sitting at zero the first time you demo this."""
    if data["log"] or not data["timetable"]:
        return data
    today = datetime.now().date()
    for i in range(1, 5):
        day = (today - timedelta(days=i)).isoformat()
        data["log"][day] = {str(idx): (idx % 3 != 0) for idx in range(len(data["timetable"]))}
    save_data(data)
    return data


# ---------- streak & goal meter ----------
def calculate_streak(log):
    streak = 0
    day = datetime.now().date()
    while True:
        key = day.isoformat()
        if key not in log:
            break
        done = list(log[key].values())
        if done and sum(done) / len(done) >= 0.7:
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


def calculate_goal_progress(data):
    goals = data["survey"]["goals"] if data["survey"] else {}
    hits = {cat: 0 for cat in goals}
    for day_log in data["log"].values():
        for idx_str, done in day_log.items():
            if not done:
                continue
            idx = int(idx_str)
            if idx < len(data["timetable"]):
                cat = data["timetable"][idx]["category"]
                if cat in hits:
                    hits[cat] += 1
    return hits, goals


# ---------- UI ----------
st.set_page_config(page_title="Ideal Timetable", layout="centered")
st.title("Your Ideal Timetable")

data = load_data()

if not WATSONX_AVAILABLE:
    st.info("watsonx isn't connected yet, so a rule-based schedule is being used. "
             "The watsonx integration code lives in generate_timetable.py and will "
             "be used automatically the moment your .env has valid credentials.")

with st.form("survey_form"):
    st.subheader("Quick survey")
    chronotype = st.radio("Are you more of a...", ["morning person", "night owl"])
    st.caption("Peak energy window")
    col1, col2 = st.columns(2)
    peak_start = col1.time_input("Starts around")
    peak_end = col2.time_input("Ends around")
    st.caption("How many hours per day do you want for each?")
    fitness_h = st.number_input("Fitness", 0.0, 8.0, 1.0, 0.5)
    study_h = st.number_input("Study / Work", 0.0, 12.0, 4.0, 0.5)
    hobbies_h = st.number_input("Hobbies", 0.0, 8.0, 1.0, 0.5)
    submitted = st.form_submit_button("Generate my timetable")

if submitted:
    survey = {
        "chronotype": chronotype,
        "peak_start": peak_start.strftime("%H:%M"),
        "peak_end": peak_end.strftime("%H:%M"),
        "goals": {"fitness": fitness_h, "study": study_h, "hobbies": hobbies_h},
    }
    data["survey"] = survey
    if WATSONX_AVAILABLE:
        try:
            timetable, _ = ai_generate_timetable(survey)
        except Exception as e:
            st.warning(f"watsonx call failed ({e}) - using rule-based fallback instead.")
            timetable = rule_based_timetable(survey)
    else:
        timetable = rule_based_timetable(survey)
    data["timetable"] = timetable
    data["log"] = {}
    save_data(data)
    seed_fake_history(data)
    st.rerun()

if data["survey"] and data["timetable"]:
    st.subheader("Your timetable (editable)")
    df = pd.DataFrame(data["timetable"])
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save changes"):
        data["timetable"] = edited.to_dict("records")
        save_data(data)
        st.success("Saved.")

    st.subheader("Today")
    today_key = datetime.now().date().isoformat()
    today_log = data["log"].get(today_key, {})
    for idx, block in enumerate(data["timetable"]):
        checked = st.checkbox(
            f"{block['start']}-{block['end']}  {block['activity']} ({block['category']})",
            value=today_log.get(str(idx), False),
            key=f"chk_{idx}",
        )
        today_log[str(idx)] = checked
    if st.button("Save today's progress"):
        data["log"][today_key] = today_log
        save_data(data)
        st.success("Today's progress saved.")

    st.subheader("Streak")
    st.metric("Consistent days in a row", calculate_streak(data["log"]))

    st.subheader("Goal meter")
    hits, goals = calculate_goal_progress(data)
    days_logged = max(1, len(data["log"]))
    for cat in goals:
        done = hits.get(cat, 0)
        st.write(f"{cat.title()}: hit on {done} / {days_logged} logged days")
        st.progress(min(1.0, done / days_logged))
else:
    st.info("Fill out the survey above to generate your timetable.")
