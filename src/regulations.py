import logging
from livekit.agents import function_tool

logger = logging.getLogger("regulation-tool")

# ── Health Insurance (IRDAI Standards) ─────────────────────────────────────

HEALTH = {
    "waiting_period": (
        "Under IRDAI norms, there is a 30-day initial waiting period (except for accidents). "
        "Pre-existing diseases (PED) have a maximum waiting period of 3 years (reduced from 4 years in 2024). "
        "Specific diseases like hernia or cataracts usually have a 2-year waiting period."
    ),
    "moratorium_period": (
        "The 'Moratorium Period' is a 3-year continuous coverage rule. After 3 years of continuous renewal, "
        "an insurer cannot reject a claim based on non-disclosure or misrepresentation, "
        "except in cases of established fraud."
    ),
    "cashless_anywhere": (
        "The 'Cashless Everywhere' initiative allows policyholders to get cashless treatment even in "
        "non-empanelled hospitals, provided the insurer is notified 48 hours before elective surgery "
        "or within 48 hours of emergency admission."
    ),
    "reimbursement": (
        "For non-network hospitals, claim documents must be submitted within 7–15 days of discharge. "
        "Insurers must settle or reject the claim within 30 days of receiving the final document."
    ),
    "room_rent": (
        "Room rent is often capped at 1% of the Sum Insured for normal rooms and 2% for ICU. "
        "Exceeding this triggers 'Proportionate Deduction,' where the insurer reduces payment "
        "for all associated medical expenses (doctors, surgery, etc.) proportionally."
    ),
    "no_claim_bonus": (
        "NCB in Health Insurance increases the Sum Insured by 10% to 50% for every claim-free year "
        "without increasing the premium. If a claim is made, the bonus is reduced at the same rate it was earned."
    ),
    "portability": (
        "You can port your policy to a new insurer at least 45 days before renewal. "
        "The new insurer must give you credit for the waiting periods already served with the previous insurer."
    ),
}

# ── Motor Insurance (Motor Vehicles Act & IRDAI) ───────────────────────────

MOTOR = {
    "third_party": (
        "Third-party liability is mandatory under the Motor Vehicles Act. It covers legal liability for "
        "third-party death, bodily injury, or property damage (up to ₹7.5 lakh for private cars). "
        "It does not cover damage to your own vehicle."
    ),
    "own_damage": (
        "Own Damage (OD) covers theft, fire, and accidental damage to your vehicle. "
        "The premium is calculated based on the IDV (Insured Declared Value), "
        "which is essentially the current market value of the vehicle."
    ),
    "ncb_transfer": (
        "No Claim Bonus (NCB) in Motor insurance is a discount on the OD premium (20% to 50%). "
        "Crucially, NCB stays with the driver, not the car. You can transfer your NCB to a new car "
        "by obtaining an NCB Reserving Letter from your previous insurer."
    ),
    "zero_dep": (
        "Zero Depreciation (Nil Dep) add-on ensures the insurer pays for the full cost of replaced parts "
        "like plastic, rubber, and fiber without deducting depreciation. "
        "Standard policies deduct up to 50% for these parts."
    ),
    "cpa_cover": (
        "Compulsory Personal Accident (CPA) cover of ₹15 lakh is mandatory for the owner-driver. "
        "It provides compensation in case of accidental death or permanent disability while driving."
    ),
}

# ── Term Life Insurance (IRDAI Section 45) ───────────────────────────────

TERM = {
    "section_45": (
        "Under Section 45 of the Insurance Act, a life insurance policy cannot be called into question "
        "for any reason (including fraud or misstatement) after 3 years of the policy being in force. "
        "This provides absolute claim certainty for the family."
    ),
    "death_benefit": (
        "The sum assured is paid to the nominee. Under IRDAI rules, claims must be settled "
        "within 30 days. If an investigation is required, it must be completed within 90 days."
    ),
    "grace_period": (
        "For annual/half-yearly/quarterly premiums, the grace period is 30 days. "
        "For monthly premiums, it is 15 days. The policy remains fully active during this time."
    ),
    "suicide_clause": (
        "If the insured commits suicide within 12 months of the policy start date or revival, "
        "the insurer pays 80% of the premiums paid. Full sum assured is payable after 12 months."
    ),
}

# ── General Rules ─────────────────────────────────────────────────────────

GENERAL = {
    "free_look": (
        "You have a 15-day Free Look Period (30 days if bought online) from the date of receiving "
        "the policy document to review the terms. You can cancel for a full refund minus stamp duty and medical costs."
    ),
    "ombudsman": (
        "If the insurer rejects a claim, you can approach the Insurance Ombudsman if the claim "
        "is up to ₹30 lakh. Their decision is binding on the insurer but not on the policyholder."
    ),
    "kyc": (
        "KYC is mandatory for all insurance purchases. Valid documents include PAN, "
        "Aadhaar (masked/E-Aadhaar), Passport, or Driving License."
    ),
}

# ── Mapping & Logic ───────────────────────────────────────────────────────

_ALL_REGULATIONS = {
    "health": HEALTH,
    "motor": MOTOR,
    "term": TERM,
    "general": GENERAL
}

_KEYWORD_MAP = [
    ("three years", "term", "section_45"),
    ("3 years", "term", "section_45"),
    ("cannot reject", "term", "section_45"),
    ("submit", "term", "death_benefit"),
    ("something happens", "term", "death_benefit"),
    ("how to claim", "term", "death_benefit"),
    ("waiting", "health", "waiting_period"),
    ("moratorium", "health", "moratorium_period"),
    ("cashless", "health", "cashless_anywhere"),
    ("room rent", "health", "room_rent"),
    ("ncb", "motor", "ncb_transfer"),
    ("third party", "motor", "third_party"),
    ("zero dep", "motor", "zero_dep"),
    ("section 45", "term", "section_45"),
    ("grace", "term", "grace_period"),
    ("free look", "general", "free_look"),
    ("ombudsman", "general", "ombudsman"),
    ("kyc", "general", "kyc"),
]

async def _lookup(topic: str) -> str:
    t = topic.lower().strip()

    # 1. First, check our specific Keyword Map (The most reliable way)
    for keyword, category, key in _KEYWORD_MAP:
        if keyword in t:
            return _ALL_REGULATIONS[category][key]

    # 2. If no keyword, check if the user just named a category
    for category, rules in _ALL_REGULATIONS.items():
        if category in t:
            # If they asked for a category + a specific rule (e.g. "health waiting")
            for rule_key, rule_text in rules.items():
                if rule_key.replace("_", " ") in t:
                    return rule_text
            # Otherwise return a summary of that category
            return f"Here are the general {category} rules: " + " ".join(list(rules.values())[:2])

    return (
        "I don't have a specific IRDAI regulation for that exact topic. "
        "However, generally, life insurance claims are governed by Section 45. "
        "Would you like me to connect you to a claim specialist?"
    )
@function_tool
async def get_regulation(topic: str) -> str:
    """
    Retrieves Indian insurance regulations and IRDAI rules for specific topics.
    Use this to answer questions about waiting periods, NCB, grace periods, or claim rules.
    """
    logger.info(f"Looking up Indian regulation for: {topic}")
    return await _lookup(topic)