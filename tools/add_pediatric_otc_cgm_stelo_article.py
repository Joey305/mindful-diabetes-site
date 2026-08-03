#!/usr/bin/env python3
"""Add the August 3, 2026 pediatric OTC CGM Stelo article to the content seed."""

from __future__ import annotations

import json
from pathlib import Path


CONTENT_PATH = Path("mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json")
IMAGE_BRIEF_PATH = Path("docs/blog-image-briefs/2026-08-03-pediatric-otc-cgm-stelo.md")
SOURCE_NOTE_PATH = Path("docs/research/2026-08-03-pediatric-otc-cgm-stelo-sources.md")


TITLE = "The First Over-the-Counter CGM for Children: What Families Should Know About Stelo"
SLUG = "otc-cgm-children-stelo-family-guide"
DATE = "2026-08-03 09:00:00"
URL = f"https://mindfuldiabetes.org/{SLUG}/"
SEO_TITLE = "OTC CGM for Children: What Families Should Know About Stelo"
META_DESCRIPTION = (
    "The FDA has cleared Stelo for children age two and older who do not use insulin. Learn who it is "
    "for, what it measures, its safety limits, and why it cannot diagnose diabetes."
)
EXCERPT = (
    "The FDA has cleared the first over-the-counter continuous glucose monitor for children as young "
    "as two who do not use insulin. Here is what Stelo can show families, who should not use it, "
    "and why sensor trends cannot replace a diabetes diagnosis or medical care."
)


IMAGES = [
    {
        "slot": "hero",
        "filename": "pediatric-otc-cgm-family-guide-2026.webp",
        "width": 1600,
        "height": 900,
        "alt": "A child wearing a small upper-arm glucose sensor sits with a caregiver and pediatric clinician reviewing a phone in a calm clinic room.",
        "title": "Family discussion about pediatric OTC CGM use",
        "description": "Hero image for a Mindful Diabetes article about the first FDA-cleared over-the-counter CGM for children who do not use insulin.",
        "caption": "The most useful glucose data begins with a shared question, a child’s context, and a clinician who can help interpret what the numbers mean.",
        "placement": "Hero image at the top of the article.",
        "prompt": "Warm pediatric-clinic scene showing a child, caregiver, and pediatric clinician discussing glucose information together. The child may have a small sensor on the back of the upper arm. A phone displays a subtle, generic glucose trend without warnings, fake medical recommendations, or identifiable commercial-interface elements. Shared decision-making, not product promotion. No logos, insulin pump, injection, emergency low alert, or fake claims.",
        "loading": "lazy",
    },
    {
        "slot": "how-it-works",
        "filename": "stelo-child-caregiver-glucose-trends.webp",
        "width": 1400,
        "height": 788,
        "alt": "A caregiver shows a child wearing an upper-arm glucose sensor a phone with a simple trend line near breakfast, sports gear, and a bedroom.",
        "title": "Child and caregiver reviewing glucose trends",
        "description": "Supporting image for a section explaining how an OTC glucose biosensor can show repeated interstitial glucose trends during ordinary routines.",
        "caption": "A sensor can make patterns visible, but the pattern still needs context: meals, movement, illness, sleep, symptoms, and the question the family is trying to answer.",
        "placement": "After the section explaining what Stelo is designed to do.",
        "prompt": "Warm editorial realism image showing a child wearing a small upper-arm sensor, a caregiver holding a smartphone with a simple generic glucose trend, subtle flow from interstitial glucose beneath skin to trend, and ordinary daily-life elements such as a meal, outdoor activity, and sleep. No product UI, diagnosis, logos, alerts, insulin pump, injection, or food shame.",
        "loading": "lazy",
    },
    {
        "slot": "diagnosis",
        "filename": "cgm-trends-versus-diabetes-diagnosis.webp",
        "width": 1400,
        "height": 788,
        "alt": "A split scene shows a family reviewing a home glucose trend on one side and a clinician reviewing laboratory test results on the other.",
        "title": "Glucose trends and diagnostic testing are different",
        "description": "Supporting image for a section distinguishing consumer glucose trend data from formal laboratory diagnosis of diabetes or prediabetes.",
        "caption": "A home trend can help a conversation start. Diagnosis still depends on clinical evaluation and validated testing.",
        "placement": "At the beginning of the section on glucose trends and diabetes diagnosis.",
        "prompt": "Balanced split-scene illustration: family reviewing a glucose trend at home on one side, clinician reviewing laboratory blood-test results in a medical setting on the other. Reinforce that home glucose patterns and formal diagnostic evaluation are different kinds of information. No thresholds, logos, pump, injection, alarms, or embedded text.",
        "loading": "lazy",
    },
    {
        "slot": "right-tool",
        "filename": "who-should-use-pediatric-otc-cgm.webp",
        "width": 1400,
        "height": 788,
        "alt": "A pediatric clinician discusses different glucose monitoring options with two families seated together in a warm clinic room.",
        "title": "Choosing the right glucose monitoring tool",
        "description": "Supporting image for sections explaining who might discuss pediatric OTC CGM use with a clinician and who needs a different monitoring system.",
        "caption": "The question is not whether one monitor is universally better. The question is whether the tool matches the child’s medical situation.",
        "placement": "Between the appropriate-use and not-designed-for sections.",
        "prompt": "Pediatric clinician discussing different monitoring options with two families. One pathway shows an alert-free OTC biosensor for a child who does not use insulin. Another shows a clinician-directed monitoring pathway for a child who requires insulin and safety support. Respectful, no red rejection symbol, no brand logos, no insulin pump, no injection, no alarm text.",
        "loading": "lazy",
    },
    {
        "slot": "emotional-health",
        "filename": "cgm-data-anxiety-eating-behavior-families.webp",
        "width": 1400,
        "height": 788,
        "alt": "An adolescent and caregiver calmly review a phone together while a family meal continues in the background.",
        "title": "Healthy family boundaries around glucose data",
        "description": "Supporting image for sections on data anxiety, family communication, and eating-disorder considerations when children use glucose monitoring.",
        "caption": "Glucose data can support awareness, but it should not become a way to police food, body size, or every ordinary fluctuation.",
        "placement": "Before the anxiety and eating-disorder considerations.",
        "prompt": "Adolescent and caregiver reviewing a phone together in a calm home setting. Thoughtful communication and healthy boundaries. Normal family meal in background without portraying foods as dangerous. No body-image imagery, scales, calorie counts, food restriction, logos, insulin pump, injection, emergency alert, or text.",
        "loading": "lazy",
    },
    {
        "slot": "questions",
        "filename": "questions-before-child-uses-cgm.webp",
        "width": 1400,
        "height": 788,
        "alt": "A caregiver, child, and pediatric clinician talk at a clinic table with a notebook, phone, and small unbranded sensor package nearby.",
        "title": "Questions before a child uses an OTC CGM",
        "description": "Supporting image for practical family and clinician questions before using an over-the-counter glucose sensor with a child.",
        "caption": "A question-led plan helps families decide what to monitor, who will review the data, and when medical care should come first.",
        "placement": "Before the practical questions and final conclusion.",
        "prompt": "Family meeting with a pediatrician or pediatric endocrinologist. Notebook with unlabeled checklist, phone with plain neutral trend line, and small unbranded packaged glucose sensor on the table. Focus on conversation and decision process, not the product. No logos, pump, injection, low alert, fake claims, or readable text.",
        "loading": "lazy",
    },
]


