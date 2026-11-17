from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import csv,json,shutil,textwrap
base=Path('/mnt/data/MDI_Plasma_Proteomics_Nov2026_Handoff')
assets=base/'assets'/'visual_drafts'
assets.mkdir(parents=True, exist_ok=True)
figs=[
 (1,'Whole-Body Insulin Resistance','whole_body_insulin_resistance_infographic.png','Whole-body insulin resistance illustration','Conceptual anatomy of insulin response across pancreas, liver, skeletal muscle and fat tissue.','HOLD','Muscle label contains a wrong phrase (“Myokine of glucose uptake”); replace with accurate glucose-uptake physiology.'),
 (2,'Clamp Method','mindful_diabetes_measuring_insulin_sensitivity.png','Hyperinsulinaemic–euglycaemic clamp illustration','Participant receives insulin and glucose infusions during a monitored research clamp.','HOLD','Typo in lower M-value panel (“My value”). Use “M value”; glucose target in artwork is illustrative, not universal or a reported protocol parameter.'),
 (3,'Plasma Proteomics Pipeline','protein_fingerprint_study_design.png','Blood plasma proteomics and study-cohort diagram','Illustration of plasma sampling, proteomics, cohort structure and associated-protein counts.','HOLD','Garbled 488-count text in cohort panel (appears “488 Idemolild”); must correct. ~8,000 across workflows, 488 discovery-associated and 62 adjusted are verified.'),
 (4,'Tissue Origin Network','the_molecular_conversation_between_organs.png','Conceptual circulating protein and tissue association diagram','Illustrated liver, fat, muscle and immune contributions to protein signals in blood.','CONCEPTUAL_REVIEW','Arrows suggest organ-to-blood secretion directly demonstrated in the patients. Caption must state tissue origins were inferred from Human Protein Atlas transcriptomics.'),
 (5,'Exercise Proteomic Changes','mindful_diabetes_exercise_transforms_blood_protei.png','Eight-week training and plasma proteomic response illustration','Exercise image and a purported example panel of protein abundance changes.','HOLD_CRITICAL','Study cohort was 43 men but artwork depicts woman. Bars and error bars are not matched to source-data protein measurements. Replace figure; do not publish fabricated plot.'),
 (6,'13-Protein Model','from_proteins_to_insulin_sensitivity.png','Insulin sensitivity prediction model inputs and validation accuracy','13 proteins plus sex, HbA1c and TG/HDL ratio, with R squared 0.73 versus 0.49.','CONCEPTUAL_REVIEW','Label these values explicitly as independent 43-person validation R². The all-cohort cross-validated R² was 0.67.'),
 (7,'Disease Risk Prediction','protein_model_predicts_diabetes_risk.png','Type 2 diabetes risk C-index comparison','C-index for predicted insulin-sensitivity score 0.86, HbA1c 0.88 and TG/HDL 0.74.','CONCEPTUAL_REVIEW','Display as discriminatory C-index in UK Biobank, not individual risk probability; confirm the source-data and units before publishing.'),
]
rows=[]
for n,title,src,alt,desc,status,issue in figs:
 p=Path('/mnt/data')/src
 if not p.exists(): raise FileNotFoundError(p)
 png_name=f'Fig_{n:02d}_{title.replace(" ","_").replace("-","_")}_DRAFT.png'
 out=assets/png_name
 shutil.copy2(p,out)
 with Image.open(out) as im:
  im.convert('RGB').save(assets/png_name.replace('.png','.webp'),'WEBP',quality=88,method=6)
  w,h=im.size
 rows.append({'figure_number':n,'figure_name':title,'png_path':str(out.relative_to(base)),'webp_path':str((assets/png_name.replace('.png','.webp')).relative_to(base)),'original_resolution':f'{w}x{h}','alt_text':alt,'caption_subject':desc,'release_status':status,'scientific_issue':issue})
logo=Path('/mnt/data/MDI_Logo(4).jpg')
if logo.exists():
 (base/'brand').mkdir(exist_ok=True)
 shutil.copy2(logo,base/'brand'/'MDI_Logo_Original.jpg')
