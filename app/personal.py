"""Personalization: an optional profile + official eligibility rules -> the services that apply to this person.

The challenge asks for citizen profiles, service eligibility data and personalization
algorithms. Dalil's version is deliberately simple and checkable:

- PROFILE: a few optional answers (emirate, residence type, residence expiry date, drives,
  rents). Never names, ID, passport or card numbers. Kept on the phone, or in the account.
- ELIGIBILITY DATA: rules stored with each service in data/services.json, copied from the
  official pages (for example the ICP grace periods by residence type: 180 / 90 / 60 / 30 days).
- ALGORITHM: plain rules (below) that match the profile to services and apply the rules.
  No AI here, so the same profile always gets the same, explainable answer.
"""
import re
from datetime import date

from . import catalog

EMIRATES = ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]
# Residence types, worded like the official ICP grace-period categories
RESIDENCE = ["golden", "graduate", "skilled", "owner", "sponsored", "other", "citizen", "not_sure"]
HOME = ["rent", "own", "other"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def clean(profile) -> dict:
    """Keep only known fields with allowed values. This is the profile's privacy filter."""
    p = profile if isinstance(profile, dict) else {}
    out = {}
    if p.get("emirate") in EMIRATES:
        out["emirate"] = p["emirate"]
    if p.get("residence") in RESIDENCE:
        out["residence"] = p["residence"]
    if isinstance(p.get("residence_expiry"), str) and DATE.match(p["residence_expiry"]):
        try:
            date.fromisoformat(p["residence_expiry"])
            out["residence_expiry"] = p["residence_expiry"]
        except ValueError:
            pass
    if isinstance(p.get("drives"), bool):
        out["drives"] = p["drives"]
    if p.get("home") in HOME:
        out["home"] = p["home"]
    return out


def _service(service_id: str) -> dict | None:
    return next((s for s in catalog.load() if s["id"] == service_id), None)


def residency_service(profile: dict) -> dict | None:
    """Dubai residence -> GDRFA Dubai; any other emirate (or unknown) -> ICP (federal)."""
    if profile.get("residence") in (None, "citizen"):
        return None
    return _service("dubai-residency-notice" if profile.get("emirate") == "Dubai" else "federal-residency-notice")


def eligibility(profile: dict, service: dict | None) -> dict | None:
    """The official rule that applies to this person for this service, if the data has one.

    Returns {"grace_days": n, "source": "..."} or None (then the app says to check the
    official page for their category, and never guesses a number)."""
    rules = (service or {}).get("eligibility") or {}
    days = (rules.get("grace_days") or {}).get(profile.get("residence"))
    return {"grace_days": days, "source": rules.get("source")} if days else None


def _summary(service: dict) -> dict:
    keep = ["id", "service_name", "authority", "official_url", "verified", "last_checked", "help", "names"]
    return {k: service.get(k) for k in keep}


def for_you(profile, today: date | None = None) -> list[dict]:
    """The services that apply to this person, most urgent first."""
    p = clean(profile)
    today = today or date.today()
    cards = []

    residency = residency_service(p)
    if residency:
        days_left = None
        if p.get("residence_expiry"):
            days_left = (date.fromisoformat(p["residence_expiry"]) - today).days
        cards.append({"reason": "residency", "service": _summary(residency), "days_left": days_left,
                      "eligibility": eligibility(p, residency),
                      "urgent": days_left is not None and days_left <= 30})

    if p.get("drives"):
        fines = {"Dubai": "dubai-traffic-fine", "Abu Dhabi": "abu-dhabi-traffic-fine"}.get(p.get("emirate"))
        if fines and _service(fines):
            cards.append({"reason": "driving", "service": _summary(_service(fines)), "emirate": p["emirate"],
                          "days_left": None, "eligibility": None, "urgent": False})

    if p.get("home") == "rent" and p.get("emirate") == "Dubai" and _service("dubai-tenancy-contract"):
        cards.append({"reason": "renting", "service": _summary(_service("dubai-tenancy-contract")),
                      "emirate": "Dubai", "days_left": None, "eligibility": None, "urgent": False})

    # most urgent first (a residence expiring within 30 days), then the order above
    return [c for _, c in sorted(enumerate(cards), key=lambda ic: (not ic[1]["urgent"], ic[0]))]
