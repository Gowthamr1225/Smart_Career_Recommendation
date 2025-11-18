# smartcareer.py
import json
import pandas as pd
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Model cache
# -----------------------------
_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

# -----------------------------
# Load course catalog
# -----------------------------
def load_course_catalog(csv_path: str = "courses.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {
        "title","provider","duration_months","prerequisites","skill_tags",
        "level","link","cost","domain","category"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"courses.csv missing columns: {missing}")

    # Normalize fields
    df["level"] = df["level"].astype(str).str.strip().str.lower()
    df["domain"] = df["domain"].astype(str).str.strip().str.lower()
    df["category"] = df["category"].astype(str).str.strip().str.lower()
    df["skill_tags"] = df["skill_tags"].astype(str).str.strip().str.lower()
    df["prerequisites"] = df["prerequisites"].astype(str).str.strip().str.lower()
    df["duration_months"] = df["duration_months"].astype(int)
    df["cost"] = df["cost"].astype(float)
    return df

# -----------------------------
# Build user profile text
# -----------------------------
def build_user_profile(
    persona: str,
    education: str,
    experience_years: int,
    technical_skills: List[str],
    soft_skills: List[str],
    current_domain: str,
    target_domain: str,
    preferred_study_hours_per_week: int
) -> str:
    tech = ", ".join([s.strip() for s in technical_skills if s.strip()]).lower()
    soft = ", ".join([s.strip() for s in soft_skills if s.strip()]).lower()
    return (
        f"persona: {persona.lower()}; education: {education.lower()}; "
        f"experience: {experience_years} years; technical skills: {tech}; soft skills: {soft}; "
        f"current domain: {current_domain.lower()}; target domain: {target_domain.lower()}; "
        f"study hours: {preferred_study_hours_per_week} per week"
    )

# -----------------------------
# Compute fit scores (semantic + rules)
# -----------------------------
def compute_fit_scores(user_profile_text: str, catalog: pd.DataFrame, target_domain: str) -> pd.DataFrame:
    model = get_model()
    user_vec = model.encode([user_profile_text])

    course_texts = catalog.apply(
        lambda r: f"{r['title']} | {r['skill_tags']} | prereq:{r['prerequisites']} | level:{r['level']} | domain:{r['domain']} | category:{r['category']}",
        axis=1
    ).tolist()
    course_vecs = model.encode(course_texts)
    sims = cosine_similarity(user_vec, course_vecs)[0]

    ranked = catalog.copy()
    ranked["fit_score"] = sims * 100

    # Domain boost: prioritize courses that match target domain keywords
    td = target_domain.strip().lower()
    td_keyword = td.split()[0] if td else ""
    ranked["domain_boost"] = ranked["domain"].apply(lambda d: 8 if td_keyword and td_keyword in d else 0)

    # Prereq/level penalties based on inferred readiness
    def penalty(row):
        p = 0
        level = row["level"]
        prereq = row["prerequisites"]
        # penalize advanced content if user signals beginner
        if ("beginner" in user_profile_text or "no coding" in user_profile_text) and level == "advanced":
            p += 15
        # penalty for missing prerequisites
        if prereq not in {"none", "", "nan"}:
            tokens = [t for t in prereq.replace("/", " ").replace(",", " ").split() if t]
            missing = [t for t in tokens if t not in user_profile_text]
            if missing:
                p += 10
        return p

    ranked["penalty"] = ranked.apply(penalty, axis=1)
    ranked["fit_score"] = (ranked["fit_score"] + ranked["domain_boost"] - ranked["penalty"]).clip(0, 100)
    return ranked.sort_values(by="fit_score", ascending=False)

# -----------------------------
# Assign timeline
# -----------------------------
def assign_timeline(row: pd.Series, hours_per_week: int) -> str:
    if row["duration_months"] <= 3 and hours_per_week >= 6 and row["level"] in {"beginner", "intermediate"}:
        return "short-term (1–3 months)"
    return "long-term (3–12 months)"

