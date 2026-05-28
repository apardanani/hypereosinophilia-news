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


def classify_article(title, abstract):
    text = f"{title} {abstract}".lower()

    clinical_keywords = [
        "treatment", "therapy", "therapeutic", "management", "guideline",
        "recommendation", "case report", "case series", "clinical trial",
        "phase 1", "phase 2", "phase 3", "prognosis", "prognostic",
        "risk stratification", "risk factor", "diagnosis", "diagnostic",
        "outcome", "survival", "response", "relapse", "refractory",
        "mepolizumab", "benralizumab", "imatinib", "corticosteroid",
        "steroid", "anti-il-5", "anti-interleukin-5"
    ]

    mechanism_keywords = [
        "mechanism", "pathophysiology", "pathogenesis", "molecular",
        "mutation", "mutations", "cytokine", "interleukin", "il-5",
        "signaling", "pathway", "gene expression", "transcriptomic",
        "genomic", "immune", "inflammation", "eosinophil activation"
    ]

    pathology_keywords = [
        "pathology", "histology", "biopsy", "bone marrow", "marrow",
        "immunophenotype", "flow cytometry", "cytogenetic", "cytogenetics",
        "fish", "pcr", "morphology", "infiltration", "tissue eosinophilia"
    ]

    if any(keyword in text for keyword in clinical_keywords):
        return "Clinical Practice"

    if any(keyword in text for keyword in mechanism_keywords):
        return "Mechanism / Pathophysiology"

    if any(keyword in text for keyword in pathology_keywords):
        return "Pathology / Diagnostic Findings"

    return "Other / Unclassified"


def make_article_html(item):
    return f"""
    <article>
        <h3><a href="{item["link"]}" target="_blank">{item["title"]}</a></h3>
        <p><strong>Journal:</strong> {item["journal"]}</p>
        <p><strong>Journal Score:</strong> {item["journal_score"]}</p>
        <p><strong>Category:</strong> {item["category"]}</p>
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
    "retmax": 100
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
        "retmode": "xml"
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
        category = classify_article(title, abstract)

        articles.append({
            "title": title,
            "journal": journal,
            "publication_date": publication_date,
            "pmid": pmid,
            "link": link,
            "abstract": short_abstract,
            "journal_score": journal_score,
            "category": category
        })


ranked_articles = [a for a in articles if a["journal_score"] > 0]
unranked_articles = [a for a in articles if a["journal_score"] == 0]

ranked_articles.sort(key=lambda x: x["journal_score"], reverse=True)

clinical_articles = [a for a in unranked_articles if a["category"] == "Clinical Practice"]
mechanism_articles = [a for a in unranked_articles if a["category"] == "Mechanism / Pathophysiology"]
pathology_articles = [a for a in unranked_articles if a["category"] == "Pathology / Diagnostic Findings"]
other_articles = [a for a in unranked_articles if a["category"] == "Other / Unclassified"]

articles_html = ""

if articles:
    articles_html += "<h2>High-Ranked Journal Articles</h2>"

    if ranked_articles:
        for item in ranked_articles:
            articles_html += make_article_html(item)
    else:
        articles_html += "<p>No articles from ranked journals found.</p>"

    articles_html += "<h2>Unranked Articles: Clinical Practice</h2>"

    if clinical_articles:
        for item in clinical_articles:
            articles_html += make_article_html(item)
    else:
        articles_html += "<p>No clinical practice articles found among unranked journals.</p>"

    articles_html += "<h2>Unranked Articles: Mechanism / Pathophysiology</h2>"

    if mechanism_articles:
        for item in mechanism_articles:
            articles_html += make_article_html(item)
    else:
        articles_html += "<p>No mechanism/pathophysiology articles found among unranked journals.</p>"

    articles_html += "<h2>Unranked Articles: Pathology / Diagnostic Findings</h2>"

    if pathology_articles:
        for item in pathology_articles:
            articles_html += make_article_html(item)
    else:
        articles_html += "<p>No pathology/diagnostic articles found among unranked journals.</p>"

    articles_html += "<h2>Unranked Articles: Other / Unclassified</h2>"

    if other_articles:
        for item in other_articles:
            articles_html += make_article_html(item)
    else:
        articles_html += "<p>No other unclassified articles found.</p>"

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

    <p>
    Articles from journals in your ranking list are shown first.
    Articles from unranked journals are grouped by topic using title and abstract keywords.
    </p>

    {articles_html}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as file:
    file.write(html)

print("Website updated successfully: index.html")
print("Total citations found:", total_found)
print("Ranked articles:", len(ranked_articles))
print("Unranked clinical articles:", len(clinical_articles))
print("Unranked mechanism/pathophysiology articles:", len(mechanism_articles))
print("Unranked pathology/diagnostic articles:", len(pathology_articles))
print("Unranked other articles:", len(other_articles))