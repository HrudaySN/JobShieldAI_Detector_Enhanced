"""Explainable baseline classifier and safety checks for JobShield AI."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

TOKEN_RE = re.compile(r"[a-zA-Z]{2,}")
DATASET = Path(__file__).with_name("data") / "job_postings_sample.csv"

RED_FLAGS = {
    "upfront payment": ("Requests upfront payment", 20),
    "registration fee": ("Requests a registration fee", 20),
    "security deposit": ("Requests a security deposit", 20),
    "processing payment": ("Requests a processing payment", 18),
    "verification charge": ("Requests a verification charge", 18),
    "refundable": ("Uses a refundable-fee claim", 12),
    "upi": ("Mentions UPI payment", 12),
    "telegram": ("Uses Telegram as the contact method", 12),
    "whatsapp": ("Uses WhatsApp as the contact method", 8),
    "no interview": ("Promises selection without an interview", 16),
    "no experience": ("Claims no experience is needed", 6),
    "bank details": ("Requests bank details", 15),
    "aadhaar": ("Requests identity documents early", 12),
    "guaranteed": ("Makes a guaranteed-income claim", 10),
    "work from home": ("Uses a work-from-home offer", 2),
}

POSITIVE_SIGNALS = {
    "official careers": "Official careers channel mentioned",
    "careers page": "Official careers channel mentioned",
    "interview process": "Structured interview process mentioned",
    "video interview": "Structured interview process mentioned",
    "health insurance": "Benefits are described",
    "salary range": "A salary range is provided",
    "no payment is required": "Explicitly says no payment is required",
}

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me", "protonmail.com"}


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _domain(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return (parsed.hostname or "").lower().removeprefix("www.")


class JobRiskModel:
    def __init__(self, dataset_path: Path = DATASET):
        self.class_docs = Counter()
        self.class_words = {"fake": Counter(), "genuine": Counter()}
        self.class_totals = Counter()
        self.vocabulary: set[str] = set()
        self.examples = 0
        self._train(dataset_path)

    def _train(self, dataset_path: Path) -> None:
        with dataset_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                label = row["label"]
                words = _tokens(row["text"])
                self.class_docs[label] += 1
                self.class_words[label].update(words)
                self.class_totals[label] += len(words)
                self.vocabulary.update(words)
                self.examples += 1

    def _log_probability(self, words: list[str], label: str) -> float:
        prior = self.class_docs[label] / self.examples
        denominator = self.class_totals[label] + len(self.vocabulary)
        return math.log(prior) + sum(
            math.log((self.class_words[label][word] + 1) / denominator) for word in words
        )

    def analyze(self, text: str, metadata: dict | None = None) -> dict:
        metadata = metadata or {}
        clean = " ".join((text or "").split())
        lowered = clean.lower()
        words = _tokens(clean)
        if len(words) < 4:
            raise ValueError("Please paste a little more of the job description (at least 4 words).")

        fake_log = self._log_probability(words, "fake")
        genuine_log = self._log_probability(words, "genuine")
        probability = 1 / (1 + math.exp(genuine_log - fake_log))

        evidence = []
        rule_boost = 0
        for phrase, (message, weight) in RED_FLAGS.items():
            if phrase in lowered:
                evidence.append({"phrase": phrase, "message": message, "weight": weight, "type": "red_flag"})
                rule_boost += weight

        positive = []
        for phrase, message in POSITIVE_SIGNALS.items():
            if phrase in lowered and message not in positive:
                positive.append(message)

        source_checks = []
        job_url = (metadata.get("job_url") or "").strip()
        recruiter_email = (metadata.get("recruiter_email") or "").strip().lower()
        company_website = (metadata.get("company_website") or "").strip()

        if job_url:
            domain = _domain(job_url)
            if domain:
                if "linkedin.com" in domain:
                    source_checks.append({"status": "info", "message": "LinkedIn job URL supplied for source verification."})
                else:
                    source_checks.append({"status": "ok", "message": f"Job source domain detected: {domain}. Verify it is the company's official site."})
            else:
                source_checks.append({"status": "warning", "message": "The job URL could not be validated as a normal website URL."})

        if company_website:
            website_domain = _domain(company_website)
            if website_domain:
                source_checks.append({"status": "ok", "message": f"Company website domain detected: {website_domain}."})
            else:
                source_checks.append({"status": "warning", "message": "The company website could not be validated."})

        if recruiter_email:
            if "@" not in recruiter_email:
                source_checks.append({"status": "warning", "message": "Recruiter email format looks invalid."})
            else:
                email_domain = recruiter_email.rsplit("@", 1)[-1].strip().removeprefix("www.")
                if email_domain in FREE_EMAIL_DOMAINS:
                    source_checks.append({"status": "warning", "message": f"Recruiter uses a free email domain ({email_domain}); verify independently."})
                    rule_boost += 5
                elif company_website and _domain(company_website) and email_domain != _domain(company_website):
                    source_checks.append({"status": "warning", "message": "Recruiter email domain does not match the company website domain."})
                    rule_boost += 10
                else:
                    source_checks.append({"status": "ok", "message": f"Recruiter email domain: {email_domain}."})

        answers = metadata.get("questions") or {}
        question_rules = [
            ("payment", "yes", "You reported a payment/deposit request.", 20),
            ("whatsapp_only", "yes", "You reported a WhatsApp/chat-only interview.", 12),
            ("unrealistic_salary", "yes", "You reported an unusually high salary claim.", 10),
            ("official_email", "no", "The offer did not come from an official company email.", 10),
            ("verify_company", "no", "The company could not be independently verified.", 10),
        ]
        for key, expected, message, weight in question_rules:
            if str(answers.get(key, "")).lower() == expected:
                evidence.append({"phrase": "Screening answer", "message": message, "weight": weight, "type": "screening"})
                rule_boost += weight

        risk = round(min(99, max(1, probability * 100 + rule_boost - len(positive) * 5)))
        if risk >= 65:
            verdict, tone, risk_level = "Likely fake", "fake", "High"
        elif risk >= 40:
            verdict, tone, risk_level = "Needs review", "review", "Medium"
        else:
            verdict, tone, risk_level = "Lower risk", "genuine", "Low"

        actions = []
        if any(item["type"] in {"red_flag", "screening"} and item["weight"] >= 15 for item in evidence):
            actions.append("Do not pay any fee, deposit, or verification charge.")
        actions.append("Verify the company through its official careers website and independently found contact details.")
        if recruiter_email or company_website or job_url:
            actions.append("Check that the recruiter email, job URL, and company domain belong to the same organization.")
        if risk >= 65:
            actions.append("Stop communication and report the listing/account to the platform if it appears fraudulent.")
        else:
            actions.append("Do not share bank details, OTPs, or identity documents until the employer is verified.")

        return {
            "risk_score": risk,
            "risk_level": risk_level,
            "verdict": verdict,
            "tone": tone,
            "flags": [item["message"] for item in evidence if item["type"] in {"red_flag", "screening"}][:8],
            "evidence": evidence[:10],
            "positive_signals": positive[:4],
            "source_checks": source_checks[:6],
            "actions": actions[:4],
            "model": {"name": "Naive Bayes baseline + safety rules", "training_examples": self.examples},
        }


model = JobRiskModel()