def figure(index: int) -> str:
    image = IMAGES[index]
    return f"""
<figure data-image-slot="{image['slot']}">
  <img data-description="{image['description']}" width="{image['width']}" height="{image['height']}" src="/static/uploads/2026/08/{image['filename']}" alt="{image['alt']}" title="{image['title']}" loading="{image['loading']}" />
  <figcaption>{image['caption']}</figcaption>
</figure>
""".strip()


CONTENT_HTML = f"""
<img width="{IMAGES[0]['width']}" height="{IMAGES[0]['height']}" src="/static/uploads/2026/08/{IMAGES[0]['filename']}" alt="{IMAGES[0]['alt']}" title="{IMAGES[0]['title']}" data-description="{IMAGES[0]['description']}" loading="{IMAGES[0]['loading']}" />
<h2>A Headline That Makes Parents Pause</h2>
<p>A parent sees the headline while making breakfast or waiting in a pickup line: children can now use an over-the-counter continuous glucose monitor. The idea is immediately understandable. A small sensor on a child’s arm. A phone nearby. A line that shows what happens after cereal, soccer practice, a stressful school day, a viral illness, or a short night of sleep.</p>
<p>For families already watching diabetes risk, that visibility can feel useful. For a parent who has wondered whether symptoms might be related to glucose, it can feel reassuring to have more information. For an adolescent who wants to understand their body, the technology can feel concrete in a way that occasional lab results do not.</p>
<p>But “available without a prescription” can be misunderstood. It does not mean every child should wear a sensor. It does not mean the sensor can diagnose diabetes. It does not mean a family can safely make medication decisions from an app. And it does not mean the device has the same alert features as a therapeutic CGM selected for a child who uses insulin.</p>
<p>This article is meant to slow the announcement down. We will look at what the FDA cleared, what Stelo is designed to do, who might reasonably discuss it with a pediatric clinician, who should not use it, and why the emotional life of glucose data matters when the person wearing the sensor is a child.</p>
<p>A glucose pattern, a diagnosis, and a treatment plan are related, but they are not interchangeable. That difference is the thread running through the whole story.</p>

<h2>What Did the FDA Actually Clear?</h2>
<p>On <strong>June 12, 2026</strong>, the U.S. Food and Drug Administration cleared Dexcom’s Stelo Glucose Biosensor System as the first over-the-counter continuous glucose monitor indicated for children. The relevant 510(k) is <a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K260935" target="_blank" rel="noopener">K260935</a>, with a public <a href="https://www.accessdata.fda.gov/cdrh_docs/reviews/K260935.pdf" target="_blank" rel="noopener">FDA decision summary</a>. The expanded indication covers people <strong>2 years of age and older who do not use insulin</strong>. FDA had previously cleared Stelo for over-the-counter use in adults 18 and older in March 2024.</p>
<p>That is a regulatory clearance for a defined intended use. It is not a universal recommendation for routine glucose tracking in children. It also does not guarantee that every pediatric purchasing pathway, app screen, insurer policy, or support workflow has caught up with the new clearance. As of this article’s source review on August 3, 2026, official consumer pages we could access still displayed adult-oriented Stelo indication language in some places, while the FDA pediatric decision summary gave the expanded age-two-and-older indication. Families should verify the current store, compatibility, labeling, and support information before buying.</p>

<table>
  <caption>Stelo at a glance under FDA 510(k) K260935</caption>
  <thead>
    <tr>
      <th>Question</th>
      <th>Verified answer</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Minimum age</td><td>2 years of age</td></tr>
    <tr><td>Prescription required</td><td>No, under the cleared over-the-counter indication</td></tr>
    <tr><td>Intended for people using insulin</td><td>No</td></tr>
    <tr><td>Provides urgent low-glucose alerts</td><td>No. FDA notes it is not designed to alert users to problematic hypoglycemia.</td></tr>
    <tr><td>Adult supervision required for minors</td><td>Yes. Users younger than 18 are to use the system under caregiver supervision.</td></tr>
    <tr><td>Sensor duration</td><td>Up to 15 days with a 12-hour grace period, with pediatric wear likely shorter than adult wear.</td></tr>
    <tr><td>Display behavior</td><td>The sensor reports new glucose data every 5 minutes; the receiving device displays updates every 15 minutes.</td></tr>
    <tr><td>Medication changes based on readings alone</td><td>No. Consult a qualified health professional before medication adjustments or other medical action.</td></tr>
    <tr><td>Major exclusions</td><td>People who use insulin, people with problematic hypoglycemia, and people receiving dialysis.</td></tr>
    <tr><td>Extra caution</td><td>People with a history of disordered eating or eating disorders should talk with a health professional before use.</td></tr>
  </tbody>
</table>

<h2>What Stelo Is Designed to Do</h2>
<p>Stelo is a wearable glucose biosensor. The sensor sits in the tissue under the skin and estimates glucose in <strong>interstitial fluid</strong>, not directly from a laboratory blood sample. It pairs with a compatible smartphone or supported smart device. For a child, the display may be on a parent’s or caregiver’s device.</p>
<p>The system records and displays repeated glucose values and trends. That can make patterns more visible than an occasional fingerstick or a single lab value. A family might notice that readings tend to be higher during illness, lower after a walk, different after a medication change, or more variable after a week of poor sleep. For background on everyday patterns, our articles on <a href="/blood-sugar-body/">daily blood sugar rhythms</a>, <a href="/sleep-and-diabetes-management/">sleep and diabetes management</a>, and <a href="/food-sequencing-diabetes/">food sequencing</a> offer related context.</p>
<p>The important word is <em>patterns</em>. Interstitial glucose can lag behind blood glucose, especially when glucose is changing quickly. Sensors can also be affected by placement, pressure, connectivity, warmup, medication interference, and whether the reading matches how the child feels. A short rise after a meal is not automatically a problem. A flatter line is not a moral achievement. A single unexpected reading is not a diagnosis.</p>

{figure(1)}

<h2>Who Might Reasonably Discuss It With a Clinician?</h2>
<p>The best reason to use an OTC glucose sensor with a child is not curiosity alone. It is a defined question that a family and clinician agree is worth exploring. Stelo may be worth discussing for a child with established type 2 diabetes who does not use insulin, a child on eligible non-insulin therapy, or a child being followed for prediabetes or metabolic risk under medical guidance. It may also be reasonable for a teenager who can participate in the plan without becoming consumed by the numbers.</p>
<p>Useful questions tend to be specific. Are symptoms occurring at the same time as unusual readings? Are glucose patterns consistently elevated at a certain time of day? Did a clinician-recommended activity or meal plan change the overall pattern? Would formal laboratory testing be appropriate? Is an existing non-insulin treatment plan producing the expected pattern?</p>
<p>The device is less useful when the question is vague. “Let’s collect every possible number because lower and flatter must always be better” is a poor plan for a child. “Let’s monitor for two weeks because the pediatrician wants to know whether symptoms line up with unusual glucose patterns” is a more grounded one.</p>

<div class="article-impact-grid">
  <div class="article-impact-card">
    <h3>Five Questions Before Placing a Sensor</h3>
    <p>What question are we trying to answer? Is this the correct device? Who will interpret the data? What will trigger medical follow-up? How will we protect the child’s relationship with food and numbers?</p>
  </div>
  <div class="article-impact-card">
    <h3>Keep the Time Frame Defined</h3>
    <p>Short-term monitoring is easier to interpret when the family knows why it is being done, how long it will last, and what the family will not infer from the graph.</p>
  </div>
</div>

{figure(3)}

<h2>Who Stelo Is Not Designed For</h2>
<p>This is the section families should read slowly. Stelo is not intended for children or adults who use insulin. It is not designed for people with problematic hypoglycemia. It is not for people receiving dialysis. It is not a device for unsupervised use by a child. It is not a tool for making independent medication changes, replacing emergency evaluation, diagnosing type 1 diabetes, or treating every glucose fluctuation as something that must be corrected.</p>
<p>The absence of urgent low-glucose alerts is especially important. Many families associate CGMs with the alerting systems used by people who take insulin. Stelo is different. FDA specifically noted that the system is not for people with problematic hypoglycemia because it is not designed to alert users when that potentially dangerous condition occurs. A child who uses insulin, is at meaningful risk for low glucose, or needs safety alerts should be using a clinician-directed monitoring plan with the features appropriate to that child’s care.</p>
<p>That does not make one device universally better than another. It means the devices are intended for different clinical situations.</p>

<h2>A Glucose Trend Is Not a Diabetes Diagnosis</h2>
<p>A consumer CGM may help show repeated estimated glucose values, direction of change, time-related patterns, responses during ordinary life, and data a family can bring to a clinician. It cannot, by itself, diagnose type 1 diabetes, type 2 diabetes, prediabetes, reactive hypoglycemia, insulin resistance, a food intolerance, or a metabolic disorder.</p>
<p>Diabetes and prediabetes are diagnosed through clinical evaluation and validated testing. The <a href="https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis" target="_blank" rel="noopener">National Institute of Diabetes and Digestive and Kidney Diseases</a> describes diagnostic tests such as A1C, fasting plasma glucose, oral glucose-tolerance testing, and random plasma glucose in an appropriate symptomatic setting. The <a href="https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes" target="_blank" rel="noopener">ADA Standards of Care in Diabetes--2026</a> likewise base diagnosis on A1C or plasma glucose criteria, with additional clinical judgment and follow-up testing when needed.</p>
<p>Children sometimes need additional testing to distinguish type 1 from type 2 diabetes, especially when symptoms, age, weight change, ketones, family history, or clinical presentation raise concern. A graph on a phone can give a clinician a reason to investigate. It does not replace that investigation.</p>

{figure(2)}

<table>
  <caption>What a CGM can show--and what it cannot diagnose</caption>
  <thead>
    <tr>
      <th>A CGM may help show</th>
      <th>A CGM cannot establish by itself</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Repeated glucose patterns</td><td>A formal diabetes diagnosis</td></tr>
    <tr><td>Changes after meals, sleep, illness, stress, or activity</td><td>The cause of an unusual pattern</td></tr>
    <tr><td>Whether a reading is rising or falling</td><td>Whether a child has type 1 or type 2 diabetes</td></tr>
    <tr><td>Information to discuss with a clinician</td><td>Whether medication should be started, stopped, or changed</td></tr>
    <tr><td>Patterns occurring during symptoms</td><td>Whether symptoms are harmless</td></tr>
    <tr><td>Variation across daily routines</td><td>A child’s future diabetes risk with certainty</td></tr>
  </tbody>
</table>

<h2>Why Type 1 Diabetes Requires Special Caution</h2>
<p>Type 1 diabetes can develop in children who previously appeared healthy, and symptoms can progress over weeks or months. The <a href="https://www.cdc.gov/diabetes/signs-symptoms/index.html" target="_blank" rel="noopener">CDC’s diabetes symptom guidance</a> includes increased thirst, frequent urination, unexplained weight loss, fatigue, blurry vision, nausea, vomiting, stomach pain, and DKA in the type 1 diabetes discussion. New bed-wetting or a sudden increase in accidents can also be a practical warning sign for families.</p>
<p>An OTC sensor must never become a reason to delay care. If a child has concerning symptoms, the symptoms take priority over the app. A normal-looking consumer sensor value does not rule out a serious condition, and an alarming pattern is not a substitute for medical assessment.</p>

<div class="article-callout">
  <p class="article-callout__title">Symptoms Take Priority Over the Sensor</p>
  <p>Seek prompt medical care when a child has increased thirst, frequent urination, unexplained weight loss, new bed-wetting, fatigue, blurry vision, nausea, vomiting, or abdominal pain. Seek urgent or emergency care when symptoms suggest possible diabetic ketoacidosis, including vomiting with inability to keep fluids down, fast or difficult breathing, fruity-smelling breath, severe fatigue, altered alertness, or several symptoms together. The <a href="https://www.cdc.gov/diabetes/about/diabetic-ketoacidosis.html" target="_blank" rel="noopener">CDC describes DKA</a> as serious and sometimes the first noticeable sign of diabetes.</p>
</div>

<h2>What Families Might Learn From Short-Term Monitoring</h2>
<p>Short-term monitoring can sometimes reduce guesswork. A family may see recurring patterns that are hard to capture with occasional checks. A clinician may get more context around symptoms, meals, activity, illness, sleep, or stress. An adolescent may learn how routines affect their body when that learning is emotionally appropriate. A monitoring period may also help a family prepare better questions before a pediatric or endocrinology visit.</p>
<p>The evidence base is still specific, not universal. In youth-onset type 2 diabetes, a 10-day CGM study reported behavioral changes and interest in continued use, but did not show short-term or long-term glycemic improvement. The <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC12690182/" target="_blank" rel="noopener">ADA 2026 Children and Adolescents section</a> notes that real-time CGM in adolescents and young adults with type 2 diabetes can improve quality of life, while the broader pediatric CGM evidence is strongest in established diabetes management rather than OTC monitoring of children without insulin treatment.</p>
<p>That distinction matters. A child with diagnosed diabetes, a child being evaluated for symptoms, a child with prediabetes under medical follow-up, and a healthy child whose parent is simply curious are not the same situation. The device may be useful in selected contexts. It has not been proven to improve long-term health for every pediatric group, and monitoring itself does not prevent diabetes.</p>

<h2>Physical Limitations and Risks</h2>
<p>FDA’s June 2026 announcement reported mild device-related adverse events in supporting data, including local infection, skin irritation, and pain or discomfort. Families should also think about adhesive reactions, sensor detachment, sweating, swimming, contact sports, clothing friction, incorrect placement, unexpected readings, phone compatibility problems, data interruptions, and whether the child dislikes wearing a visible device.</p>
<p>The decision summary says the sensor is inserted on the back of the upper arm; children ages 2 to 6 may also use the upper buttocks. It specifically says not to use other sites, such as the abdomen, because the system may not work as expected. Pediatric survival data also suggest real-world wear may be shorter in children than in adults. In reprocessed pediatric data, 76.2% of arm sensors lasted through day 10, while a smaller 2-to-6 upper-buttocks group had 56.3% last through day 10.</p>
<p>Families should follow the instructions for use and contact product support or a clinician when the skin becomes increasingly red, painful, swollen, warm, or draining; when the sensor repeatedly fails; when a reading does not fit the child’s symptoms; or when the child is distressed by insertion or wearing the device. The article cannot diagnose a skin reaction, and a device manual cannot replace clinical judgment.</p>

<h2>When More Data Creates More Anxiety</h2>
<p>Glucose data can have different emotional effects. Some families feel more informed, better prepared, and less dependent on guesswork. Others may start checking repeatedly, worrying about ordinary fluctuations, interrupting sleep, commenting on every meal, or creating tension between adolescents and caregivers.</p>
<p>Research in pediatric diabetes does not support a simple “CGM helps everyone emotionally” or “CGM harms everyone emotionally” story. Reviews of youth CGM use describe mixed psychological responses, and some findings come from children with established type 1 diabetes or families using alert-enabled systems. That evidence cannot be copied directly onto OTC monitoring in children who do not use insulin. It can still teach a useful lesson: expectations, family communication, and boundaries matter.</p>
<p>Helpful boundaries include deciding how often the data will be reviewed, avoiding comments on every reading, not assigning moral value to numbers, avoiding praise for “flat” glucose as proof of being good, and letting older children participate in how the data will be discussed. If monitoring is increasing distress, arguments, restriction, or sleep disruption, the family should pause and seek professional support.</p>

{figure(4)}

<h2>Eating-Disorder and Disordered-Eating Considerations</h2>
<p>The FDA decision summary and announcement include an unusually important caution: people with a history of disordered eating or eating disorders should talk with a health professional before using Stelo. That warning deserves more than a footnote.</p>
<p>Glucose tracking does not cause an eating disorder by itself. But a device that creates constant food-related feedback could reinforce unhealthy attention to numbers in a vulnerable child or adolescent. Extra caution is appropriate when a child is intensely worried about food, skips meals, restricts whole food groups, feels guilt after eating, uses exercise to compensate for food, is preoccupied with weight or body shape, or has a known history of disordered eating or eating-disorder treatment.</p>
<p>The goal is not to hide useful health information. The goal is to make sure the information is used in a way that protects the child. That may mean involving the pediatrician, an eating-disorder-informed behavioral-health professional, and a registered dietitian. It also means avoiding language that turns meals into “good” or “bad” choices based on a single line on a phone.</p>

<h2>Do Not Change Medication From Sensor Data Alone</h2>
<p>This point is simple and important: families should not start medication, stop medication, change a dose, give someone else’s medication, use insulin, or aggressively restrict food based only on Stelo readings. Medication decisions depend on diagnosis, laboratory results, symptoms, growth and development, current medication, kidney and liver health, family history, other medical conditions, and whether the sensor pattern is reliable and clinically meaningful.</p>
<p>FDA and Stelo safety information both tell users to consult a health care professional before medication adjustments or other medical action based on sensor readings. The same caution applies to delaying care. Do not wait to collect more sensor data when a child has symptoms that need prompt evaluation.</p>

<h2>What Should Happen When Readings Look Unusual?</h2>
<p>If there is an unexpected number without symptoms, first slow down. Check whether the sensor is newly inserted, whether pressure or dislodgement is possible, whether the app is connected, whether the placement matches the instructions, and whether the device instructions recommend another step. Record the context, and contact a health professional if the pattern persists or feels concerning.</p>
<p>If unusual patterns repeat, save or export the relevant data if supported. Note meals, activity, sleep, illness, medications, and symptoms. Then arrange a pediatric or endocrinology discussion. Expect that lab testing may still be needed. The pattern is evidence to discuss, not a diagnosis to name at home.</p>
<p>If the child has concerning symptoms, care comes first. Seek prompt or emergency medical help as appropriate. Do not assume the sensor has ruled out danger because a line looked ordinary a few minutes ago.</p>

<h2>Questions Before Buying an OTC CGM for a Child</h2>
<p>A practical decision begins with a few honest questions: What specific question are we trying to answer? Has the child’s pediatrician recommended glucose monitoring? Does the child use insulin? Does the child need urgent low-glucose alerts? Has the child had symptoms suggesting diabetes? Would laboratory testing be more appropriate first?</p>
<p>Then ask how the data will be handled: Who will review it? How long will we use the sensor? What pattern or symptom would lead us to call the clinician? How will we prevent repeated checking or food anxiety? Does the child understand why the device is being used? How does the child feel about wearing it?</p>
<p>Finally, check the practical realities: Is there a history of disordered eating or an eating disorder? Is the phone compatible? What will the device cost? Does insurance cover any part of it? What happens if the sensor falls off early? What data are stored, shared, or uploaded? Are we expecting the device to answer a question it cannot answer?</p>

{figure(5)}

<h2>Questions for the Child’s Clinician</h2>
<p>Families do not need perfect questions to have a useful appointment. Start with these: Is this device appropriate for my child’s medical situation? Would laboratory testing be more useful? Are we evaluating prediabetes, type 2 diabetes, symptoms, medication response, or something else? How long should we collect data? Which patterns should we bring to you?</p>
<p>It is also reasonable to ask what symptoms require urgent evaluation, whether unexpected readings should be confirmed another way, whether any medication could interfere with the reading, whether a different CGM is more appropriate, how the data should be discussed with the child, and whether anxiety or eating-disorder concerns should change the plan.</p>

<h2>Over-the-Counter Does Not Mean Medically Neutral</h2>
<p>The pediatric clearance is part of a larger shift: more health data is moving into family life, outside the walls of clinics. That can help some families ask better questions earlier. It may help people who face barriers to specialty care notice patterns worth discussing. But access to data is not the same as access to interpretation, follow-up testing, affordable devices, supported phones, language-accessible education, privacy protections, or a clinician with time to review consumer-generated data.</p>
<p>As of August 3, 2026, official Stelo pages we accessed listed a one-time price of $99 and subscription options beginning at $89 per month for adult-oriented product pages, and stated that the product was HSA/FSA eligible. We did not verify a pediatric-specific store pathway or insurance coverage guarantee. Stelo compatibility information listed iOS and Android operating-system requirements, including iOS 18.6 and Android 13 minimums and iOS 26.5 and Android 16 as highest tested versions, with smartwatch use as an extension of the phone app. Those details can change, so families should confirm before purchase.</p>

<h2>What We Still Do Not Know</h2>
<p>FDA clearance addresses the device’s intended use and regulatory evidence. It does not answer every clinical, behavioral, or access question that will matter in real homes. We still need to learn how families will use pediatric OTC CGM data outside structured care, which pediatric groups benefit most, how long monitoring should last, how often data should be reviewed, and whether short-term learning persists after a sensor is removed.</p>
<p>We also need better evidence on emotional effects, family communication, food relationships, equity, real-world pediatric wear time, clinician workload, false reassurance, and overdiagnosis. A sensor may help some families. It may create unnecessary monitoring for others. The same technology can be useful or unhelpful depending on the child, the question, and the support around it.</p>

<h2>What We Can Honestly Say</h2>
<ol>
  <li>Stelo became the first OTC CGM cleared in the United States for people as young as two.</li>
  <li>Its pediatric indication applies to people who do not use insulin.</li>
  <li>It is not designed for people who need reliable hypoglycemia alerts.</li>
  <li>Sensor trends can support a clinical conversation but cannot independently diagnose diabetes.</li>
  <li>Families should not change medication based only on the device’s output.</li>
  <li>The device may be useful in selected situations, but the value depends on the child, the clinical question, and how the family responds to the information.</li>
</ol>
<p>A glucose sensor can make an invisible pattern visible. That can be genuinely helpful. It can also tempt adults to treat every number as if it has an immediate meaning. For a child, the goal should not be to collect the most data possible. The goal should be to answer a worthwhile health question while protecting the child’s body, confidence, relationships, and ordinary life beyond the graph.</p>

<h2>Sources and Further Reading</h2>
<ul>
  <li><a href="https://www.fda.gov/news-events/press-announcements/fda-clears-first-over-counter-continuous-glucose-monitor-children" target="_blank" rel="noopener">FDA: Clears first OTC continuous glucose monitor for children</a></li>
  <li><a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K260935" target="_blank" rel="noopener">FDA 510(k) database entry K260935</a></li>
  <li><a href="https://www.accessdata.fda.gov/cdrh_docs/reviews/K260935.pdf" target="_blank" rel="noopener">FDA decision summary for K260935</a></li>
  <li><a href="https://www.stelo.com/en-us/safety-information" target="_blank" rel="noopener">Stelo safety information</a> and <a href="https://www.stelo.com/en-us/compatibility" target="_blank" rel="noopener">Stelo app compatibility</a></li>
  <li><a href="https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis" target="_blank" rel="noopener">NIDDK: Diabetes tests and diagnosis</a></li>
  <li><a href="https://www.cdc.gov/diabetes/signs-symptoms/index.html" target="_blank" rel="noopener">CDC: Diabetes symptoms</a> and <a href="https://www.cdc.gov/diabetes/about/diabetic-ketoacidosis.html" target="_blank" rel="noopener">CDC: Diabetic ketoacidosis</a></li>
  <li><a href="https://diabetesjournals.org/care/article/49/Supplement_1/S297/163923/14-Children-and-Adolescents-Standards-of-Care-in" target="_blank" rel="noopener">ADA Standards of Care in Diabetes--2026: Children and Adolescents</a></li>
  <li><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC10258317/" target="_blank" rel="noopener">Short-term CGM use in youth-onset type 2 diabetes</a></li>
  <li><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC5038546/" target="_blank" rel="noopener">Psychological reactions associated with CGM in youth</a></li>
  <li><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC4002640/" target="_blank" rel="noopener">Eating disorders and disordered eating in type 1 diabetes</a></li>
</ul>

<h2>Related Mindful Diabetes Reading</h2>
<p>For more context, visit the <a href="/guide/">Mindful Diabetes guide</a>, our <a href="/free-guides/">free health guides</a>, and articles on <a href="/continuous-glucose-monitors-and-more-to-keep-you-on-track/">continuous glucose monitors</a>, <a href="/glucose-metabolism-and-brain-health/">glucose metabolism</a>, <a href="/insulin-resistance-cognitive-decline/">insulin resistance</a>, <a href="/low-impact-exercise/">low-impact exercise</a>, <a href="/mindful-eating-the-key-to-blood-sugar-management/">mindful eating</a>, and <a href="/health-tools/">health tools</a>. You can also <a href="#subscribe">subscribe</a> for future diabetes prevention and family-health updates.</p>

<aside class="article-wellness-tools">
  <div class="article-wellness-tools__intro">
    <p class="eyebrow">Mindful Diabetes Tools</p>
    <h2 class="article-wellness-tools__title">Track the Question, Not Every Number</h2>
    <p>When families are preparing for a clinician conversation, a short symptom note or routine log can sometimes be more helpful than reacting to every sensor point. For broader wellness journaling, visit <a href="https://memovela.com/" target="_blank" rel="noopener">Memovela</a> or <a href="/memovela/">Read about Memovela</a>.</p>
  </div>
</aside>
""".strip()


