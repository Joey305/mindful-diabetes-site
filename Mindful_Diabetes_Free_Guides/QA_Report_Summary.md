# Revised Guides QA Summary

- Rebuilt from one canonical generator: `scripts/build_all_free_guides.py`.
- Explicit page specs and visual mappings are stored in each guide's `Editable_Source/source.json`.
- All PDFs were rendered at 200 DPI and contact sheets were generated.
- Footers use three fixed zones: organization, website, page number.
- PDF/UA tagging remains pending and is not claimed as complete.
- PyMuPDF was not available in this runtime; link/bookmark checks used `pypdf`, `pdfinfo`, and `pdffonts`.
