import csv
import re
import requests
import feedparser
from urllib.parse import quote
from xml.etree import ElementTree
from datetime import date


def load_journal_scores():
    scores = {}

    try:
        with open("journal_scores.csv", "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                journal = row["journal"].strip().lower()
                score = float(row["score"])
                scores[journal] = score

    except FileNotFoundError:
        print("journal_scores.csv not found. Using default score of 0.")

    return scores


def contains_any(text, keywords):
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, text):
            return True
    return False


def category_to_id(category):
    return (
        category.lower()
        .replace(" / ", "-")
        .replace(" ", "-")
        .replace("&", "and")
        .replace(",", "")
    )


def get_news_feed():
    search_terms = [
        "hypereosinophilia",
        "hypereosinophilic syndrome",
        "eosinophilia",
    ]

    news_items = []
    seen_titles = set()

    for term in search_terms:
        query = quote(term)

        rss_url = (
            f"https://news.google.com/rss/search?"
            f"q={query}&hl=en-US&gl=US&ceid=US:en"
        )

        feed = feedparser.parse(rss_url)

        for entry in feed.entries[:5]:
            title = entry.get("title", "No title")

            if title in seen_titles:
                continue

            seen_titles.add(title)

            news_items.append({
                "term": term,
                "title": title,
                "link": entry.get("link", ""),
                "published": entry.get("published", "Date not available"),
            })

    return news_items

def get_clinical_trials():

    search_terms = [
        "hypereosinophilic syndrome",
        "hypereosinophilia",
    ]

    trials = []
    seen_nct = set()

    for term in search_terms:

        url = "https://clinicaltrials.gov/api/v2/studies"

        params = {
            "query.term": term,
            "pageSize": 20,
            "format": "json",
        }

        response = requests.get(url, params=params)

        print("ClinicalTrials.gov search:", term, response.status_code)

        if response.status_code != 200:
            continue

        data = response.json()

        studies = data.get("studies", [])

        print("Trials found for", term, ":", len(studies))

        for study in studies:

            protocol = study.get("protocolSection", {})

            identification = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            design_module = protocol.get("designModule", {})
            conditions_module = protocol.get("conditionsModule", {})
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})

            nct = identification.get("nctId", "")

            if not nct or nct in seen_nct:
                continue

            title = identification.get(
                "briefTitle",
                "No title"
            )

            status = status_module.get(
                "overallStatus",
                "Unknown"
            )

            phases = design_module.get("phases", [])

            phase = (
                ", ".join(phases)
                if phases
                else "Not specified"
            )

            conditions = conditions_module.get(
                "conditions",
                []
            )

            condition = (
                ", ".join(conditions)
                if conditions
                else "Not specified"
            )

            trial_text = (
                f"{title} {condition}"
            ).lower()

            keep_terms = [
                "hypereosinophilic syndrome",
                "hypereosinophilia",
                "hypereosinophilic",
            ]

            if not any(
                term in trial_text
                for term in keep_terms
            ):
                continue

            seen_nct.add(nct)

            sponsor_info = sponsor_module.get(
                "leadSponsor",
                {}
            )

            sponsor = sponsor_info.get(
                "name",
                "Unknown"
            )

            trials.append({
                "title": title,
                "status": status,
                "phase": phase,
                "condition": condition,
                "sponsor": sponsor,
                "nct": nct,
                "link":
                    f"https://clinicaltrials.gov/study/{nct}",
            })

    print(
        "Total unique clinical trials found:",
        len(trials)
    )

    return trials