# contact sheet, unmodified previews on neutral backdrop
pw,ph=300,385
sheet=Image.new('RGB',(pw*4+80,ph*2+100),'#f7f4ec')
d=ImageDraw.Draw(sheet)
for idx,row in enumerate(rows):
 with Image.open(base/row['png_path']) as im:
  im=im.convert('RGB'); im.thumbnail((pw-18,ph-44))
  x=20+(idx%4)*pw+(pw-im.width)//2
  y=24+(idx//4)*ph
  sheet.paste(im,(x,y))
  d.text((20+(idx%4)*pw+12,y+im.height+7),f'{idx+1}. {row["figure_name"][:29]}',fill='#173f38')
  d.text((20+(idx%4)*pw+12,y+im.height+23),row['release_status'],fill='#b25b38')
sheet.save(base/'preview'/'figure_contact_sheet.jpg',quality=90)
# figure metadata
with (base/'metadata'/'figure_manifest.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(base/'metadata'/'figure_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
seo={
 'article_title':'Your Blood Has a Hidden Protein Fingerprint. Could It Reveal Insulin Resistance?',
 'seo_title':'Blood Protein Fingerprint of Insulin Resistance | MDI',
 'meta_description':'A November 2026 Nature Metabolism study linked 488 blood proteins to insulin sensitivity, exercise and disease risk. Explore what the findings mean.',
 'dek':'A new study maps circulating proteins linked to insulin sensitivity and develops a 13-protein model. Here is what the science really shows.',
 'suggested_slug':'blood-protein-fingerprint-insulin-resistance-2026',
 'canonical_url_suggestion':'https://mindfuldiabetes.org/blood-protein-fingerprint-insulin-resistance-2026/',
 'byline':'Use the site’s existing editorial/byline convention; do not invent credentials',
 'date_published':'Set from actual production deployment; do not backdate',
 'primary_paper_published':'2026-11-16',
 'categories':['Research & Updates','Metabolic Health','Diabetes Science'],
 'tags':['insulin resistance','proteomics','blood proteins','exercise','precision medicine','metabolism','HbA1c','biomarkers'],
 'article_type':'NewsArticle or Article according to site conventions',
 'og_image':'REQUIRES NEW APPROVED HERO: do not automatically use a figure or stale holiday food photo',
 'cover_image':'REQUIRES EDITORIAL APPROVAL',
 'reading_level':'educated general audience, define technical terms in context',
 'language':'en-US',
 'primary_reference':'https://doi.org/10.1038/s42255-026-01662-1',
 'figure_status':'Visual drafts only; HOLD figures 1, 2, 3 and 5 for scientific corrections'
}
(base/'metadata'/'seo.json').write_text(json.dumps(seo,ensure_ascii=False,indent=2))
(base/'metadata'/'editorial_extras.md').write_text('''# Mindful Diabetes — Supporting Editorial Material\n\n## Blog card teaser\n\nA brand-new Nature Metabolism study identified hundreds of blood proteins associated with insulin sensitivity—and tested whether a smaller protein signature could predict metabolic risk. Learn how the experiment worked, what exercise changed, and why this is not yet a clinical blood test.\n\n## Memovela blurb\n\n**Your blood carries a molecular conversation.** New research suggests circulating protein patterns can help scientists understand insulin sensitivity across multiple organs. Explore how exercise, adipose signaling, glucose measures, and emerging biomarker models fit together—then use Memovela to keep track of the everyday habits you can actually observe. Memovela does not measure protein biomarkers or diagnose insulin resistance.\n\n## Suggested newsletter hook\n\n**Could a blood sample reveal metabolic changes that glucose tests don't show?** A study published just yesterday profiled more than 8,000 proteins and uncovered a 13-protein model linked to insulin sensitivity. This week, we're decoding the experiment—not selling a futuristic blood test.\n\n## Short research social teaser\n\nResearchers measured insulin sensitivity in 161 people, profiled thousands of circulating proteins, and developed a model using 13 proteins plus routine clinical data. It's early research, not a medical test you can order today. The bigger question: what can blood proteins tell us about metabolism?\n\n## Recommended context links\n\n- https://mindfuldiabetes.org/ultra-processed-foods-same-calories-insulin-2026/\n- https://mindfuldiabetes.org/your-body-is-talking-every-time-you-move/\n- https://mindfuldiabetes.org/fat-cells-store-release-energy-2026/\n- https://mindfuldiabetes.org/same-meal-different-glucose-response/\n- https://mindfuldiabetes.org/dash-diet/\n- https://mindfuldiabetes.org/metabolic-syndrome-midlife-brain-2026/\n''')
print('Copied and indexed',len(rows),'figure drafts')