IMAGE_BRIEF = f"""# Image Brief: {TITLE}

Article URL: `/{SLUG}/`

Publication date: August 3, 2026

Upload folder: `static/uploads/2026/08/`

## General Direction

Use a warm nonprofit health publication style: realistic, calm, scientifically grounded, family-centered, and independent from product marketing. Use natural daylight, modern pediatric clinical or home settings, diverse families, and subtle Mindful Diabetes orange-and-green accents. Avoid product logos, insulin pumps, injections, emergency low-glucose alerts, fear-based food imagery, body-size judgment, embedded medical claims, or fake branded phone interfaces.

Export guidance:

- Hero image: `1600 x 900`, WebP.
- Standard article images: `1400 x 788`, WebP.
- Loading behavior: all six images use `loading=\"lazy\"` in the content seed; the site template may promote the first image into the article hero.
- Credit: newly generated editorial images for Mindful Diabetes; no stock or product photography reused.
- Accessibility: alt text describes visible content; captions explain editorial meaning without relying on the image.
- Integration confirmation: exactly six generated WebP images are integrated into the article.

"""

for index, image in enumerate(IMAGES, start=1):
    IMAGE_BRIEF += f"""## {index}. {image['title']}

Filename: `{image['filename']}`

Size: `{image['width']} x {image['height']}`

Article placement: {image['placement']}

Alt text:

{image['alt']}

SEO title:

{image['title']}

Caption:

{image['caption']}

Description:

{image['description']}

Generation prompt:

{image['prompt']}

Newly generated: yes.

"""


