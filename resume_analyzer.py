"""Explainable, keyword-based resume skill matching for JobShield AI."""

from __future__ import annotations

import re

# Master skills list, grouped loosely by domain. Matching is case-insensitive
# and looks for these as whole words/phrases inside the resume text. A few
# entries include common no-space variants (e.g. "reactjs") since resumes
# often write framework names without a separating space.
SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "html", "css",
    "react", "reactjs", "angular", "vue", "vuejs", "node.js", "nodejs", "flask",
    "django", "spring", "rest api", "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "machine learning", "deep learning", "nlp", "data analysis",
    "data visualization", "power bi", "tableau", "excel", "statistics", "aws",
    "azure", "gcp", "docker", "kubernetes", "git", "ci/cd", "linux", "agile",
    "scrum", "project management", "communication", "leadership", "problem solving",
    "figma", "ui/ux", "photoshop", "seo", "content writing", "digital marketing",
    "salesforce", "accounting", "excel vba",
]

# Common target roles and the skills most associated with each, used both for
# fit-score calculation (when the user gives a target role) and for suggesting
# roles when they don't.
ROLE_SKILLS = {
    "Data Analyst": ["python", "sql", "excel", "data analysis", "power bi", "tableau", "statistics"],
    "Data Scientist": ["python", "machine learning", "statistics", "pandas", "numpy", "scikit-learn", "sql"],
    "Frontend Developer": ["javascript", "html", "css", "react", "typescript", "git"],
    "Backend Developer": ["python", "sql", "rest api", "flask", "django", "docker", "git"],
    "Business Intelligence Analyst": ["sql", "power bi", "tableau", "excel", "data visualization"],
    "DevOps Engineer": ["docker", "kubernetes", "aws", "ci/cd", "linux", "git"],
    "Project Manager": ["agile", "scrum", "project management", "communication", "leadership"],
    "Digital Marketing Specialist": ["seo", "content writing", "digital marketing", "communication"],
}


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def _find_skills(text_lower: str) -> list[str]:
    found = []
    for skill in SKILLS:
        pattern = r"(?<![a-zA-Z])" + re.escape(skill) + r"(?![a-zA-Z])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


class ResumeScreeningModel:
    def __init__(self):
        self.skills = SKILLS
        self.roles = ROLE_SKILLS

    def analyze(self, text: str, target_role: str | None = None) -> dict:
        clean = _normalize(text)
        if len(clean.split()) < 10:
            raise ValueError("Please paste more of the resume (at least a few sentences).")

        detected = _find_skills(clean)
        detected_set = set(detected)

        target_role = (target_role or "").strip()
        role_match = None

        if target_role and target_role in self.roles:
            required = self.roles[target_role]
        else:
            # No target role given (or not recognized) — pick the best-fitting
            # role from the taxonomy based on overlap with detected skills.
            best_role, best_overlap = None, -1
            for role, required_skills in self.roles.items():
                overlap = len(detected_set & set(required_skills))
                if overlap > best_overlap:
                    best_role, best_overlap = role, overlap
            role_match = best_role
            required = self.roles[best_role]

        matched = [s for s in required if s in detected_set]
        missing = [s for s in required if s not in detected_set]
        fit_score = round(100 * len(matched) / len(required)) if required else 0

        # Recommend the top 3 roles overall by skill overlap, for the
        # "Recommended Jobs For You" section.
        ranked_roles = sorted(
            self.roles.items(),
            key=lambda item: len(detected_set & set(item[1])),
            reverse=True,
        )
        recommendations = []
        for role, required_skills in ranked_roles[:3]:
            pct = round(100 * len(detected_set & set(required_skills)) / len(required_skills)) if required_skills else 0
            recommendations.append({"role": role, "match": pct})

        return {
            "fit_score": fit_score,
            "target_role": target_role or role_match,
            "role_was_suggested": not bool(target_role and target_role in self.roles),
            "skills_detected": sorted(detected_set),
            "skills_missing": missing,
            "skills_matched_for_role": matched,
            "recommended_jobs": recommendations,
            "model": {"name": "Keyword-based skill matcher", "skills_tracked": len(self.skills), "roles_tracked": len(self.roles)},
        }


model = ResumeScreeningModel()