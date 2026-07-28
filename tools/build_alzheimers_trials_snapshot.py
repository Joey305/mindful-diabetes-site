#!/usr/bin/env python3
"""Build a conservative June 10, 2026 Alzheimer clinical-trials snapshot."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


CUTOFF = "2026-06-10"
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
QUERY = {
    "query.cond": "Alzheimer Disease",
    "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION",
    "pageSize": "1000",
    "format": "json",
    "countTotal": "true",
}
OUT_DIR = Path("data")
CSV_PATH = OUT_DIR / "2026-06-10-alzheimers-clinical-trials.csv"
EXCLUDED_PATH = OUT_DIR / "2026-06-10-alzheimers-clinical-trials-excluded-after-cutoff.csv"
SUMMARY_PATH = OUT_DIR / "2026-06-10-alzheimers-clinical-trials-summary.json"


def fetch_all_studies() -> tuple[list[dict], int]:
    studies = []
    page_token = ""
    total = 0

    while True:
        params = dict(QUERY)
        if page_token:
            params["pageToken"] = page_token
        url = f"{BASE_URL}?{urlencode(params)}"
        with urlopen(url, timeout=60) as response:
            payload = json.load(response)

        total = payload.get("totalCount", total)
        studies.extend(payload.get("studies", []))
        page_token = payload.get("nextPageToken", "")
        if not page_token:
            return studies, total


def get_path(value: dict, *path, default=None):
    current = value
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def post_date(status_module: dict, field: str) -> str:
    return get_path(status_module, field, "date", default="")


def before_or_on(value: str, cutoff: str = CUTOFF) -> bool:
    return bool(value) and value <= cutoff


def normalize_phase(phases: list[str]) -> str:
    if not phases:
        return "NOT_APPLICABLE"
    if len(phases) == 1:
        return phases[0]
    return "+".join(phases)


def text_blob(*parts) -> str:
    chunks = []
    for part in parts:
        if isinstance(part, str):
            chunks.append(part)
        elif isinstance(part, list):
            chunks.extend(str(item) for item in part)
    return " ".join(chunks).lower()


def intervention_names(study: dict) -> list[str]:
    interventions = get_path(study, "protocolSection", "armsInterventionsModule", "interventions", default=[])
    return [item.get("name", "") for item in interventions]


def intervention_types(study: dict) -> list[str]:
    interventions = get_path(study, "protocolSection", "armsInterventionsModule", "interventions", default=[])
    return [item.get("type", "") for item in interventions]


def classify_category(study: dict) -> str:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    desc = protocol.get("descriptionModule", {})
    conditions = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    interventions = intervention_names(study)
    intervention_type_values = intervention_types(study)
    blob = text_blob(
        ident.get("briefTitle", ""),
        ident.get("officialTitle", ""),
        desc.get("briefSummary", ""),
        desc.get("detailedDescription", ""),
        conditions.get("conditions", []),
        conditions.get("keywords", []),
        interventions,
        intervention_type_values,
        design.get("designInfo", {}).get("primaryPurpose", ""),
    )

    if any(term in blob for term in ["caregiver", "care partner", "burden", "agitation", "quality of life", "daily function", "sleep disturbance", "behavioral symptoms"]):
        return "Care, behavior, and quality of life"
    if any(term in blob for term in ["biomarker", "pet", "mri", "blood test", "plasma", "cerebrospinal", "csf", "retinal", "speech", "gait", "wearable", "diagnostic", "imaging"]):
        if not any(term in blob for term in ["amyloid antibody", "lecanemab", "donanemab", "gantenerumab", "remternetug"]):
            return "Diagnostics, imaging, and biomarkers"
    if any(term in blob for term in ["exercise", "diet", "sleep", "cognitive training", "multidomain", "lifestyle", "social engagement", "nutrition", "physical activity"]):
        return "Lifestyle and multidomain"
    if any(term in blob for term in ["stimulation", "ultrasound", "transcranial", "gamma", "40 hz", "device", "neuromodulation", "light and sound", "sensory"]):
        return "Devices and brain stimulation"
    if any(term in blob for term in ["vascular", "blood pressure", "hypertension", "blood-brain barrier", "cerebral blood flow", "small vessel", "angiopathy"]):
        return "Vascular and blood-brain barrier"
    if any(term in blob for term in ["glp-1", "semaglutide", "liraglutide", "insulin", "metformin", "ketone", "metabolic", "mitochondria", "mitochondrial", "glucose", "lipid"]):
        return "Metabolism, insulin signaling, and cellular energy"
    if any(term in blob for term in ["synapse", "synaptic", "neurotransmitter", "receptor", "neurotrophic", "neuroregeneration", "excitat"]):
        return "Synapses and neuronal communication"
    if any(term in blob for term in ["microglia", "astrocyte", "inflammation", "inflammatory", "immune", "trem2", "complement", "cytokine"]):
        return "Neuroinflammation and immune biology"
    if any(term in blob for term in ["tau", "anti-tau", "tauopathy"]):
        return "Tau-targeting approaches"
    if any(term in blob for term in ["amyloid", "lecanemab", "donanemab", "gantenerumab", "remternetug", "solanezumab", "aducanumab", "bace"]):
        return "Amyloid-targeting approaches"
    if intervention_type_values:
        return "Other interventional treatment research"
    return "Other Alzheimer clinical studies"


def classify_stage(study: dict) -> str:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    desc = protocol.get("descriptionModule", {})
    elig = protocol.get("eligibilityModule", {})
    conditions = protocol.get("conditionsModule", {})
    blob = text_blob(
        ident.get("briefTitle", ""),
        ident.get("officialTitle", ""),
        desc.get("briefSummary", ""),
        elig.get("eligibilityCriteria", ""),
        elig.get("studyPopulation", ""),
        conditions.get("conditions", []),
        conditions.get("keywords", []),
    )

    if any(term in blob for term in ["caregiver", "care partner", "informal carer"]):
        return "Care partners or care systems"
    if any(term in blob for term in ["preclinical", "cognitively unimpaired", "asymptomatic", "at risk", "genetic risk", "down syndrome"]):
        return "Preclinical or elevated-risk"
    if any(term in blob for term in ["subjective cognitive"]):
        return "Subjective cognitive concerns"
    if any(term in blob for term in ["mild cognitive impairment", "mci", "prodromal"]):
        return "MCI or prodromal Alzheimer’s"
    if any(term in blob for term in ["early alzheimer", "early-stage", "early stage"]):
        return "Early Alzheimer’s disease"
    if any(term in blob for term in ["moderate", "severe", "advanced"]):
        return "Moderate or later dementia"
    if any(term in blob for term in ["mild dementia", "mild alzheimer"]):
        return "Mild Alzheimer’s dementia"
    return "Mixed or not specified"


def countries_for(study: dict) -> list[str]:
    locations = get_path(study, "protocolSection", "contactsLocationsModule", "locations", default=[])
    return sorted({loc.get("country", "") for loc in locations if loc.get("country")})


def location_count(study: dict) -> int:
    return len(get_path(study, "protocolSection", "contactsLocationsModule", "locations", default=[]))


def nct_url(nct_id: str) -> str:
    return f"https://clinicaltrials.gov/study/{nct_id}"


def flatten(study: dict, excluded_reason: str = "") -> dict:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    outcomes = protocol.get("outcomesModule", {})
    conditions = protocol.get("conditionsModule", {})
    contacts_locations = protocol.get("contactsLocationsModule", {})
    nct_id = ident.get("nctId", "")
    countries = countries_for(study)
    primary_outcomes = outcomes.get("primaryOutcomes", [])

    return {
        "nct_id": nct_id,
        "url": nct_url(nct_id),
        "brief_title": ident.get("briefTitle", ""),
        "official_title": ident.get("officialTitle", ""),
        "overall_status": status.get("overallStatus", ""),
        "study_type": design.get("studyType", ""),
        "phase": normalize_phase(design.get("phases", [])),
        "primary_purpose": design.get("designInfo", {}).get("primaryPurpose", ""),
        "category": classify_category(study),
        "participant_stage": classify_stage(study),
        "enrollment": get_path(design, "enrollmentInfo", "count", default=""),
        "lead_sponsor": get_path(sponsor, "leadSponsor", "name", default=""),
        "interventions": "; ".join(intervention_names(study)),
        "conditions": "; ".join(conditions.get("conditions", [])),
        "countries": "; ".join(countries),
        "has_us_site": "United States" in countries,
        "country_count": len(countries),
        "location_count": location_count(study),
        "multinational": len(countries) > 1,
        "has_public_locations": bool(contacts_locations.get("locations")),
        "study_first_post_date": post_date(status, "studyFirstPostDateStruct"),
        "last_update_post_date": post_date(status, "lastUpdatePostDateStruct"),
        "start_date": get_path(status, "startDateStruct", "date", default=""),
        "primary_completion_date": get_path(status, "primaryCompletionDateStruct", "date", default=""),
        "completion_date": get_path(status, "completionDateStruct", "date", default=""),
        "primary_outcomes": "; ".join(item.get("measure", "") for item in primary_outcomes[:3]),
        "excluded_reason": excluded_reason,
    }


def counter_dict(counter: Counter) -> dict:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def top_counter_dict(counter: Counter, limit: int) -> dict:
    return dict(counter.most_common(limit))


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    studies, api_total = fetch_all_studies()
    deduped = {get_path(study, "protocolSection", "identificationModule", "nctId"): study for study in studies}
    deduped.pop(None, None)

    included = []
    excluded = []
    for study in deduped.values():
        status = get_path(study, "protocolSection", "statusModule", default={})
        first_post = post_date(status, "studyFirstPostDateStruct")
        last_update = post_date(status, "lastUpdatePostDateStruct")
        if not before_or_on(first_post):
            excluded.append(flatten(study, "First posted after June 10, 2026"))
        elif not before_or_on(last_update):
            excluded.append(flatten(study, "Last public update posted after June 10, 2026; historical status not reconstructed"))
        else:
            included.append(flatten(study))

    fieldnames = list(flatten(next(iter(deduped.values()))).keys())
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(included, key=lambda item: item["nct_id"]))

    with EXCLUDED_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(excluded, key=lambda item: item["nct_id"]))

    participation_statuses = {"RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"}
    participation_now = [
        item for item in included if item["overall_status"] in participation_statuses and item["has_public_locations"]
    ]
    country_locations = Counter()
    country_studies = Counter()
    region_locations = Counter()
    region_studies = Counter()
    regions = {
        "United States": "North America",
        "Canada": "North America",
        "Mexico": "North America",
        "Brazil": "Latin America",
        "Argentina": "Latin America",
        "Chile": "Latin America",
        "Colombia": "Latin America",
        "Peru": "Latin America",
        "United Kingdom": "Europe",
        "France": "Europe",
        "Germany": "Europe",
        "Spain": "Europe",
        "Italy": "Europe",
        "Netherlands": "Europe",
        "Sweden": "Europe",
        "Denmark": "Europe",
        "Norway": "Europe",
        "Finland": "Europe",
        "Belgium": "Europe",
        "Poland": "Europe",
        "Switzerland": "Europe",
        "Austria": "Europe",
        "Ireland": "Europe",
        "Portugal": "Europe",
        "Czechia": "Europe",
        "Czech Republic": "Europe",
        "Russia": "Europe",
        "China": "East Asia",
        "Japan": "East Asia",
        "South Korea": "East Asia",
        "Korea, Republic of": "East Asia",
        "Taiwan": "East Asia",
        "Hong Kong": "East Asia",
        "Singapore": "Asia-Pacific",
        "Australia": "Asia-Pacific",
        "New Zealand": "Asia-Pacific",
        "Israel": "Middle East",
        "Turkey": "Middle East",
        "Turkey (Türkiye)": "Middle East",
        "South Africa": "Africa",
    }
    for item in included:
        countries = [country for country in item["countries"].split("; ") if country]
        for country in countries:
            country_studies[country] += 1
            region = regions.get(country, "Other/unspecified region")
            region_studies[region] += 1

    included_ncts = {item["nct_id"] for item in included}
    for study in deduped.values():
        nct_id = get_path(study, "protocolSection", "identificationModule", "nctId", default="")
        if nct_id not in included_ncts:
            continue
        locations = get_path(study, "protocolSection", "contactsLocationsModule", "locations", default=[])
        for location in locations:
            country = location.get("country")
            if not country:
                continue
            country_locations[country] += 1
            region = regions.get(country, "Other/unspecified region")
            region_locations[region] += 1

    summary = {
        "retrieved_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "cutoff_date": CUTOFF,
        "clinicaltrials_api_url": f"{BASE_URL}?{urlencode(QUERY)}",
        "api_total_before_cutoff_filter": api_total,
        "deduplicated_current_active_records": len(deduped),
        "broad_snapshot_total": len(included),
        "excluded_after_cutoff_or_first_post": len(excluded),
        "participation_now_subset_total": len(participation_now),
        "definition": (
            "ClinicalTrials.gov records returned by query.cond=Alzheimer Disease and active recruitment "
            "statuses, deduplicated by NCT number, first posted on or before 2026-06-10, and with the current "
            "public record last updated on or before 2026-06-10."
        ),
        "participation_now_definition": (
            "Included snapshot records with overall status RECRUITING, NOT_YET_RECRUITING, or "
            "ENROLLING_BY_INVITATION and at least one public location entry."
        ),
        "status_counts": counter_dict(Counter(item["overall_status"] for item in included)),
        "study_type_counts": counter_dict(Counter(item["study_type"] for item in included)),
        "phase_counts": counter_dict(Counter(item["phase"] for item in included)),
        "category_counts": counter_dict(Counter(item["category"] for item in included)),
        "participant_stage_counts": counter_dict(Counter(item["participant_stage"] for item in included)),
        "has_us_site_count": sum(1 for item in included if item["has_us_site"]),
        "outside_us_site_count": sum(1 for item in included if item["countries"] and not item["has_us_site"]),
        "multinational_study_count": sum(1 for item in included if item["multinational"]),
        "with_public_locations_count": sum(1 for item in included if item["has_public_locations"]),
        "top_countries_by_unique_studies": top_counter_dict(country_studies, 20),
        "top_countries_by_location_entries": top_counter_dict(country_locations, 20),
        "region_counts_by_unique_studies": counter_dict(region_studies),
        "region_counts_by_location_entries": counter_dict(region_locations),
        "sample_featured_ncts": [
            "NCT03887455",
            "NCT04468659",
            "NCT05026866",
            "NCT06268886",
            "NCT06602258",
            "NCT04098666",
            "NCT07200622",
            "NCT05983575",
            "NCT06595511",
            "NCT06122415",
            "NCT05397639",
            "NCT06852326",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
