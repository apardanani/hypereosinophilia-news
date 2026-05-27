import requests
from xml.etree import ElementTree
from datetime import date

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

articles_html = ""

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

        articles_html += f"""
        <article>
            <h2><a href="{link}" target="_blank">{title}</a></h2>
            <p><strong>Journal:</strong> {journal}</p>
            <p><strong>Publication Date:</strong> {publication_date}</p>
            <p><strong>PubMed Link:</strong> <a href="{link}" target="_blank">{link}</a></p>
            <p><strong>Abstract:</strong> {short_abstract}</p>
        </article>
        <hr>
        """
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