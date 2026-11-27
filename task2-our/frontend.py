import os
from flask import Flask, request, render_template
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, AndGroup

from flask import Flask, request, render_template

app = Flask(__name__)
INDEX = "indexdir" 

lastrev="none"

def search_whoosh(query):
    if not query or not os.path.exists(INDEX):
        return []

    ix = open_dir(INDEX)
    results = []

    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "content"], schema=ix.schema, group=AndGroup)
        parsed = parser.parse(query)
        hits = searcher.search(parsed, limit=20)

        for hit in hits:
            results.append({
                "title": hit.get("title", "").strip() or hit.get("url", ""),
                "url": hit.get("url", ""),
            })

    return results
    

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/search")
def search():
    query = request.args['q']
    # Here you would typically call your search function and pass the query
    return render_template('search.html', query=query)

if __name__ == "__main__":
    app.run(debug=True)
    