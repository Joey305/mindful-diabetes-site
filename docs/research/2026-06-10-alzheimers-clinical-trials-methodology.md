# June 10, 2026 Alzheimer’s Clinical-Trials Snapshot Methodology

Article slug: `alzheimers-clinical-trials-june-2026`

This methodology note documents the registry snapshot used for the Mindful Diabetes article dated June 10, 2026.

## Principal Registry Source

ClinicalTrials.gov API v2 was used as the principal registry source.

Retrieval timestamp: `2026-07-28T10:30:57+00:00`

Cutoff date: `2026-06-10`

API query:

```text
https://clinicaltrials.gov/api/v2/studies?query.cond=Alzheimer+Disease&filter.overallStatus=RECRUITING%2CNOT_YET_RECRUITING%2CACTIVE_NOT_RECRUITING%2CENROLLING_BY_INVITATION&pageSize=1000&format=json&countTotal=true
```

The local builder is:

```text
tools/build_alzheimers_trials_snapshot.py
```

## Files Created

```text
data/2026-06-10-alzheimers-clinical-trials.csv
data/2026-06-10-alzheimers-clinical-trials-excluded-after-cutoff.csv
data/2026-06-10-alzheimers-clinical-trials-summary.json
```

## Inclusion Rule

The broad snapshot includes ClinicalTrials.gov records that:

1. Were returned by `query.cond=Alzheimer Disease`.
2. Had an overall recruitment status of `RECRUITING`, `NOT_YET_RECRUITING`, `ACTIVE_NOT_RECRUITING`, or `ENROLLING_BY_INVITATION`.
3. Were deduplicated by NCT number.
4. Had `studyFirstPostDateStruct.date` on or before `2026-06-10`.
5. Had `lastUpdatePostDateStruct.date` on or before `2026-06-10`.

This is a conservative historical rule. ClinicalTrials.gov records can change after a date of interest. Records whose public status was updated after June 10, 2026 were not treated as reliable evidence of their June 10 status unless a historical record was separately reconstructed. For this article, no post-cutoff-updated records were added back manually.

## Exclusion Rule

Records were excluded from the headline snapshot if:

1. The study was first posted after June 10, 2026.
2. The study was first posted on or before June 10, 2026 but the public record’s latest update was posted after June 10, 2026, making its exact June 10 status unreconstructed in this workflow.

Excluded records are preserved in:

```text
data/2026-06-10-alzheimers-clinical-trials-excluded-after-cutoff.csv
```

## Count Summary

ClinicalTrials.gov active-status records returned before cutoff filtering: `1,067`

Deduplicated current active-status records returned by the API: `1,067`

Broad June 10 snapshot total: `878`

Excluded records: `189`

Excluded records by reason:

| Reason | Records |
| --- | ---: |
| Last public update posted after June 10, 2026; historical status not reconstructed | 146 |
| First posted after June 10, 2026 | 43 |

## Participation-Now Subset

The participation-now subset includes broad-snapshot records that:

1. Had status `RECRUITING`, `NOT_YET_RECRUITING`, or `ENROLLING_BY_INVITATION`.
2. Had at least one public location entry.

Participation-now subset total: `671`

This subset is meant to approximate the records a reader might reasonably begin exploring through a public registry, not to determine personal eligibility.

## Status Counts

| Recruitment status | Studies |
| --- | ---: |
| Recruiting | 516 |
| Not yet recruiting | 164 |
| Active, not recruiting | 137 |
| Enrolling by invitation | 61 |

## Study Type Counts

| Study type | Studies |
| --- | ---: |
| Interventional | 592 |
| Observational | 286 |

## Phase Counts

| Phase value | Studies |
| --- | ---: |
| Not applicable to an interventional phase (`NA`) | 372 |
| Observational / not applicable | 286 |
| Phase 2 | 81 |
| Phase 1 | 45 |
| Phase 3 | 34 |
| Phase 1/2 | 19 |
| Early Phase 1 | 17 |
| Phase 4 | 15 |
| Phase 2/3 | 9 |

