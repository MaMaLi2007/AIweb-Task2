import os
from flask import Flask, request, render_template
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, AndGroup

app = Flask(__name__)  # initialize app
INDEX = "indexdir"  # directory where the Whoosh index is stored

lastrev = "none" 



def search_whoosh(query):
    if not query or not os.path.exists(INDEX):  # no query or index directory does not exist -> no result possible
        return []
    
    # Open the existing Whoosh index from the index directory
    ix = open_dir(INDEX)
    results = []  # initialize an empty list to store search results
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "content"], schema=ix.schema, group=AndGroup)
        parsed = parser.parse(query)   # clean user input query
        hits = searcher.search(parsed, limit=20)   # search the index with the parsed query, limit to 20 results
        # append all results in results list
        for hit in hits:

            '''
            teaser = hit.highlights("content")
            
            # 2. Fallback: Falls das Suchwort nur im Titel stand, nimm die ersten 200 Zeichen
            if not teaser:
                teaser = hit.fields().get("content", "")[:200] + "..."
            '''

            results.append({
                "title": hit.fields().get("title", "").strip(),
                "url": hit.fields().get("url", ""),
                #"teaser": teaser,
            })
    return results

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/search")
def search():
    query = request.args.get('q', '')
    # Here you would typically call your search function and pass the query
    url_list = search_whoosh(query)
    return render_template('search.html', query=query, url_list=url_list)  # pass the query and url_list to the template

if __name__ == "__main__":
    app.run(debug=True)