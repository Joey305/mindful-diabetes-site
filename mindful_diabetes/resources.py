"""Shared educational resource data for public /resources pages."""

from copy import deepcopy


AI_SITE_URL = "https://www.mindfuldiabetes.ai"
AI_RESOURCES_URL = f"{AI_SITE_URL}/resources"
JEIR_URL = f"{AI_SITE_URL}/jeir"
ABOUT_URL = f"{AI_SITE_URL}/about"
REVIEW_DATE = "July 31, 2026"
PUBLISHED_DATE = "July 31, 2026"
REVIEW_NOTE = (
    "Reviewed for clarity, source alignment, and educational usefulness. "
    "This resource has not been individually medically reviewed unless a named "
    "qualified medical reviewer is displayed."
)
AUTHOR_NAME = "Prepared by the Mindful Diabetes Editorial Team"
RESPONSIBLE_EDITOR = "Joseph M. Schulz, Founder, Mindful Diabetes Inc."
DISCLAIMER = (
    "Mindful Diabetes Inc. and JEIR provide educational information only. They do not "
    "provide diagnosis, treatment, emergency guidance, or personalized medical advice."
)

COMMON_SOURCES = [
    {
        "organization": "Centers for Disease Control and Prevention",
        "title": "Diabetes",
        "url": "https://www.cdc.gov/diabetes/",
    },
    {
        "organization": "National Institute of Diabetes and Digestive and Kidney Diseases",
        "title": "Diabetes overview",
        "url": "https://www.niddk.nih.gov/health-information/diabetes",
    },
    {
        "organization": "MedlinePlus",
        "title": "Diabetes",
        "url": "https://medlineplus.gov/diabetes.html",
    },
]

CATEGORY_ORDER = [
    "Blood Sugar Basics",
    "Metabolic Health",
    "Brain Health",
    "Daily Habits",
    "Working With Your Doctor",
]