SOURCE_NOTE = """# Source Verification: Pediatric OTC CGM Stelo Article

Publication date: August 3, 2026

Research cutoff: August 3, 2026

Article slug: `otc-cgm-children-stelo-family-guide`

FDA clearance date: June 12, 2026

510(k): `K260935`

## Core Source Findings

- FDA announced on June 12, 2026 that Dexcom's Stelo Glucose Biosensor System was cleared as the first over-the-counter continuous glucose monitor for children.
- FDA K260935 expands the intended-use population to people 2 years and older who do not use insulin.
- The system is OTC, home-use, and intended to continuously measure, record, analyze, and display glucose values from interstitial fluid.
- The receiving device displays glucose data every 15 minutes; the sensor reports data every 5 minutes.
- Expected wear is up to 15 days with a 12-hour grace period, but FDA notes pediatric wear may be shorter and the decision summary states pediatric sensor survival is likely lower than adult survival.
- People younger than 18 are to use Stelo under caregiver supervision.
- Insertion site: back of upper arm. Children ages 2 to 6 may also use the upper buttocks. Other sites, including abdomen, are not recommended in the decision summary.
- Major exclusions: people who use insulin, people with problematic hypoglycemia, and people receiving dialysis.
- Stelo has no glucose or system alerts in the K260935 comparison table and is not designed to alert users to problematic hypoglycemia.
- Medication and medical action: users/caregivers should consult a qualified health professional before medication changes or other medical action based on output.
- Interfering substances and procedural warnings: MR unsafe for MRI/diathermy; CT only if sensor is outside scanned area and covered with lead apron; acetaminophen above maximum dosing may make readings look higher; hydroxyurea can make sensor readings falsely higher.
- FDA announcement reported mild adverse events including local infection, skin irritation, and pain or discomfort.
- FDA and decision-summary language advises people with a history of disordered eating or eating disorders to consult a health professional before use.

## Claim-Verification Matrix

| Claim | Source | Source date | Applicable population | Verified as of | Included or excluded | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| FDA cleared first OTC CGM for children on June 12, 2026 | FDA press announcement | June 12, 2026 | U.S.; pediatric OTC CGM | Aug. 3, 2026 | Included | Article uses “cleared,” not “approved.” |
| Expanded indication is people age 2+ who do not use insulin | FDA announcement; FDA K260935 decision summary | June 12, 2026 | People 2+ not using insulin | Aug. 3, 2026 | Included | Central label boundary. |
| Previous OTC clearance was adult 18+ in March 2024 | FDA announcement; K234070 predicate noted in decision summary | March 2024 / June 2026 | Adults 18+ not using insulin | Aug. 3, 2026 | Included | Used for context only. |
| Stelo measures interstitial fluid and displays values/trends | FDA K260935 decision summary | June 2026 | Intended users | Aug. 3, 2026 | Included | Article avoids calling it direct lab blood glucose. |
| Display updates every 15 minutes; sensor reports every 5 minutes | FDA K260935 decision summary | June 2026 | Intended users | Aug. 3, 2026 | Included | Table and device-operation section. |
| Up to 15-day wear with pediatric wear likely shorter | FDA announcement; K260935 decision summary | June 2026 | Intended users, pediatric extrapolation | Aug. 3, 2026 | Included | Article notes pediatric survival uncertainty. |
| No urgent hypoglycemia alert function | FDA announcement; K260935 comparison table | June 2026 | Intended users | Aug. 3, 2026 | Included | Article distinguishes from therapeutic insulin-user CGMs. |
| Do not use if on insulin, problematic hypoglycemia, or dialysis | FDA announcement; K260935 decision summary; Stelo safety information | June 2026 / retrieved Aug. 3, 2026 | Intended users and excluded populations | Aug. 3, 2026 | Included | Prominent “not designed for” section. |
| Minors require caregiver supervision | FDA announcement; K260935 decision summary | June 2026 | Users under 18 | Aug. 3, 2026 | Included | Table and article body. |
| Do not change medication or take medical action based on readings alone | FDA announcement; Stelo safety information | June 2026 / retrieved Aug. 3, 2026 | Users/caregivers | Aug. 3, 2026 | Included | Repeated in article. |
| Disordered-eating history requires professional discussion | FDA announcement; K260935 decision summary | June 2026 | Users with history of disordered eating/eating disorders | Aug. 3, 2026 | Included | Dedicated section. |
| CGM cannot diagnose diabetes or prediabetes | NIDDK diagnostic testing; ADA 2026 diagnosis section | Current pages / Jan. 2026 Standards | People being evaluated for diabetes | Aug. 3, 2026 | Included | Article contrasts trends with A1C/FPG/OGTT/RPG. |
| Type 1 symptoms and DKA require prompt/emergency care | CDC diabetes symptoms; CDC DKA guidance | Current pages | Children and adults | Aug. 3, 2026 | Included | Safety callout. |
| Stelo improves long-term health for all children | Not verified | N/A | Broad pediatric population | Aug. 3, 2026 | Excluded | Article explicitly avoids this claim. |
| Stelo can screen for or rule out type 1 diabetes | Not supported by labeling/guidelines | N/A | Pediatric consumers | Aug. 3, 2026 | Excluded | Article says not to delay evaluation. |
| Every healthy child should use a CGM | Not supported | N/A | General pediatric population | Aug. 3, 2026 | Excluded | Article rejects universal suitability. |
| Pediatric-specific purchase pathway and insurance coverage are guaranteed | Not verified on official consumer pages | Retrieved Aug. 3, 2026 | U.S. consumers | Aug. 3, 2026 | Excluded | Article notes uncertainty. |

## Product Availability, Price, and Compatibility

Official Stelo consumer pages retrieved on August 3, 2026 continued to display adult-oriented indication language in some places, despite FDA K260935 providing the expanded pediatric indication. The article therefore treats the FDA clearance as verified but does not claim a pediatric-specific purchase workflow or insurance coverage guarantee.

Standalone public Stelo user-guide URL variants checked on August 3, 2026 returned 404, despite the official site referencing a support/request-user-guide flow. The article therefore uses the FDA K260935 decision summary for pediatric labeling details and current official Stelo safety/compatibility pages for live practical-access details.

Official Stelo pages retrieved August 3, 2026 listed a one-time purchase price of `$99.00`, a monthly subscription price of `$89.00`, and HSA/FSA eligibility. These are mentioned as observed adult-oriented storefront details, not as a pediatric coverage promise.

Official Stelo compatibility page retrieved August 3, 2026 listed iOS 18.6 and Android 13 as minimum operating systems, iOS 26.5 and Android 16 as highest tested operating systems, and smartwatch use as an extension of the phone app.

## Principal Sources

- FDA announcement: `https://www.fda.gov/news-events/press-announcements/fda-clears-first-over-counter-continuous-glucose-monitor-children`
- FDA 510(k) K260935: `https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K260935`
- FDA decision summary K260935: `https://www.accessdata.fda.gov/cdrh_docs/reviews/K260935.pdf`
- Stelo safety information: `https://www.stelo.com/en-us/safety-information`
- Stelo compatibility: `https://www.stelo.com/en-us/compatibility`
- Stelo storefront/subscription page: `https://www.stelo.com/en-us/buy-stelo-monthly-subscription-archive`
- NIDDK diagnosis guidance: `https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis`
- CDC diabetes symptoms: `https://www.cdc.gov/diabetes/signs-symptoms/index.html`
- CDC DKA: `https://www.cdc.gov/diabetes/about/diabetic-ketoacidosis.html`
- ADA 2026 Diagnosis and Classification: `https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes`
- ADA 2026 Children and Adolescents: `https://diabetesjournals.org/care/article/49/Supplement_1/S297/163923/14-Children-and-Adolescents-Standards-of-Care-in`
- Youth-onset type 2 diabetes CGM study: `https://pmc.ncbi.nlm.nih.gov/articles/PMC10258317/`
- Psychological reactions to CGM in youth: `https://pmc.ncbi.nlm.nih.gov/articles/PMC5038546/`
- Eating disorders and disordered eating in type 1 diabetes: `https://pmc.ncbi.nlm.nih.gov/articles/PMC4002640/`

## Excluded Language and Claims

- “FDA approved”
- “Breakthrough for every child”
- “Revolutionary diabetes detector”
- “End of fingersticks”
- “Every parent should”
- “Hack” or “optimize” a child’s glucose
- “Good foods” or “bad foods”
- “Flatten every glucose spike”
- Claims that Stelo prevents diabetes, diagnoses diabetes, rules out type 1 diabetes, or safely guides medication changes without a clinician
"""


