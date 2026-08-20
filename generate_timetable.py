"""
This is the heart of the app: turn survey answers into a JSON day-plan
using watsonx. Run this file directly to stress-test the prompt against
a few fake survey inputs before you wire it into the real UI.
"""
import json
from watsonx_client import get_model


def build_prompt(survey):
    goals_text = ", ".join(f"{hours}h {category}" for category, hours in survey["goals"].items())
    categories = ", ".join(survey["goals"].keys())
    return f"""You are creating a daily schedule for someone with these traits:
- Chronotype: {survey['chronotype']}
- Peak energy window: {survey['peak_start']} to {survey['peak_end']}
- Daily goals: {goals_text}

Create a full-day schedule (wake to sleep) as a JSON array ONLY.
No explanation, no markdown formatting, no text before or after the array.
Each item must look exactly like this:
{{"start": "07:00", "end": "08:00", "activity": "Workout", "category": "fitness"}}

Categories must be one of: {categories}, plus "rest" or "other" if needed.
Put the most demanding goal activities during the peak energy window.
Return ONLY the JSON array, nothing else."""


def extract_json(text):
    """Models sometimes add stray words around the array - grab just the
    brackets and everything between them."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in model output")
    return json.loads(text[start:end + 1])


def generate_timetable(survey):
    model = get_model(max_tokens=800, temperature=0.2)
    raw_output = model.generate_text(prompt=build_prompt(survey))
    return extract_json(raw_output), raw_output


if __name__ == "__main__":
    fake_surveys = [
        {
            "chronotype": "night owl",
            "peak_start": "18:00",
            "peak_end": "22:00",
            "goals": {"fitness": 1, "study": 3, "hobbies": 1},
        },
        {
            "chronotype": "morning person",
            "peak_start": "06:00",
            "peak_end": "10:00",
            "goals": {"fitness": 1.5, "work": 6, "hobbies": 0.5},
        },
        {
            "chronotype": "morning person",
            "peak_start": "07:00",
            "peak_end": "11:00",
            "goals": {"fitness": 0.5, "study": 4, "food": 1.5, "hobbies": 1},
        },
    ]

    for i, survey in enumerate(fake_surveys, start=1):
        print(f"\n--- Test {i}: {survey['chronotype']} ---")
        try:
            timetable, raw = generate_timetable(survey)
            print(f"Parsed {len(timetable)} blocks successfully:")
            for block in timetable:
                print(f"  {block['start']}-{block['end']}  {block['activity']} ({block['category']})")
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(f"Failed to parse JSON: {e}")
            print("Raw output was:")
            print(raw)
