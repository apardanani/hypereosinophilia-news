import csv
import requests
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


def assign_disease_category(title, abstract):
    text = f"{title} {abstract}".lower()

    categories = [
        (
            "Hypereosinophilic Syndrome / Hypereosinophilia",
            [
                "hypereosinophilic syndrome",
                "hypereosinophilia",
                "hypereosinophilic",
                "idiopathic hypereosinophilic",
                "hes",
            ],
        ),
        (
            "Eosinophilic Leukemia / Hematologic Neoplasms",
            [
                "eosinophilic leukemia",
                "chronic eosinophilic leukemia",
                "cel",
                "myeloid/lymphoid neoplasm",
                "pdgfra",
                "pdgfrb",
                "fgfr1",
                "pcm1-jak2",
                "systemic mastocytosis",
            ],
        ),
        (
            "EGPA / Churg-Strauss / Vasculitis",
            [
                "eosinophilic granulomatosis with polyangiitis",
                "egpa",
                "churg-strauss",
                "churg strauss",
                "vasculitis",
                "anca",
            ],
        ),
        (
            "Asthma / Airway Disease",
            [
                "asthma",
                "eosinophilic asthma",
                "severe asthma",
                "airway eosinophilia",
                "airway inflammation",
            ],
        ),
        (
            "Chronic Rhinosinusitis / Nasal Polyps",
            [
                "chronic rhinosinusitis",
                "rhinosinusitis",
                "nasal polyp",
                "nasal polyps",
                "crsw NP".lower(),
                "crswnp",
                "eosinophilic chronic rhinosinusitis",
            ],
        ),
        (
            "Pulmonary Eosinophilic Disorders",
            [
                "pulmonary eosinophilia",
                "eosinophilic pneumonia",
                "allergic bronchopulmonary aspergillosis",
                "abpa",
                "lung eosinophilia",
            ],
        ),
        (
            "Eosinophilic Esophagitis",
            [
                "eosinophilic esophagitis",
                "eosinophilic oesophagitis",
                "eoe",
            ],
        ),
        (
            "Eosinophilic Gastrointestinal Disease",
            [
                "eosinophilic gastritis",
                "eosinophilic gastroenteritis",
                "eosinophilic colitis",
                "eosinophilic gastrointestinal",
                "egid",
            ],
        ),
        (
            "DRESS / Drug Hypersensitivity",
            [
                "dress",
                "drug reaction with eosinophilia",
                "drug hypersensitivity",
                "drug-induced eosinophilia",
                "drug induced eosinophilia",
            ],
        ),
        (
            "Dermatologic Eosinophilic Disorders",
            [
                "atopic dermatitis",
                "wells syndrome",
                "eosinophilic cellulitis",
                "eosinophilic dermatosis",
                "skin eosinophilia",
            ],
        ),
        (
            "Infectious / Parasitic Eosinophilia",
            [
                "parasite",
                "parasitic",
                "helminth",
                "strongyloides",
                "tropical eosinophilia",
                "schistosomiasis",
                "toxocara",
            ],
        ),
        (
            "Pediatric Eosinophilic Disorders",
            [
                "pediatric",
                "paediatric",
                "children",
                "childhood",
                "infant",
            ],
        ),
        (
            "Basic Science / Translational Eosinophil Biology",
            [
                "il-5",
                "interleukin-5",
                "eosinophil activation",
                "cytokine",
                "pathogenesis",
                "pathophysiology",
                "signaling",
                "molecular",
                "transcriptomic",
                "genomic",
            ],
        ),
    ]

    for category_name, keywords in categories:
        if any(keyword in text for keyword in keywords):
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

search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

search_params = {
    "db": "pubmed",
    "term": '("hypereosinophilia" OR "hypereosinophilic syndrome" OR "eosinophilia" OR "eosinophilic leukemia") AND ("last 30 days"[dp])',
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
        short_abstract = abstract[:700] + "..." if len(abstract) > 700 else abstract

        link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        journal_score = journal_scores.get(journal.lower(), 0)
        disease_category = assign_disease_category(title, abstract)

        articles.append(
            {
                "title": title,
                "journal": journal,
                "publication_date": publication_date,
                "pmid": pmid,
                "link": link,
                "abstract": short_abstract,
                "journal_score": journal_score,
                "disease_category": disease_category,
            }
        )


category_order = [
    "Hypereosinophilic Syndrome / Hypereosinophilia",
    "Eosinophilic Leukemia / Hematologic Neoplasms",
    "EGPA / Churg-Strauss / Vasculitis",
    "Asthma / Airway Disease",
    "Chronic Rhinosinusitis / Nasal Polyps",
    "Pulmonary Eosinophilic Disorders",
    "Eosinophilic Esophagitis",
    "Eosinophilic Gastrointestinal Disease",
    "DRESS / Drug Hypersensitivity",
    "Dermatologic Eosinophilic Disorders",
    "Infectious / Parasitic Eosinophilia",
    "Pediatric Eosinophilic Disorders",
    "Basic Science / Translational Eosinophil Biology",
    "Other Eosinophilic Disorders",
]

articles_html = ""

if articles:
    articles_html += """
    <p>
    Articles are grouped by disease area. Within each disease area,
    articles are sorted by journal score, highest first.
    </p>
    """

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
            articles_html += f"<h2>{category}</h2>"

            for item in category_articles:
                articles_html += make_article_html(item)

else:
    articles_html = "<p>No articles found in the prior 30 days.</p>"


html = f"""
<html>
<head>
    <title>Hypereosinophilia Research Updates</title>
</head>
<body>
    <h1>Hypereosinophilia Research Updates</h1>
    <p>Updated: {date.today()}</p>
    <p>Total citations found in prior 30 days: {total_found}</p>

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