## Category Counts

Categories were assigned by transparent keyword heuristics from titles, conditions, descriptions, intervention names, intervention types, and primary purpose fields. These categories are for reader orientation and should not be treated as regulatory classifications.

| Category | Studies |
| --- | ---: |
| Diagnostics, imaging, and biomarkers | 378 |
| Care, behavior, and quality of life | 282 |
| Other interventional treatment research | 72 |
| Lifestyle and multidomain | 48 |
| Devices and brain stimulation | 34 |
| Amyloid-targeting approaches | 22 |
| Tau-targeting approaches | 13 |
| Synapses and neuronal communication | 9 |
| Other Alzheimer clinical studies | 7 |
| Vascular and blood-brain barrier | 6 |
| Neuroinflammation and immune biology | 4 |
| Metabolism, insulin signaling, and cellular energy | 3 |

## Participant Stage Counts

| Participant stage | Studies |
| --- | ---: |
| MCI or prodromal Alzheimer’s | 224 |
| Care partners or care systems | 222 |
| Mixed or not specified | 149 |
| Moderate or later dementia | 123 |
| Preclinical or elevated-risk | 112 |
| Subjective cognitive concerns | 26 |
| Early Alzheimer’s disease | 15 |
| Mild Alzheimer’s dementia | 7 |

## Geography Counts

Study counts are unique-study counts. Location-entry counts count public location records listed inside included ClinicalTrials.gov records. A single public location entry does not mean broad national access.

Top countries by unique included studies:

| Country | Unique studies |
| --- | ---: |
| United States | 350 |
| China | 111 |
| France | 73 |
| Canada | 56 |
| Spain | 48 |
| Italy | 47 |
| United Kingdom | 32 |
| South Korea | 19 |
| Taiwan | 19 |
| Australia | 18 |

Top countries by public location entries:

| Country | Location entries |
| --- | ---: |
| United States | 2,331 |
| China | 542 |
| Japan | 247 |
| Canada | 202 |
| France | 179 |
| Spain | 144 |
| United Kingdom | 126 |
| Italy | 106 |
| South Korea | 94 |
| Germany | 84 |

Regional study counts:

| Region | Unique studies | Location entries |
| --- | ---: | ---: |
| North America | 408 | 2,535 |
| Europe | 317 | 926 |
| East Asia | 174 | 926 |
| Asia-Pacific | 24 | 83 |
| Latin America | 12 | 22 |
| Middle East | 12 | 20 |
| Other/unspecified region | 27 | 66 |

Additional geography fields:

| Field | Count |
| --- | ---: |
| Included studies with at least one United States site | 350 |
| Included studies with listed sites outside the United States and no United States site | 458 |
| Included multinational studies | 41 |
| Included studies with public location entries | 808 |

## Representative Records Used in the Article

Representative NCT records were selected to illustrate major research questions rather than to promote sponsors or suggest personal eligibility.

```text
NCT03887455
NCT04468659
NCT05026866
NCT06268886
NCT06602258
NCT04098666
NCT07200622
NCT05983575
NCT06595511
NCT06122415
NCT05397639
NCT06852326
```

## Limitations

ClinicalTrials.gov is a public registry, not a complete picture of every Alzheimer’s study worldwide. It may omit studies registered elsewhere, include records with incomplete locations, and contain records whose sponsor-updated fields lag behind real-world site activity.

The snapshot is intentionally conservative. It excludes records updated after June 10, 2026 because their current status on July 28, 2026 may not reflect their June 10 status. This avoids presenting post-cutoff information as historical fact, but it may undercount some studies that truly were active on June 10.

The query focused on `Alzheimer Disease`. It did not automatically merge all dementia, cognitive impairment, neurodegeneration, or ADRD records into the headline total. Some records include Alzheimer’s disease together with related dementias or care-partner populations; these were retained when ClinicalTrials.gov returned them under the Alzheimer Disease condition query.

Category and participant-stage assignments are heuristic and intended for editorial explanation. The raw registry fields remain available in the CSV.
