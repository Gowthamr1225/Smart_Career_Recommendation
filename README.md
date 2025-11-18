# Career Recommender (IT, Non-IT, SAP/ERP, Accounts, Banking)

A Streamlit app that recommends career paths and an upskilling roadmap using semantic matching, domain boosts, and prerequisite-aware ranking. Covers IT, Non-IT, SAP/ERP, Accounts, and Banking.

## Run locally
1. python -m venv .venv
2. source .venv/bin/activate  # Windows: .venv\Scripts\activate
3. pip install -r requirements.txt
4. streamlit run app.py

## Files
- app.py: Streamlit UI
- smartcareer.py: Core logic
- courses.csv: Course catalog (editable)
- requirements.txt: Dependencies

## Customize
- Edit courses.csv to add providers, links, costs, durations, domains, and categories.
- Tune penalties/boosts and role mapping in smartcareer.py for your audience.
- Add resume parsing or switch catalog to SQLite if needed.

## Deploy on Streamlit Cloud
- Push to GitHub.
- On streamlit.io → New app → select repo → main file: app.py → Deploy.