def assign_disease_category(title, abstract):
    text = f"{title} {abstract}".lower()

    categories = [
        ("EGPA / Churg-Strauss / Vasculitis", [
            "egpa", "anca", "vasculitis", "churg-strauss", "churg strauss",
            "eosinophilic granulomatosis with polyangiitis",
            "anca-associated vasculitis", "polyangiitis",
        ]),

        ("Infectious / Parasitic Eosinophilia", [
            "strongyloides", "strongyloidiasis", "toxocara", "toxocariasis",
            "paragonimus", "paragonimiasis", "ancylostoma", "ankylostomiasis",
            "hookworm", "helminth", "helminthic", "schistosomiasis",
            "schistosoma", "fasciola", "fascioliasis", "trichinella",
            "trichinellosis", "ascaris", "ascariasis", "filariasis",
            "loiasis", "toxoplasma", "toxoplasmosis", "parasitic eosinophilia",
            "tropical eosinophilia", "coccidioidomycosis", "histoplasmosis",
            "aspergillosis", "ebv", "epstein-barr virus", "ebstein-barr virus",
            "covid-19", "sars-cov-2",
        ]),

        ("Eosinophilic Leukemia / Hematologic Neoplasms", [
            "eosinophilic leukemia", "chronic eosinophilic leukemia",
            "pdgfra", "pdgfrb", "fgfr1", "pcm1-jak2",
            "myeloid/lymphoid", "myeloid lymphoid", "systemic mastocytosis",
        ]),

        ("Hypereosinophilic Syndrome / Hypereosinophilia", [
            "hypereosinophilic syndrome", "hypereosinophilia",
            "hypereosinophilic", "idiopathic hypereosinophilic",
        ]),

        ("Asthma / Airway Disease", [
            "asthma", "eosinophilic asthma", "severe asthma",
            "airway eosinophilia", "airway inflammation",
        ]),

        ("Chronic Rhinosinusitis / Nasal Polyps", [
            "chronic rhinosinusitis", "rhinosinusitis", "nasal polyp",
            "nasal polyps", "crswnp", "eosinophilic chronic rhinosinusitis",
        ]),

        ("Pulmonary Eosinophilic Disorders", [
            "pulmonary eosinophilia", "eosinophilic pneumonia", "abpa",
            "allergic bronchopulmonary aspergillosis", "lung eosinophilia",
        ]),

        ("Eosinophilic Esophagitis", [
            "eosinophilic esophagitis", "eosinophilic oesophagitis", "eoe",
        ]),

        ("Eosinophilic Gastrointestinal Disease", [
            "eosinophilic gastritis", "eosinophilic gastroenteritis",
            "eosinophilic colitis", "eosinophilic gastrointestinal", "egid",
        ]),

        ("DRESS / Drug Hypersensitivity", [
            "dress", "drug reaction", "drug reaction with eosinophilia",
            "drug reaction with eosinophilia and systemic symptoms",
            "drug hypersensitivity", "drug-induced eosinophilia",
            "drug induced eosinophilia", "rash", "exanthema",
            "cutaneous adverse reaction", "severe cutaneous adverse reaction",
            "scar",
        ]),

        ("Dermatologic Eosinophilic Disorders", [
            "atopic dermatitis", "wells syndrome", "eosinophilic cellulitis",
            "eosinophilic dermatosis", "skin eosinophilia",
        ]),

        ("Pediatric Eosinophilic Disorders", [
            "pediatric", "paediatric", "children", "childhood", "infant",
        ]),

        ("Basic Science / Translational Eosinophil Biology", [
            "il-5", "interleukin-5", "eosinophil activation", "cytokine",
            "pathogenesis", "pathophysiology", "signaling", "molecular",
            "transcriptomic", "genomic",
        ]),
    ]

    for category_name, keywords in categories:
        if contains_any(text, keywords):
            return category_name

    return "Other Eosinophilic Disorders"


def make_article_html(item):
    return f"""
    <article>
        <h3><a href="{item["link"]}" target="_blank">{item["title"]}</a></h3>
        <p><strong>Journal:</strong> {item["journal"]}</p>
        <p><strong>Journal Score:</strong> {item["journal_score"]}</p>
        <p><strong>Publication Date:</strong> {item["publication_date"]}</p>
        <p><strong>PubMed Link:</strong> <a href="{item["link"]}" target="_blank">{item["link"]}</a></p>
        <p><strong>Abstract:</strong> {item["abstract"]}</p>
    </article>
    <hr>
    """


journal_scores = load_journal_scores()

fda_medications = {
    "Hypereosinophilic Syndrome / Hypereosinophilia": [
        (
            "Mepolizumab (Nucala)",
            "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=125526"
        ),
        (
            "Benralizumab (Fasenra)",
            "https://www.accessdata.fda.gov/drugsatfda_docs/label/2026/761070s023lbl.pdf"
        ),
    ]
}


search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

search_params = {
    "db": "pubmed",
    "term": (
        '("hypereosinophilia" OR '
        '"hypereosinophilic syndrome" OR '
        '"eosinophilia" OR '
        '"eosinophilic leukemia") '
        'AND ("last 30 days"[dp])'
    ),
    "retmode": "json",
    "retmax": 100,
}

search_response = requests.get(search_url, params=search_params)
search_data = search_response.json()

pmids = search_data["esearchresult"]["idlist"]
total_found = search_data["esearchresult"]["count"]

articles = []

if pmids:
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }

    fetch_response = requests.get(fetch_url, params=fetch_params)
    root = ElementTree.fromstring(fetch_response.content)

    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle") or "No title available"
        journal = article.findtext(".//Journal/Title") or "Journal not available"
        pmid = article.findtext(".//PMID") or ""

        year = article.findtext(".//PubDate/Year") or ""
        month = article.findtext(".//PubDate/Month") or ""
        day = article.findtext(".//PubDate/Day") or ""
        publication_date = f"{month} {day} {year}".strip()

        abstract_parts = article.findall(".//Abstract/AbstractText")
        abstract = " ".join(part.text for part in abstract_parts if part.text)

        short_abstract = (
            abstract[:700] + "..."
            if len(abstract) > 700
            else abstract
        )

        link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        journal_score = journal_scores.get(journal.lower(), 0)
        disease_category = assign_disease_category(title, abstract)

        articles.append({
            "title": title,
            "journal": journal,
            "publication_date": publication_date,
            "pmid": pmid,
            "link": link,
            "abstract": short_abstract,
            "journal_score": journal_score,
            "disease_category": disease_category,
        })