RESOURCE_ARTICLES = [
    {
        "slug": "blood-sugar-and-energy",
        "title": "How does blood sugar affect energy?",
        "category": "Blood Sugar Basics",
        "meta_description": "Educational guidance on how blood sugar may relate to energy and why patterns over time are more informative than isolated moments.",
        "summary": "Glucose helps fuel the body, including the brain, but energy is shaped by more than glucose alone. Sleep, hormones, stress, meals, hydration, and activity can all change how steady or uneven a day feels.",
        "big_idea": "Energy has multiple inputs",
        "best_lens": "Look for trends across the day",
        "learning_points": [
            "How glucose and energy are related without oversimplifying",
            "Why quick rises and falls may feel different",
            "What context helps make energy patterns more useful",
        ],
        "sections": [
            ("Glucose is part of the story, not the whole story", "Blood sugar can influence how energized or depleted you feel, but it does not explain every moment of fatigue or alertness. A useful conversation usually includes sleep, food timing, hydration, medication, stress, and other health context."),
            ("Why quick changes may feel different", "Some people notice that fast changes in glucose line up with shifts in energy, focus, or hunger. That pattern can be worth discussing, but one feeling or one reading is not enough to diagnose a condition."),
            ("Why patterns matter more than single moments", "Repeated patterns across meals, sleep, movement, and stress are usually more informative than isolated numbers. Notes about timing and routine can help a qualified professional interpret what may be meaningful."),
            ("Daily context changes the picture", "A difficult night of sleep, dehydration, illness, stress, or an unusually timed meal can all change how a day feels. The goal is to understand context rather than blame one factor."),
            ("When to bring it up", "Persistent fatigue, dizziness, major changes in thirst or urination, or symptoms that worry you deserve professional guidance. Educational resources can prepare questions, not replace evaluation."),
        ],
        "notice": "Energy has many causes. Blood sugar patterns may be one part of the discussion, especially when they repeat in a recognizable way.",
        "questions": [
            "Could the energy pattern I am noticing be related to meals, sleep, medication, stress, or something else?",
            "What information would be useful to track before an appointment?",
            "Are there symptoms that should prompt more urgent medical attention?",
        ],
        "related_resource_slugs": ["post-meal-blood-sugar", "sleep-and-blood-sugar", "stress-and-glucose-patterns"],
        "nonprofit_articles": [
            {
                "title": "Brain Sugar: How Glucose Metabolism Influences Cognitive Health",
                "url": "/glucose-metabolism-and-brain-health/",
                "why": "Expands the glucose-and-brain-energy connection in the broader education library.",
            },
            {
                "title": "Continuous Glucose Monitors and More to Keep You on Track",
                "url": "/continuous-glucose-monitors-and-more-to-keep-you-on-track/",
                "why": "Adds context on trend information without treating consumer data as diagnosis.",
            },
        ],
        "video": {
            "title": "Brain Fog After Eating? Your Blood Sugar May Be the Reason",
            "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g",
            "why": "A related Mindful Diabetes video topic about glucose swings, meals, and energy.",
        },
    },
    {
        "slug": "understanding-a1c",
        "title": "Understanding A1C",
        "category": "Blood Sugar Basics",
        "meta_description": "Learn what A1C generally represents and why clinicians may use it as one part of a larger blood sugar picture.",
        "summary": "A1C is often discussed as a longer-term marker of average blood sugar, but it is not a complete picture by itself. Clinicians may interpret it alongside symptoms, history, medications, and other lab information.",
        "big_idea": "A1C is a summary marker",
        "best_lens": "Use it as one part of the conversation",
        "learning_points": ["What A1C is designed to reflect", "Why clinicians use it alongside other data", "Why individual interpretation belongs with a qualified professional"],
        "sections": [
            ("What A1C is meant to summarize", "A1C generally reflects how much glucose has attached to hemoglobin over a period of time. It can help clinicians discuss longer-term patterns rather than only a single fasting or post-meal moment."),
            ("Why it is not the whole story", "Different health situations can affect interpretation. A clinician may consider anemia, pregnancy, kidney disease, recent blood loss, medication, or other factors before drawing conclusions."),
            ("Why trends are helpful", "Changes over time may be more useful than one result by itself. Bringing a history of results and daily-life context can make the conversation clearer."),
            ("How to avoid over-reading it", "A1C does not identify every high or low moment. It also does not explain why a pattern is happening without clinical interpretation."),
            ("What to ask next", "If your clinician discusses A1C, ask how it fits with your situation, what other measurements matter, and what follow-up makes sense for you."),
        ],
        "notice": "A1C is clinical information. This page explains the concept but does not interpret anyone's result.",
        "questions": ["What does my A1C mean in the context of my overall health?", "Are there reasons this result might be harder to interpret?", "What other information should we consider?"],
        "related_resource_slugs": ["fasting-glucose-basics", "post-meal-blood-sugar", "questions-to-ask-your-doctor"],
        "nonprofit_articles": [
            {"title": "Continuous Glucose Monitors and More to Keep You on Track", "url": "/continuous-glucose-monitors-and-more-to-keep-you-on-track/", "why": "Compares different ways people encounter glucose information."},
            {"title": "Meet Buddy the Blood Sugar! A Fun Guide to Daily Blood Sugar Control", "url": "/blood-sugar-body/", "why": "Offers a plain-language introduction to blood sugar education."},
        ],
        "video": {"title": "Mindful Diabetes blood sugar education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "Continue with general blood sugar education from Mindful Diabetes."},
    },
    {
        "slug": "fasting-glucose-basics",
        "title": "Fasting glucose basics",
        "category": "Blood Sugar Basics",
        "meta_description": "Explore what fasting glucose means in general educational terms and why it may be discussed with other health markers.",
        "summary": "Fasting glucose is one snapshot of blood sugar after a period without food. It can be useful, but it does not tell the whole story without context.",
        "big_idea": "Fasting is a snapshot",
        "best_lens": "Interpret with context",
        "learning_points": ["Why fasting is used for some labs", "What fasting glucose may and may not show", "Why repeat patterns matter"],
        "sections": [
            ("Why fasting is used", "Fasting can reduce some short-term food effects before a lab test. That can make certain comparisons easier, but it still remains one piece of information."),
            ("What it may show", "A fasting value may help a clinician understand baseline glucose regulation. It does not identify every meal-related or overnight pattern."),
            ("What it cannot do alone", "A single fasting value cannot explain cause, diagnose every situation, or replace clinical judgment. Interpretation depends on the person and the circumstances."),
            ("Why preparation matters", "Following lab instructions matters because food, drinks, illness, stress, and timing can affect results. Questions about preparation should go to the ordering clinician or lab."),
            ("What to discuss", "Ask how the result fits with A1C, symptoms, medications, family history, and any patterns you have noticed."),
        ],
        "notice": "This guide is about the concept of fasting glucose, not interpretation of individual lab values.",
        "questions": ["Was this test meant to be fasting, and did anything affect the result?", "How does this compare with my prior results?", "Do we need any follow-up testing?"],
        "related_resource_slugs": ["understanding-a1c", "post-meal-blood-sugar", "metabolic-health-basics"],
        "nonprofit_articles": [
            {"title": "Brain Sugar: How Glucose Metabolism Influences Cognitive Health", "url": "/glucose-metabolism-and-brain-health/", "why": "Connects glucose education to energy and brain-health learning."},
            {"title": "Continuous Glucose Monitors and More to Keep You on Track", "url": "/continuous-glucose-monitors-and-more-to-keep-you-on-track/", "why": "Explains why different measurements answer different questions."},
        ],
        "video": {"title": "Mindful Diabetes glucose education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A general video pathway for blood sugar education."},
    },
    {
        "slug": "post-meal-blood-sugar",
        "title": "Post-meal blood sugar",
        "category": "Blood Sugar Basics",
        "meta_description": "Understand why glucose may rise after meals and why repeated post-meal patterns can matter more than a single spike.",
        "summary": "Blood sugar commonly changes after eating. The size and shape of that change can depend on food, timing, activity, sleep, stress, medication, and individual biology.",
        "big_idea": "Meals create curves",
        "best_lens": "Look for repeated patterns",
        "learning_points": ["Why post-meal rises happen", "What shapes the curve after eating", "Why one meal does not define health"],
        "sections": [
            ("Why glucose rises after meals", "Carbohydrate-containing foods are broken down into glucose, and the body responds with insulin and other signals. A rise after eating can be expected."),
            ("Why meals affect people differently", "Fiber, protein, fat, portion size, meal order, activity, sleep, stress, medications, and digestion can all shape the post-meal pattern."),
            ("Why single spikes can mislead", "One unusual meal or stressful day may not represent a person's usual pattern. Repeated trends are often more useful for conversation."),
            ("Why context helps", "Notes about what was eaten, when movement happened, and how the day was going can make post-meal patterns easier to discuss with a clinician."),
            ("When to ask for guidance", "If post-meal symptoms, high readings, or concerns repeat, ask a qualified healthcare professional how to interpret them safely."),
        ],
        "notice": "Post-meal glucose education should not become a reason to fear food or make drastic changes without professional guidance.",
        "questions": ["Which post-meal patterns should I pay attention to?", "Would any tracking be useful, and for how long?", "How can I discuss meals without turning every number into a judgment?"],
        "related_resource_slugs": ["blood-sugar-and-energy", "food-patterns-and-blood-sugar", "movement-and-insulin-sensitivity"],
        "nonprofit_articles": [
            {"title": "Mindful Eating: The Key to Blood Sugar Management", "url": "/mindful-eating-the-key-to-blood-sugar-management/", "why": "Adds a practical food-awareness lens without prescribing a single diet."},
            {"title": "Continuous Glucose Monitors and More to Keep You on Track", "url": "/continuous-glucose-monitors-and-more-to-keep-you-on-track/", "why": "Provides context for glucose trend tools."},
        ],
        "video": {"title": "Mindful Diabetes post-meal education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for meal and blood sugar learning."},
    },
    {
        "slug": "insulin-resistance",
        "title": "What is insulin resistance?",
        "category": "Metabolic Health",
        "meta_description": "Learn how cells can become less responsive to insulin and why that may matter for blood sugar, energy, and metabolic health.",
        "summary": "Insulin resistance is a general term for reduced responsiveness to insulin signals. It can develop gradually and is often discussed alongside blood sugar, energy, liver health, movement, sleep, and other metabolic patterns.",
        "big_idea": "Signals can become harder to hear",
        "best_lens": "Think gradual, not sudden",
        "learning_points": ["How insulin signaling works at a high level", "Why insulin resistance can build slowly", "Why context matters before conclusions"],
        "sections": [
            ("Insulin is a signal", "Insulin helps cells respond to glucose and energy availability. Insulin resistance means that response may be less effective than expected."),
            ("It often develops over time", "Patterns related to body composition, activity, sleep, stress, genetics, medication, and other health factors may all be part of the broader picture."),
            ("Blood sugar may not change first", "The body can sometimes compensate for a period of time. That is one reason clinicians may look at multiple markers and patterns."),
            ("The phrase is not a personal diagnosis", "Learning the concept is different from knowing whether it applies to you. Personal interpretation belongs with qualified healthcare professionals."),
            ("Questions are useful", "A careful appointment can explore which markers, symptoms, history, or next steps are relevant without jumping to conclusions."),
        ],
        "notice": "Do not use this guide to decide that you have insulin resistance. Use it to prepare better questions.",
        "questions": ["What information would help us evaluate insulin sensitivity or metabolic health?", "Which lifestyle factors are most relevant in my case?", "Are there medications or conditions that affect this discussion?"],
        "related_resource_slugs": ["metabolic-health-basics", "movement-and-insulin-sensitivity", "type-3-diabetes"],
        "nonprofit_articles": [
            {"title": "Unlocking Brain Health: Managing Insulin Resistance for Cognitive and Diabetes Wellness", "url": "/insulin-resistance-cognitive-decline/", "why": "Connects insulin-resistance education to cognitive-health discussions."},
            {"title": "How Insulin Resistance Affects Brain Function and Neuroplasticity", "url": "/insulin-sensitivity-and-neuroplasticity/", "why": "Explores the brain-health angle with careful educational framing."},
        ],
        "video": {"title": "Mindful Diabetes insulin resistance education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related video pathway for insulin signaling and metabolic health."},
    },
    {
        "slug": "metabolic-health-basics",
        "title": "Metabolic health basics",
        "category": "Metabolic Health",
        "meta_description": "Learn the big-picture basics of metabolism, insulin, glucose, and why clinicians often look at patterns instead of isolated moments.",
        "summary": "Metabolic health is a broad educational idea involving how the body handles energy, glucose, fats, blood pressure, inflammation, sleep, movement, and other signals.",
        "big_idea": "Metabolism is a system",
        "best_lens": "Look at clusters of information",
        "learning_points": ["What metabolism means at a high level", "Why clinicians use clusters of information", "Why no single habit tells the whole story"],
        "sections": [
            ("Metabolism is more than calories", "Metabolism includes how the body stores, releases, and uses energy. Glucose, insulin, fats, liver function, muscles, and hormones all participate."),
            ("Markers cluster together", "Clinicians may consider blood pressure, blood sugar, lipids, waist measurement, sleep, medications, family history, and other information together."),
            ("Daily routines interact", "Food patterns, movement, sleep, stress, and illness can influence each other. Education is most useful when it avoids one-factor explanations."),
            ("Prevention language needs caution", "Health-supportive habits may reduce risk in some contexts, but no resource can guarantee prevention or cure."),
            ("Better questions help", "Understanding the system can help you ask what matters most for your own situation with a qualified professional."),
        ],
        "notice": "Metabolic health is a broad concept, not a score this page can calculate for you.",
        "questions": ["Which markers matter most for my current health picture?", "How often should they be reviewed?", "What routine changes would be appropriate and safe for me?"],
        "related_resource_slugs": ["insulin-resistance", "food-patterns-and-blood-sugar", "inflammation-and-metabolic-health"],
        "nonprofit_articles": [
            {"title": "Memovela: A Wellness Tracker for Insulin Resistance & Brain Health", "url": "/memovela/", "why": "Shows how daily routines can be tracked without turning education into diagnosis."},
            {"title": "Mindful Living: A Pathway to Managing Diabetes and Preventing Alzheimer's", "url": "/mindfulness-for-diabetes/", "why": "Adds a broad daily-life wellness lens."},
        ],
        "video": {"title": "Mindful Diabetes metabolic health videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for metabolic-health education."},
    },
    {
        "slug": "food-patterns-and-blood-sugar",
        "title": "Food patterns and blood sugar",
        "category": "Metabolic Health",
        "meta_description": "Explore general food-pattern education without prescribing a single diet or one-size-fits-all approach.",
        "summary": "Food patterns can influence glucose and energy trends. One meal is less important than repeated patterns over time, and personalized diet advice belongs with qualified professionals.",
        "big_idea": "Patterns beat perfection",
        "best_lens": "Notice what repeats",
        "learning_points": ["How meal patterns can influence glucose trends", "Why one meal does not define metabolic health", "Why personalized nutrition belongs with professionals"],
        "sections": [
            ("Patterns are more useful than perfection", "A single meal rarely tells the whole story. Repeated routines around meals, drinks, snacks, timing, and portions are usually more informative."),
            ("Meal composition can matter", "Fiber, protein, fat, carbohydrate amount, and food processing can all shape glucose responses. That does not mean one rigid diet is right for everyone."),
            ("Culture and access matter", "Food advice should fit budget, culture, schedule, kitchen access, preferences, and medical needs. Useful education leaves room for real life."),
            ("Avoid fear-based tracking", "Tracking food or glucose should not become punishment or anxiety. If monitoring increases distress, talk with a professional."),
            ("Use food questions constructively", "A clinician or registered dietitian can help turn patterns into safe next steps, especially when medications or other health conditions are involved."),
        ],
        "notice": "This page does not prescribe a diet. It supports safer, better-informed conversations about food patterns.",
        "questions": ["Which meal patterns seem most relevant to the trends I notice?", "Would a dietitian be helpful for my situation?", "Are there medications or conditions that change food guidance?"],
        "related_resource_slugs": ["post-meal-blood-sugar", "metabolic-health-basics", "questions-to-ask-your-doctor"],
        "nonprofit_articles": [
            {"title": "Mindful Eating: The Key to Blood Sugar Management", "url": "/mindful-eating-the-key-to-blood-sugar-management/", "why": "A practical article about food awareness and blood sugar education."},
            {"title": "The MIND Diet: Boost Brain Health and Combat Diabetes & Alzheimer's", "url": "/mind-diet/", "why": "Adds a brain-health nutrition pathway with broader context."},
        ],
        "video": {"title": "Mindful Diabetes food and blood sugar videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related video pathway for food-pattern education."},
    },
    {
        "slug": "inflammation-and-metabolic-health",
        "title": "Inflammation and metabolic health",
        "category": "Metabolic Health",
        "meta_description": "Explore inflammation as a broad educational topic that researchers also study in relation to metabolic health.",
        "summary": "Inflammation is a complex body process. Researchers study how chronic inflammatory patterns may relate to metabolic health, but the topic should be explained carefully and without overclaiming.",
        "big_idea": "Inflammation is nuanced",
        "best_lens": "Avoid one-cause explanations",
        "learning_points": ["Why inflammation is a broad term", "How researchers study its relationship to metabolism", "Why symptoms need clinical interpretation"],
        "sections": [
            ("Inflammation can be protective", "Short-term inflammation can help the body respond to injury or infection. Problems may arise when inflammatory signaling becomes persistent or poorly regulated."),
            ("Metabolism and immunity communicate", "Fat tissue, liver, muscles, blood vessels, and immune signals can interact. Researchers study these relationships in diabetes and cardiovascular health."),
            ("Do not self-diagnose inflammation", "Many symptoms are nonspecific. Lab markers and clinical context need professional interpretation."),
            ("Lifestyle claims need caution", "Sleep, movement, food patterns, smoking, stress, and medical care can all be part of inflammation discussions, but no single habit fixes every inflammatory process."),
            ("Ask what is actionable", "A useful appointment focuses on what is relevant, measurable, and appropriate for your health situation."),
        ],
        "notice": "Inflammation language is often overused online. This guide keeps the concept educational and cautious.",
        "questions": ["Are there signs or labs that make inflammation relevant in my case?", "What conditions should be considered before assuming a cause?", "Which steps are evidence-informed and safe for me?"],
        "related_resource_slugs": ["metabolic-health-basics", "brain-health-and-alzheimers", "lifestyle-habits"],
        "nonprofit_articles": [
            {"title": "The Brain's Immune Conversation: What Microglia and Astrocytes Reveal About Alzheimer's Disease", "url": "/microglia-astrocytes-alzheimers/", "why": "Connects immune signaling to brain-health education."},
            {"title": "Antioxidants & Brain Health: A Powerful Defense Against Type III Diabetes", "url": "/antioxidants-and-diabetes/", "why": "Shows how inflammation-related claims need careful framing."},
        ],
        "video": {"title": "Mindful Diabetes inflammation and metabolic health videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for inflammation and metabolism education."},
    },
    {
        "slug": "type-3-diabetes",
        "title": "What does Type 3 diabetes mean?",
        "category": "Brain Health",
        "meta_description": "Understand Type 3 diabetes as an informal research-related phrase connected to brain insulin resistance and Alzheimer's disease education.",
        "summary": "Type 3 diabetes is an informal phrase sometimes used in research and public education to discuss links between insulin resistance, brain metabolism, and Alzheimer's disease. It is not presented here as an official clinical diagnosis.",
        "big_idea": "A research phrase, not a diagnosis",
        "best_lens": "Use careful language",
        "learning_points": ["Why the phrase became popular", "How it relates to research on brain insulin signaling", "Why it should not be treated as an official diagnosis"],
        "sections": [
            ("The phrase is informal", "Type 3 diabetes is not a standard clinical diagnosis like type 1 or type 2 diabetes. It is usually used to introduce research questions about insulin signaling and brain health."),
            ("Why people connect it to Alzheimer's research", "Researchers have studied insulin resistance, glucose metabolism, inflammation, blood vessels, and other pathways in relation to cognitive decline and Alzheimer's disease."),
            ("Why the phrase can mislead", "Informal language can make a complex research area sound settled. It should not be used to diagnose a person or claim that diabetes inevitably leads to dementia."),
            ("What careful education can do", "The phrase can open a conversation about metabolic and brain health if it stays grounded in evidence and avoids fear-based claims."),
            ("What to discuss with professionals", "Questions about memory symptoms, diabetes care, family history, or cognitive concerns belong with qualified healthcare professionals."),
        ],
        "notice": "Mindful Diabetes uses Type 3 diabetes language only with careful framing. It is an educational research-related phrase, not an official diagnosis.",
        "questions": ["What does current research suggest, and what remains uncertain?", "Are my cognitive concerns something that should be evaluated?", "Which metabolic health steps are appropriate for my situation?"],
        "related_resource_slugs": ["brain-health-and-alzheimers", "insulin-resistance", "cognitive-health-and-daily-habits"],
        "nonprofit_articles": [
            {"title": "What is Type 3 Diabetes? Unraveling the Mystery", "url": "/type-3-diabetes/", "why": "The broader Mindful Diabetes article on the informal phrase."},
            {"title": "The Diabetes-Alzheimer's Connection: Unraveling the Link", "url": "/connecting-diabetes-and-alzheimers/", "why": "Expands the diabetes and Alzheimer's education pathway."},
        ],
        "video": {"title": "Mindful Diabetes Type 3 diabetes education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related video pathway for careful Type 3 diabetes framing."},
    },
    {
        "slug": "brain-health-and-alzheimers",
        "title": "Brain health and Alzheimer's education",
        "category": "Brain Health",
        "meta_description": "Build a clearer foundation for learning about metabolism, inflammation, cognitive health, and emerging Alzheimer's research.",
        "summary": "Brain health is broader than one diagnosis. Education about Alzheimer's disease can include metabolism, blood vessels, sleep, hearing, movement, inflammation, and social connection without promising prevention or cure.",
        "big_idea": "Brain health has many inputs",
        "best_lens": "Avoid single-cause stories",
        "learning_points": ["How brain health is bigger than one diagnosis", "Why metabolism enters the conversation", "Why research does not equal certainty"],
        "sections": [
            ("Alzheimer's is complex", "Alzheimer's disease involves multiple biological pathways. Metabolism is one area researchers study, but it is not the only explanation."),
            ("Blood vessels and inflammation matter too", "Cardiovascular health, immune signaling, sleep, hearing, movement, and social factors can all enter brain-health education."),
            ("Research language needs humility", "Emerging science can be promising and still incomplete. Education should distinguish hypotheses, associations, and established clinical guidance."),
            ("Daily habits are supportive, not guarantees", "Healthy routines may support overall health, but no habit can guarantee that Alzheimer's disease will be prevented."),
            ("Evaluation matters", "Memory concerns, confusion, or changes in daily function deserve clinical attention rather than self-diagnosis."),
        ],
        "notice": "This guide supports brain-health learning without making prevention, treatment, or prediction claims.",
        "questions": ["Which brain-health risk factors are relevant to me?", "When should memory changes be evaluated?", "How do metabolic markers fit into the broader picture?"],
        "related_resource_slugs": ["type-3-diabetes", "cognitive-health-and-daily-habits", "inflammation-and-metabolic-health"],
        "nonprofit_articles": [
            {"title": "Inside the Alzheimer's Clinical-Trial Landscape: What Researchers Were Testing in June 2026", "url": "/alzheimers-clinical-trials-june-2026/", "why": "Shows the breadth and uncertainty of current Alzheimer's research."},
            {"title": "Amyloid Plaques Are Not the Whole Story: What New Alzheimer's Research Is Teaching Us", "url": "/amyloid-plaques-alzheimers-research/", "why": "Adds nuance to Alzheimer's education beyond one pathway."},
        ],
        "video": {"title": "Mindful Diabetes brain health education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related video pathway for brain-health education."},
    },
    {
        "slug": "cognitive-health-and-daily-habits",
        "title": "Cognitive health and daily habits",
        "category": "Brain Health",
        "meta_description": "Learn how daily routines are commonly discussed in brain health education without making prevention or cure claims.",
        "summary": "Daily habits such as sleep, movement, food patterns, stress management, hearing support, social connection, and medical follow-up are often discussed in cognitive-health education.",
        "big_idea": "Routines can support resilience",
        "best_lens": "Supportive, not guaranteed",
        "learning_points": ["Why routines are part of brain-health education", "How supportive habits differ from cure claims", "Why consistency can be more useful than perfection"],
        "sections": [
            ("Habits influence the environment around the brain", "Sleep, movement, nutrition, stress, and social connection can shape general health. They are supportive factors, not guaranteed protection."),
            ("Cognitive health is not only memory", "Attention, mood, hearing, vision, medication effects, sleep quality, and medical conditions can all affect how thinking feels day to day."),
            ("Small changes can be realistic", "Consistent, modest routines may be easier to sustain than dramatic changes. The best plan is one that fits the person's life and medical context."),
            ("Medical concerns still need care", "New, worsening, or concerning cognitive symptoms should be evaluated. Lifestyle education should never delay clinical assessment."),
            ("Questions create a bridge", "A resource can help you prepare questions about sleep, movement, medication, mood, hearing, or metabolic health for a professional visit."),
        ],
        "notice": "Daily habits can support overall health, but they do not guarantee prevention of cognitive decline or Alzheimer's disease.",
        "questions": ["Which daily routines are most realistic for me to adjust?", "Could sleep, mood, hearing, or medication affect cognition?", "When should cognitive changes be evaluated?"],
        "related_resource_slugs": ["lifestyle-habits", "sleep-and-blood-sugar", "brain-health-and-alzheimers"],
        "nonprofit_articles": [
            {"title": "Sleep and the Aging Brain: What Patterns of Rest May Reveal About Dementia Risk", "url": "/sleep-aging-brain-dementia-risk/", "why": "Connects sleep patterns to brain-health research."},
            {"title": "Long-Term Potentiation and Exercise: Strengthening Brain and Body Connection", "url": "/long-term-potentiation/", "why": "Adds an education pathway on movement and brain signaling."},
        ],
        "video": {"title": "Mindful Diabetes cognitive health videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related video pathway for cognition and daily habits."},
    },
    {
        "slug": "lifestyle-habits",
        "title": "Lifestyle habits",
        "category": "Daily Habits",
        "meta_description": "Review general education around movement, food patterns, sleep, stress, and daily routines that support metabolic health.",
        "summary": "Lifestyle habits interact with each other. Movement, food patterns, sleep, stress, hydration, medication routines, and social support can all shape metabolic health conversations.",
        "big_idea": "Habits interact",
        "best_lens": "Consistency over perfection",
        "learning_points": ["How habits interact with each other", "Why consistency often matters more than perfection", "Why individual plans should be professional"],
        "sections": [
            ("Habits are connected", "Sleep can influence appetite and stress. Stress can influence movement and meals. Food timing can influence energy. It is rarely one isolated behavior."),
            ("Perfection is not the goal", "Sustainable routines are usually more useful than short bursts of intensity. Small repeated changes can be easier to maintain."),
            ("Medical context matters", "Medication, pregnancy, kidney disease, eating-disorder history, disability, pain, and other factors can change what advice is safe."),
            ("Tracking should be gentle", "A simple pattern note can help a conversation. Tracking should not become shame, fear, or constant self-monitoring."),
            ("Choose one next question", "A practical starting point is to ask which habit area is most relevant, safe, and realistic right now."),
        ],
        "notice": "Lifestyle education should support care conversations, not replace individualized medical guidance.",
        "questions": ["Which habit area is most relevant to focus on first?", "Are there medical limits I should consider?", "How can I track patterns without over-monitoring?"],
        "related_resource_slugs": ["movement-and-insulin-sensitivity", "sleep-and-blood-sugar", "stress-and-glucose-patterns"],
        "nonprofit_articles": [
            {"title": "Memovela: A Wellness Tracker for Insulin Resistance & Brain Health", "url": "/memovela/", "why": "Shows a supportive habit-tracking approach."},
            {"title": "Mindful Living: A Pathway to Managing Diabetes and Preventing Alzheimer's", "url": "/mindfulness-for-diabetes/", "why": "Adds a daily-life wellness perspective."},
        ],
        "video": {"title": "Mindful Diabetes daily habit videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for daily habit education."},
    },
    {
        "slug": "movement-and-insulin-sensitivity",
        "title": "Movement and insulin sensitivity",
        "category": "Daily Habits",
        "meta_description": "Learn how regular movement may support metabolic health in general terms without turning education into a treatment plan.",
        "summary": "Movement can help muscles use energy and is often discussed in insulin-sensitivity education. The safest movement plan depends on health status, ability, medication, and professional guidance.",
        "big_idea": "Muscles help use energy",
        "best_lens": "Start with safe consistency",
        "learning_points": ["Why movement often enters metabolic health conversations", "How consistency may matter more than intensity", "Why safety and individual context matter"],
        "sections": [
            ("Muscles are metabolically active", "Muscles use glucose and other fuels. Regular movement is often discussed because it can support overall metabolic health."),
            ("Different forms can help", "Walking, strength training, mobility work, household activity, and short movement breaks may all matter depending on the person."),
            ("Intensity is not the only variable", "Frequency, consistency, timing, recovery, and enjoyment can influence whether movement becomes sustainable."),
            ("Safety comes first", "People with symptoms, diabetes medications, neuropathy, heart concerns, pregnancy, pain, or other conditions should ask what is safe."),
            ("Movement is not a prescription here", "This page explains concepts. A personalized plan belongs with a qualified professional."),
        ],
        "notice": "Do not start intense exercise or change medication based on this guide. Ask for individual guidance when needed.",
        "questions": ["What kinds of movement are safe for me?", "Should I consider glucose monitoring around activity?", "Are there symptoms that should make me stop and seek care?"],
        "related_resource_slugs": ["insulin-resistance", "lifestyle-habits", "post-meal-blood-sugar"],
        "nonprofit_articles": [
            {"title": "Simple Exercises to Stabilize Blood Sugar & Boost Brain Health", "url": "/low-impact-exercise/", "why": "Offers approachable movement education."},
            {"title": "Exercise as Medicine: Managing Diabetes and Reducing Alzheimer's Risk", "url": "/exercise-as-medicine-managing-diabetes-and-reducing-alzheimers-risk/", "why": "Explores movement as a health-supportive topic with broader context."},
        ],
        "video": {"title": "Mindful Diabetes movement education videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for movement and metabolic health."},
    },
    {
        "slug": "sleep-and-blood-sugar",
        "title": "Sleep and blood sugar",
        "category": "Daily Habits",
        "meta_description": "Educational guidance on how sleep quality and routine may relate to blood sugar, energy, and metabolic health patterns.",
        "summary": "Sleep affects hormones, appetite signals, energy, attention, and stress response. That is why sleep often comes up in conversations about blood sugar patterns.",
        "big_idea": "Sleep influences the next day",
        "best_lens": "Quality and consistency matter too",
        "learning_points": ["Why sleep can affect more than fatigue alone", "How sleep routines may shape metabolic patterns", "What repeated sleep concerns are worth discussing"],
        "sections": [
            ("Why a rough night can echo through the next day", "Poor sleep can affect hunger, cravings, focus, mood, and how manageable routines feel. That may shape glucose-related patterns directly and indirectly."),
            ("Why routines matter beyond total hours", "Sleep duration is only one part of the picture. Timing, regularity, sleep quality, and possible sleep disorders may also matter."),
            ("Why one bad night does not define everything", "Many people have occasional restless nights. Educational conversations are more useful when they focus on repeated sleep patterns."),
            ("How sleep affects other habits", "A rough night can make meals less regular, movement less appealing, and stress harder to manage. Sleep often interacts with many other habits."),
            ("When the topic may deserve attention", "Snoring, waking often, feeling unrefreshed, or daytime sleepiness may be worth discussing with a qualified healthcare professional."),
        ],
        "notice": "Repeated sleep concerns can be worth discussing, especially when they line up with energy or glucose-related patterns.",
        "questions": ["Could sleep quality be relevant to the patterns I am noticing?", "Are there signs that should prompt evaluation for a sleep disorder?", "What kind of sleep tracking, if any, would be useful to review?"],
        "related_resource_slugs": ["blood-sugar-and-energy", "stress-and-glucose-patterns", "lifestyle-habits"],
        "nonprofit_articles": [
            {"title": "The Sleep-Diabetes Nexus: Understanding the Importance of Quality Rest", "url": "/the-sleep-diabetes-nexus-understanding-the-importance-of-quality-rest/", "why": "Direct match for sleep and blood-sugar education."},
            {"title": "Nighttime Balance: Unlocking Sleep's Role in Diabetes Control", "url": "/sleep-and-diabetes-management/", "why": "Adds another Mindful Diabetes sleep education pathway."},
        ],
        "video": {"title": "Nighttime Balance Unlocking Sleep's Role in Diabetes Control", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related video topic for sleep and glucose routines."},
    },
    {
        "slug": "stress-and-glucose-patterns",
        "title": "Stress and glucose patterns",
        "category": "Daily Habits",
        "meta_description": "Learn how stress hormones and routines may influence energy and glucose patterns in general educational terms.",
        "summary": "Stress can influence hormones, sleep, meals, movement, and medication routines. For glucose-related education, the pattern usually matters more than one stressful moment.",
        "big_idea": "Stress affects routines and signals",
        "best_lens": "Look for repeated links",
        "learning_points": ["Why stress can affect more than mood", "How stress can indirectly change glucose-related routines", "Why support matters"],
        "sections": [
            ("Stress can change body signals", "Stress hormones may influence glucose regulation, energy, appetite, and sleep. The effect can vary by person and situation."),
            ("Stress changes routines too", "A stressful week can affect meals, movement, alcohol use, sleep, medication timing, and self-care. Those indirect effects often matter."),
            ("Patterns are more useful than blame", "The goal is not to blame stress for every number. It is to notice whether repeated patterns deserve attention."),
            ("Support is part of health", "Stress management may include professional support, social support, routines, rest, or care for anxiety, depression, grief, or trauma."),
            ("Ask when it is too much", "Persistent distress, panic, depression, or thoughts of self-harm require timely support from qualified professionals or emergency services."),
        ],
        "notice": "Stress education should be compassionate. It should not turn health patterns into personal blame.",
        "questions": ["Do stress patterns seem to line up with sleep, meals, movement, or glucose trends?", "What support options are appropriate for me?", "Are there mental-health symptoms that need professional care?"],
        "related_resource_slugs": ["sleep-and-blood-sugar", "blood-sugar-and-energy", "lifestyle-habits"],
        "nonprofit_articles": [
            {"title": "The Role of Stress in Diabetes: Strategies for Stress Management", "url": "/stress-in-diabetes-and-strategies-for-stress-management/", "why": "Directly expands stress and diabetes education."},
            {"title": "Emotional Well-being and Blood Sugar: Navigating the Ups and Downs", "url": "/emotional-diabetes-management-and-its-connection-with-blood-sugar/", "why": "Adds emotional-health context for blood sugar education."},
        ],
        "video": {"title": "Mindful Diabetes stress and glucose videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for stress and daily routines."},
    },
    {
        "slug": "questions-to-ask-your-doctor",
        "title": "Questions to ask your doctor",
        "category": "Working With Your Doctor",
        "meta_description": "Prepare thoughtful, practical questions for a qualified healthcare professional without replacing their guidance.",
        "summary": "Good questions can turn general health education into a safer, more useful appointment. Bring patterns, context, and concerns rather than conclusions.",
        "big_idea": "Bring questions, not conclusions",
        "best_lens": "Prepare for shared understanding",
        "learning_points": ["How to bring patterns instead of conclusions", "What notes help most in appointments", "Why individual guidance matters"],
        "sections": [
            ("Start with what you noticed", "Describe the pattern, timing, symptoms, and context. Avoid arriving with a self-diagnosis based only on online reading."),
            ("Bring useful details", "Medication lists, recent labs, sleep changes, meal timing, activity patterns, symptoms, and family history can all help a clinician understand the picture."),
            ("Ask what matters most", "A professional can help prioritize which markers, symptoms, or next steps are relevant rather than trying to solve every question at once."),
            ("Clarify safety boundaries", "Ask what symptoms require urgent care, what changes should not be made without guidance, and what information is worth tracking."),
            ("Leave with a plan", "Useful appointments often end with next steps, follow-up timing, and clarity about who to contact if something changes."),
        ],
        "notice": "This guide helps prepare conversations. It does not replace professional evaluation or urgent care.",
        "questions": ["What patterns are most important for us to discuss?", "What should I track, and what should I stop tracking?", "What symptoms or results should prompt urgent care?"],
        "related_resource_slugs": ["understanding-a1c", "fasting-glucose-basics", "food-patterns-and-blood-sugar"],
        "nonprofit_articles": [
            {"title": "Continuous Glucose Monitors and More to Keep You on Track", "url": "/continuous-glucose-monitors-and-more-to-keep-you-on-track/", "why": "Helps readers think about data to bring into clinical conversations."},
            {"title": "Traveling with Diabetes: Tips for a Stress-Free Journey", "url": "/traveling-with-diabetes-tips-for-a-stress-free-journey/", "why": "Shows practical question-led planning for real life."},
        ],
        "video": {"title": "Mindful Diabetes appointment preparation videos", "url": "https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g", "why": "A related pathway for preparing better health questions."},
    },
]


def all_resources():
    return [normalize_resource(resource) for resource in RESOURCE_ARTICLES]


def resource_by_slug(slug):
    for resource in RESOURCE_ARTICLES:
        if resource["slug"] == slug:
            return normalize_resource(resource)
    return None


def resources_grouped_by_category():
    resources = all_resources()
    return [
        {
            "name": category,
            "slug": slugify_category(category),
            "resources": [resource for resource in resources if resource["category"] == category],
        }
        for category in CATEGORY_ORDER
    ]


def related_resources(resource):
    by_slug = {item["slug"]: item for item in all_resources()}
    return [
        by_slug[slug]
        for slug in resource.get("related_resource_slugs", [])
        if slug in by_slug
    ]


def normalize_resource(resource):
    item = deepcopy(resource)
    item["canonical_path"] = f"/resources/{item['slug']}"
    item["external_url"] = f"{AI_RESOURCES_URL}/{item['slug']}"
    item["review_date"] = REVIEW_DATE
    item["published_date"] = PUBLISHED_DATE
    item["review_note"] = REVIEW_NOTE
    item["author"] = AUTHOR_NAME
    item["responsible_editor"] = RESPONSIBLE_EDITOR
    item["disclaimer"] = DISCLAIMER
    item["sources"] = item.get("sources") or COMMON_SOURCES
    item["category_slug"] = slugify_category(item["category"])
    return item


def slugify_category(category):
    return category.lower().replace("&", "and").replace(" ", "-")