# -----------------------------
# Map to roles (IT, non-IT, SAP/ERP, Accounts, Banking)
# -----------------------------
def map_skills_to_roles(skill_tags: str, domain: str) -> List[str]:
    s = f"{skill_tags} {domain}".lower()
    roles = []

    # IT roles
    if any(k in s for k in ["python","sql","ml","pandas","scikit","data","analytics"]):
        roles += ["Data Analyst","Data Scientist"]
    if any(k in s for k in ["deep learning","pytorch","tensorflow","nlp","cv","transformers"]):
        roles += ["ML Engineer"]
    if any(k in s for k in ["cloud","aws","azure","gcp","devops","kubernetes","docker"]):
        roles += ["Cloud/DevOps Engineer"]
    if any(k in s for k in ["java","javascript","react","node","backend","frontend","full stack","django","flask","fastapi"]):
        roles += ["Software Engineer"]
    if "cybersecurity" in s or "security" in s:
        roles += ["Cybersecurity Specialist"]
    if any(k in s for k in ["ui","ux","figma","design","wireframe","interaction"]):
        roles += ["UI/UX Designer"]
    if any(k in s for k in ["qa","testing","selenium","cypress","pytest"]):
        roles += ["QA/Test Engineer"]

    # Non-IT roles
    if any(k in s for k in ["excel","analytics","business","visualization","power bi","tableau","dashboard"]):
        roles += ["Business Analyst"]
    if any(k in s for k in ["marketing","seo","content","social media","ads","analytics"]):
        roles += ["Digital Marketing Specialist"]
    if any(k in s for k in ["finance","accounting","fp&a","valuation","tally","gst","sap fico","erp","sap mm","sap sd","sap hcm"]):
        roles += ["Finance Analyst","Accounting Professional","SAP/ERP Specialist"]
    if any(k in s for k in ["hr","recruitment","talent","people ops","hrms"]):
        roles += ["HR Executive"]
    if any(k in s for k in ["operations","supply chain","logistics","lean","six sigma","procurement"]):
        roles += ["Operations/Supply Chain Analyst"]
    if any(k in s for k in ["product","roadmap","ux","wireframe","agile"]):
        roles += ["Product Manager (Associate)"]
    if any(k in s for k in ["sales","crm","inside sales","bd","lead gen"]):
        roles += ["Sales/Business Development Executive"]

    # Banking sector roles
    if any(k in s for k in ["banking","credit","risk","loan","investment","treasury","retail banking","corporate banking","nbfc"]):
        roles += ["Banking Operations Associate","Credit Risk Analyst","Investment Banking Analyst","Retail Banking Officer"]

    # FinTech extras (optional broader finance tech)
    if any(k in s for k in ["fintech","payments","upi","cards","core banking"]):
        roles += ["FinTech Analyst"]

    if not roles:
        roles = ["Generalist — explore foundation courses"]

    # Deduplicate preserving order
    seen, ordered = set(), []
    for r in roles:
        if r not in seen:
            seen.add(r)
            ordered.append(r)
    return ordered

# -----------------------------
# Rationale text
# -----------------------------
def make_rationale(user_profile_text: str, row: pd.Series) -> str:
    prep = "no formal prerequisites" if row["prerequisites"] in {"none", ""} else f"prerequisites: {row['prerequisites']}"
    return (
        f"Matches your profile via {row['skill_tags']}. Builds {row['category']} in {row['domain']}. "
        f"Level: {row['level']}, duration: {row['duration_months']} months, {prep}."
    )

# -----------------------------
# Build roadmap
# -----------------------------
def build_roadmap(
    persona: str,
    user_profile_text: str,
    catalog: pd.DataFrame,
    target_domain: str,
    top_n: int,
    hours_per_week: int,
    budget_cap: Optional[float] = None
) -> Dict:
    ranked = compute_fit_scores(user_profile_text, catalog, target_domain)

    if budget_cap and budget_cap > 0:
        ranked = ranked[ranked["cost"] <= budget_cap]

    short, long = [], []
    cost_s, cost_l = 0.0, 0.0

    for _, row in ranked.head(top_n).iterrows():
        timeline = assign_timeline(row, hours_per_week)
        item = {
            "title": row["title"],
            "provider": row["provider"],
            "fit_score": round(row["fit_score"], 2),
            "timeline": timeline,
            "level": row["level"],
            "duration_months": int(row["duration_months"]),
            "domain": row["domain"],
            "category": row["category"],
            "rationale": make_rationale(user_profile_text, row),
            "recommended_prep": "Brush up prerequisites" if row["prerequisites"] not in {"none", ""} else "Start directly",
            "link": row["link"],
            "cost": float(row["cost"]),
            "suggested_roles": map_skills_to_roles(row["skill_tags"], row["domain"])
        }
        if timeline.startswith("short-term"):
            short.append(item)
            cost_s += item["cost"]
        else:
            long.append(item)
            cost_l += item["cost"]

    return {
        "persona": persona,
        "short_term_plan": short,
        "long_term_plan": long,
        "short_term_total_cost": round(cost_s, 2),
        "long_term_total_cost": round(cost_l, 2)
    }

# -----------------------------
# Public API
# -----------------------------
def recommend(
    persona: str,
    education: str,
    experience_years: int,
    technical_skills: List[str],
    soft_skills: List[str],
    current_domain: str,
    target_domain: str,
    preferred_study_hours_per_week: int,
    top_n: int = 15,
    budget_cap: Optional[float] = None
) -> Dict:
    profile = build_user_profile(
        persona=persona,
        education=education,
        experience_years=experience_years,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        current_domain=current_domain,
        target_domain=target_domain,
        preferred_study_hours_per_week=preferred_study_hours_per_week
    )
    catalog = load_course_catalog("courses.csv")
    return build_roadmap(
        persona=persona,
        user_profile_text=profile,
        catalog=catalog,
        target_domain=target_domain,
        top_n=top_n,
        hours_per_week=preferred_study_hours_per_week,
        budget_cap=budget_cap
    )

def to_json(data: Dict) -> str:
    return json.dumps(data, indent=2)