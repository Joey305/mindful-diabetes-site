# Scientific figure audit — Required before publishing

**IMPORTANT:** Preserve the seven illustrated original PNGs as user-selected visual directions, but the artwork is NOT a validated reproduction of the published paper. Some images contain materially incorrect scientific labels or fabricated quantitative graphics.

| File / Figure | Status | Minimum safe correction |
|---|---|---|
| Fig 1 — whole-body insulin sensitivity | HOLD | Incorrect skeletal-muscle text ("Myokine of glucose uptake"). Correct to "Major site of insulin-stimulated glucose uptake" or similar. Keep organ anatomy conceptual. |
| Fig 2 — clamp | HOLD | AI typo "My value" must become "M value." Treat 90 mg/dL as a sample clamp target rather than a universal or study-specific reported figure. |
| Fig 3 — proteomics workflow | HOLD | Garbled label around 488 proteins ("488 Idemolild"). The three cohort sizes are 75, 43, 43; >8,000 proteins identified across workflows; 488 associations initially; 62 after broader adjustment. Do not imply 8,000 > 488 > 62 is a literal single-stage filtering pipeline across identical samples. |
| Fig 4 — organ network | REVIEW | Add visual note "Conceptual tissue associations; Human Protein Atlas inference". No proof of direct interorgan traffic for every depicted protein. |
| Fig 5 — exercise | **HOLD: CRITICAL** | Cohort was 43 men, not a woman. The displayed categorical bar heights and error bars are *invented*, not source-data measurements. Replace with a scientifically correct results panel, e.g. '43 men', '8 weeks HIIT', '30–40% higher M value', '22 significant protein changes'; use actual source data for any numerical bar chart. Do not patch merely the caption. |
| Fig 6 — prediction model | REVIEW | R²=0.73 and 0.49 describe independent 43-person validation; cross-validation R²=0.67. Label the comparison accordingly. |
| Fig 7 — disease-risk prediction | REVIEW | Values 0.86, 0.88 and 0.74 are C-indices for UKBB incident T2D discrimination, not personal disease risk probabilities. The protein model was comparable to, not better than, HbA1c for T2D. |

## Figure processing requirements

1. Do NOT replace the figures with the previously rejected slide-style infographic package.
2. Make surgical changes to the selected illustrations where possible, but do not let AI redraw verified numerical axes or labels without manual QA.
3. For source-data panels, reconstruct from the primary publication's downloadable source data, with unit labels, sample sizes and uncertainty shown accurately.
4. Use accurate MDInc branding and the user-supplied square MDI logo. Do not create a new invented leaf brand.
5. Captions should live in the article below each figure; avoid putting "Figure 1" / "Figure N" decorative labels into the artwork.
6. Use optimized WebP on page, retain originals, implement click-to-zoom for text-rich art. These portrait illustrations are taller than ideal for standard inline wide figures; consider responsive max-width and horizontal placement with text.
7. Obtain editorial approval for any redesigned figure and a separate hero image before live deployment.
