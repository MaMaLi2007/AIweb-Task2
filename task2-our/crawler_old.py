import os
import time
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser



#crawler with search function and memory index

#search function to search for words in the in_memory_index

def search(search_term, in_memory_index):
    # if there is no word to search for, return an empty list
    if not search_term:
        return []
    
    result_urls = None # initialize result_urls as None

    for word in search_term:
        clean_word = word.lower() # lowercase because index is in lowercase too
        if clean_word in in_memory_index: # look if the word is in the index
            current_urls = set(in_memory_index[clean_word]) # add the urls of the word to the result_urls set
        else:
            return [] # if the word is not in the index, return an empty list, because there are no urls for this word
        
        if result_urls is None: # if result_urls is None, it means this is the first word we are searching for, so we initialize it with the urls of the first word
            result_urls = current_urls
        else:
            result_urls = result_urls & current_urls # if result_urls is not None, it means we have already searched for a word, so we take the intersection of the urls of the current word and the urls of the previous words

    return list(result_urls) #return the result_urls as a list


if not os.path.exists("indexdir"):
    os.makedirs("indexdir")
    
# where to start crawling
#root = "http://info.cern.ch/hypertext/WWW"
root = "https://books.toscrape.com"

agenda = [root]   # what to crawl next
visited = set()   # does not crawl what already was crawled

# unique -> no urls multiple times; stored -> readable, ID -> identificator
schema = Schema(
    title=TEXT(stored=True), 
    content=TEXT, 
    url= ID(stored=True, unique=True),
)

# create an index in the directory indexdr (the directory must already exist!)
ix = create_in("indexdir", schema)
writer = ix.writer()

max_pages = 10
pages_crawled = 0
in_memory_index = {}

while agenda and pages_crawled < max_pages:
    url = agenda.pop()

    # checks if we have already crawled this URL
    if url in visited:
        continue
    visited.add(url)

    # get the page
    r = requests.get(
        url,
        headers={"User-Agent": "AIWebPageCheck/1.0"},
        timeout=15,
    )

    # check the status code and skip if not 200 OK or if it's not an HTML page
    print("Get", r.status_code, r.url)
    if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", "").lower():
        continue

    pages_crawled += 1   # 

    # parse the page and find all links
    soup = BeautifulSoup(r.content, "html.parser")

    # get title and text
    title = soup.title.get_text() if soup.title else ""
    content = soup.get_text()
    writer.add_document(
        title=title,
        content=content,
        url=r.url,
    )

    # saves every word from a website in a set
    unique_words = set()   # creates for each new website a empty set to save words
    # content.lower: whole text gets converged to lowercase 
    # split: splits text in single raw words at spaces
    for raw_word in content.lower().split():
        # strips raw word of all symbols possibilty attachted to it
        word = raw_word.strip(",.!?;:\"'()[]{}<>-_/\\")
        # adds word to set, if only symbols -> ignored
        if word:
            unique_words.add(word)

    # adds word into in_memroy_index
    for word in unique_words:
        # checks if the word is already in the index if not adds it
        if word not in in_memory_index:
            in_memory_index[word] = []
        # appends URL to word in memory index regardless of just added or already in index
        in_memory_index[word].append(r.url)    

    for link in soup.select("a[href]"):
        # get the absolute URL of the link, and remove any fragment (the part after #)
        target, _ = urldefrag(urljoin(r.url, link["href"]))
        if (target == root or target.startswith(root + "/")) and target not in visited:
            #print("Found ", target)
            agenda.append(target)



try:
    writer.commit() 
except PermissionError:   # works around Error from windowsystem
    time.sleep(0.5)
    try:
        # deletes MAIN.tmp and tells python no to crash if folder doesn't exist
        shutil.rmtree("indexdir/MAIN.tmp", ignore_errors=True)
    except Exception:
        pass

with ix.searcher() as searcher:
    # find entries with the word 'program'
    query = QueryParser("content", ix.schema).parse("program")
    results = searcher.search(query)

    # print all results
    for r in results:
        print(r)

#print(in_memory_index)
print("Suchergebnis:", search(["the"], in_memory_index))