"""Opportunity scoring.

Formula (documented in README too, max 100 points — higher = better lead,
i.e. weaker web presence):

  website missing                +50
  website present but http-only  +25
  website present with https      +0
  phone missing                  +20
  opening_hours missing          +15
  email missing                  +10
  address missing                 +5
  ----------------------------------
  maximum                        100

Levels: score >= 70 -> "high", 40-69 -> "medium", < 40 -> "low".
"""
from __future__ import annotations

from .models import Business

POINTS_NO_WEBSITE = 50
POINTS_HTTP_ONLY = 25
POINTS_NO_PHONE = 20
POINTS_NO_HOURS = 15
POINTS_NO_EMAIL = 10
POINTS_NO_ADDRESS = 5


def level_for(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def score_business(biz: Business) -> Business:
    """Score ``biz`` in place and return it."""
    score = 0
    reasons: list[str] = []
    if not biz.has_website:
        score += POINTS_NO_WEBSITE
        reasons.append("no website (+50)")
    elif not biz.website_is_https:
        score += POINTS_HTTP_ONLY
        reasons.append("website is http-only, no HTTPS (+25)")
    else:
        reasons.append("website with HTTPS (+0)")
    if not biz.phone.strip():
        score += POINTS_NO_PHONE
        reasons.append("no phone listed (+20)")
    if not biz.opening_hours.strip():
        score += POINTS_NO_HOURS
        reasons.append("no opening hours listed (+15)")
    if not biz.email.strip():
        score += POINTS_NO_EMAIL
        reasons.append("no email listed (+10)")
    if not biz.address.strip():
        score += POINTS_NO_ADDRESS
        reasons.append("no street address listed (+5)")
    biz.opportunity_score = score
    biz.opportunity_level = level_for(score)
    biz.reasons = reasons
    return biz


def score_all(businesses: list[Business]) -> list[Business]:
    """Score every business and return them sorted best-lead first."""
    scored = [score_business(b) for b in businesses]
    return sorted(scored, key=lambda b: (-(b.opportunity_score or 0), b.name.lower()))
