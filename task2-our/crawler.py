import requests
from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser

# where to start crawling
root = "https://info.cern.ch/hypertext/WWW"

agenda = [root] # what to crawl next

# unique -> no urls multiple times; stored -> readable, ID -> identificator
schema = Schema(title=TEXT(stored=True), content=TEXT, url= ID(stored=True, unique=True))

# Create an index in the directory indexdr (the directory must already exist!)
ix = create_in("indexdir", schema)
writer = ix.writer()

while agenda:
    url = agenda.pop()

    # Get the page
    r = requests.get(
        url,
        headers={"User-Agent": "AIWebPageCheck/1.0"},
        timeout=15,
    )

    # Check the status code and skip if not 200 OK
    print("Get", r.status_code, r.url)
    if r.status_code != 200:
        continue

    # Parse the page and find all links
    soup = BeautifulSoup(r.content, "html.parser")

    # get title and text
    title = soup.title.get_text() if soup.title else ""
    content = soup.get_text()
    writer.add_document(
        title = title,
        content = content,
        url = r.url
    )

    for link in soup.select("a[href]"):

        # Get the absolute URL of the link, and remove any fragment (the part after #)
        target, _ = urldefrag(urljoin(r.url, link["href"]))
        if (target == root or target.startswith(root + "/")) and target not in visited:
            #print("Found ", target)
            agenda.append(target)
    
    # write the index to the disk
    writer.commit()



with ix.searcher() as searcher:
    # find entries with the words 'first' AND 'last'
    query = QueryParser("content", ix.schema).parse("first last")
    results = searcher.search(query)

    # print all results
    for r in results:
        print(r)