def main() -> None:
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    data = [item for item in data if item.get("slug") != SLUG]

    post = {
        "id": "5115",
        "type": "post",
        "status": "publish",
        "title": TITLE,
        "slug": SLUG,
        "url": URL,
        "date": DATE,
        "modified": DATE,
        "parent": "0",
        "menu_order": "0",
        "categories": ["Blog"],
        "tags": [
            "OTC CGM",
            "Stelo",
            "Pediatric diabetes",
            "Continuous glucose monitoring",
            "Prediabetes",
            "Type 2 diabetes",
            "Diabetes technology",
            "Family health",
            "Mindful Diabetes guide",
        ],
        "featured_image_id": "pediatric-otc-cgm-family-guide-2026",
        "template": "default",
        "excerpt_html": EXCERPT,
        "seo_title": SEO_TITLE,
        "meta_description": META_DESCRIPTION,
        "canonical_url": URL,
        "og_title": SEO_TITLE,
        "og_description": META_DESCRIPTION,
        "og_image": "/static/uploads/2026/08/pediatric-otc-cgm-family-guide-2026.webp",
        "content_html": CONTENT_HTML,
    }

    data.append(post)
    CONTENT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    IMAGE_BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_BRIEF_PATH.write_text(IMAGE_BRIEF, encoding="utf-8")
    SOURCE_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_NOTE_PATH.write_text(SOURCE_NOTE, encoding="utf-8")


if __name__ == "__main__":
    main()
