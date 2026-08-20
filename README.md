# Ideal Timetable

A personalized time-table app: a short survey (chronotype, peak-energy
window, and per-category goal hours) generates an editable daily schedule,
then tracks daily completion with a streak counter and a goal meter.

## IBM watsonx integration
`generate_timetable.py` builds a prompt from the survey answers and calls
an IBM Granite model on watsonx.ai (via the `ibm-watsonx-ai` SDK) to
generate the schedule as structured JSON. `watsonx_client.py` handles
authentication. `test_connection.py` is a minimal script proving the
watsonx credentials and API call work.

If watsonx credentials aren't configured in `.env`, `app.py` automatically
falls back to a rule-based schedule generator so the rest of the app
(editing, streaks, goal meter) remains fully demonstrable either way.

## Run it
```
https://priyanshkumaryadavpbel30-lnl3xj5cuwqgdar6su3pas.streamlit.app/
pip install -r requirements.txt
cp .env.example .env   
streamlit run app.py
```