category_order = [
    "EGPA / Churg-Strauss / Vasculitis",
    "Infectious / Parasitic Eosinophilia",
    "Eosinophilic Leukemia / Hematologic Neoplasms",
    "Hypereosinophilic Syndrome / Hypereosinophilia",
    "Asthma / Airway Disease",
    "Chronic Rhinosinusitis / Nasal Polyps",
    "Pulmonary Eosinophilic Disorders",
    "Eosinophilic Esophagitis",
    "Eosinophilic Gastrointestinal Disease",
    "DRESS / Drug Hypersensitivity",
    "Dermatologic Eosinophilic Disorders",
    "Pediatric Eosinophilic Disorders",
    "Basic Science / Translational Eosinophil Biology",
    "Other Eosinophilic Disorders",
]

articles_html = ""

articles_html += """
<h2>Topics</h2>
<ul>
"""

for category in category_order:
    category_articles = [
        article for article in articles
        if article["disease_category"] == category
    ]

    if category_articles:
        category_id = category_to_id(category)

        articles_html += f"""
        <li>
            <a href="#{category_id}">{category}</a>
            ({len(category_articles)})
        """

        if category in fda_medications:
            articles_html += " — FDA-approved medications: "

            medication_links = []

            for med_name, med_link in fda_medications[category]:
                medication_links.append(
                    f'<a href="{med_link}" target="_blank">{med_name}</a>'
                )

            articles_html += ", ".join(medication_links)

        articles_html += "</li>"

articles_html += """
</ul>
"""

clinical_trials = get_clinical_trials()

articles_html += """
<h2>Clinical Trials</h2>
<p>Clinical trials related to hypereosinophilia and eosinophilic disorders.</p>
<ul>
"""

if clinical_trials:
    for trial in clinical_trials:
        articles_html += f"""
        <li>
            <strong>
                <a href="{trial['link']}" target="_blank">
                    {trial['title']}
                </a>
            </strong>
            <br>
            Status: {trial['status']}
            <br>
            Phase: {trial['phase']}
            <br>
            Sponsor: {trial['sponsor']}
            <br>
            NCT: {trial['nct']}
        </li>
        <br>
        """
else:
    articles_html += "<li>No clinical trials found.</li>"

articles_html += "</ul>"

news_items = get_news_feed()
print("News items found:", len(news_items))

articles_html += """
<h2>Eosinophilia News & Updates</h2>
<p>
Recent news items related to hypereosinophilia,
hypereosinophilic syndrome, and eosinophilia.
</p>
<ul>
"""

if news_items:
    for item in news_items:
        articles_html += f"""
        <li>
            <strong>{item["term"]}:</strong>
            <a href="{item["link"]}" target="_blank">{item["title"]}</a>
            <br>
            <small>{item["published"]}</small>
        </li>
        """
else:
    articles_html += "<li>No recent news items found.</li>"

articles_html += """
</ul>

<p>
Articles are grouped by disease area. Within each disease area,
articles are sorted by journal score, highest first.
</p>
"""

if articles:
    for category in category_order:
        category_articles = [
            article for article in articles
            if article["disease_category"] == category
        ]

        category_articles.sort(
            key=lambda x: x["journal_score"],
            reverse=True
        )

        if category_articles:
            category_id = category_to_id(category)

            articles_html += f"""
            <h2 id="{category_id}">{category}</h2>
            <p><a href="#top">Back to top</a></p>
            """

            for item in category_articles:
                articles_html += make_article_html(item)
else:
    articles_html += "<p>No PubMed articles found in the prior 30 days.</p>"


html = f"""
<html>

<head>
    <title>Hypereosinophilia Research Updates</title>

    <style>

    body {{
        font-family: Arial, sans-serif;
        margin: 20px;
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}

    .header-text {{
        max-width: 75%;
    }}

    .header-image img {{
        width: 300px;
        border-radius: 10px;
    }}

    </style>

</head>

<body id="top">

    <div class="header">

        <div class="header-text">

            <h1>Hypereosinophilia Research Updates</h1>

            <p>
                Updated: {date.today()}
            </p>

            <p>
                Total citations found in prior 30 days:
                {total_found}
            </p>

        </div>

        <div class="header-image">

            <img src="eosinophil.png"
                 alt="Eosinophil">

        </div>

    </div>

    {articles_html}

</body>

</html>
"""


with open("index.html", "w", encoding="utf-8") as file:
    file.write(html)


print("Website updated successfully: index.html")
print("Total citations found:", total_found)

for category in category_order:
    count = len([
        article for article in articles
        if article["disease_category"] == category
    ])

    print(f"{category}: {count}")