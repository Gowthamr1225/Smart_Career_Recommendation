# app.py
import streamlit as st
from smartcareer import recommend, to_json

st.set_page_config(page_title="Career Recommender (IT, Non-IT, SAP/ERP, Accounts, Banking)", layout="wide")
st.title("🎯 Career Recommender for IT, Non-IT, SAP/ERP, Accounts, and Banking")

st.write("Enter your details to get a personalized roadmap with roles and courses.")

with st.sidebar:
    st.header("Options")
    top_n = st.slider("Max recommendations", min_value=5, max_value=30, value=15, step=1)
    budget_cap = st.number_input("Budget cap (USD, optional)", min_value=0.0, value=0.0, step=10.0)
    show_json = st.checkbox("Show JSON output", value=True)
    st.caption("Tip: Set a budget cap to prioritize free/low-cost courses.")

with st.form("profile_form"):
    st.subheader("Your profile")
    persona = st.selectbox("You are", ["Student", "Professional"])
    education = st.text_input("Education", "B.Com / B.E / MBA (specify)")
    experience_years = st.number_input("Experience (years)", min_value=0, max_value=40, value=0, step=1)

    current_domain = st.selectbox(
        "Current domain",
        ["Non-IT", "IT", "Finance", "Marketing", "HR", "Operations", "Sales", "Other"],
        index=0
    )
    target_domain = st.selectbox(
        "Target domain",
        [
            "IT - Data/ML",
            "IT - Software",
            "IT - Cloud/DevOps",
            "IT - Cybersecurity",
            "IT - UI/UX",
            "Non-IT - Business/BA",
            "Non-IT - Marketing",
            "Non-IT - Finance/Accounts (incl. SAP/ERP)",
            "Banking",
            "Non-IT - HR",
            "Operations/Supply Chain",
            "Undecided"
        ],
        index=0
    )

    technical_skills = st.text_area("Technical skills (comma-separated)", "Excel, Basics of Python, Tally, Banking Basics")
    soft_skills = st.text_area("Soft skills (comma-separated)", "Communication, Problem-solving, Teamwork")
    study_hours = st.slider("Study hours per week", min_value=2, max_value=25, value=6, step=1)

    submit = st.form_submit_button("Generate roadmap")

if submit:
    tech_list = [s.strip() for s in technical_skills.split(",") if s.strip()]
    soft_list = [s.strip() for s in soft_skills.split(",") if s.strip()]
    budget = budget_cap if budget_cap > 0 else None

    st.info("Generating personalized roadmap...")
    result = recommend(
        persona=persona,
        education=education,
        experience_years=experience_years,
        technical_skills=tech_list,
        soft_skills=soft_list,
        current_domain=current_domain,
        target_domain=target_domain,
        preferred_study_hours_per_week=study_hours,
        top_n=top_n,
        budget_cap=budget
    )

    st.subheader("📌 Short-term plan (1–3 months)")
    if result["short_term_plan"]:
        for item in result["short_term_plan"]:
            st.markdown(f"### {item['title']} — {item['provider']}")
            st.markdown(
                f"- **Domain:** {item['domain']} | **Category:** {item['category']}\n"
                f"- **Fit score:** {item['fit_score']} | **Level:** {item['level']}\n"
                f"- **Duration:** {item['duration_months']} months | **Cost:** ${item['cost']:.2f}\n"
                f"- **Rationale:** {item['rationale']}\n"
                f"- **Recommended prep:** {item['recommended_prep']}\n"
                f"- **Suggested roles:** {', '.join(item['suggested_roles'])}\n"
                f"- [🔗 Enrollment link]({item['link']})"
            )
        st.success(f"Estimated short-term total cost: ${result['short_term_total_cost']:.2f}")
    else:
        st.warning("No short-term courses matched your profile and constraints.")

    st.subheader("🎯 Long-term plan (3–12 months)")
    if result["long_term_plan"]:
        for item in result["long_term_plan"]:
            st.markdown(f"### {item['title']} — {item['provider']}")
            st.markdown(
                f"- **Domain:** {item['domain']} | **Category:** {item['category']}\n"
                f"- **Fit score:** {item['fit_score']} | **Level:** {item['level']}\n"
                f"- **Duration:** {item['duration_months']} months | **Cost:** ${item['cost']:.2f}\n"
                f"- **Rationale:** {item['rationale']}\n"
                f"- **Recommended prep:** {item['recommended_prep']}\n"
                f"- **Suggested roles:** {', '.join(item['suggested_roles'])}\n"
                f"- [🔗 Enrollment link]({item['link']})"
            )
        st.success(f"Estimated long-term total cost: ${result['long_term_total_cost']:.2f}")
    else:
        st.warning("No long-term courses matched your profile and constraints.")

    if show_json:
        st.subheader("🗂 JSON output")
        st.code(to_json(result), language="json")