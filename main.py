import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import csv
import json
import sys
import time  # Importujeme modul time pro měření doby

# Vytvoříme session a nastavíme reálný User-Agent
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
})

# Globální slovníky pro uložení dat
pages_data = {}  # klíč = URL stránky, hodnota = { "status_code": ..., "links": [...] }
links_data = {}  # klíč = URL odkazu, hodnota = { "is_absolute": ..., "opens_new_window": ..., "scheme": ..., "nofollow": ..., "external": ..., "status_code": ..., "pages": set() }

def is_valid_url(url):
    """Ověří, zda URL obsahuje schéma (http/https) a doménu."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def get_response(url):
    """Načte obsah stránky – pomocí GET požadavku, stahujeme pouze HTML dokument."""
    try:
        r = session.get(url, timeout=10)
        return r
    except Exception as e:
        print(f"Chyba při stahování {url}: {e}")
        return None

def get_head_response(url):
    """Pomocí HEAD požadavku zjistí status kód odkazu."""
    try:
        r = session.head(url, timeout=10, allow_redirects=True)
        return r
    except Exception as e:
        print(f"Chyba při HEAD požadavku na {url}: {e}")
        return None

def save_progress(visited_pages, pages_data, links_data, filename="progress.json"):
    """Uloží průběžný stav do JSON souboru."""
    # Protože nelze přímo serializovat množinu, převedeme ji na list
    links_data_serializable = {}
    for link, data in links_data.items():
        data_copy = data.copy()
        data_copy['pages'] = list(data_copy.get('pages', []))
        links_data_serializable[link] = data_copy
    progress = {
        "visited_pages": list(visited_pages),
        "pages_data": pages_data,
        "links_data": links_data_serializable,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    print(f"Průběžný stav uložen do {filename}")

def process_links(soup, current_url, base_domain):
    """
    Ze zpracované stránky získá všechny odkazy a ke každému uloží:
      - zda je odkaz zapsán jako absolutní či relativní,
      - zda se má otevírat v novém okně (target="_blank"),
      - použitý protokol (http/https),
      - zda obsahuje atribut nofollow,
      - zda jde o externí odkaz (na základě porovnání domén),
      - u externích odkazů se pokusí zjistit status kód pomocí HEAD požadavku.
    
    Dále odstraní fragment (kotvu) z URL, aby se např. 
    https://domena.cz/stranka#obsah zpracovalo jako https://domena.cz/stranka.
    """
    page_links = []
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        if not href:
            continue
        # Přeskočíme odkazy typu javascript: nebo mailto:
        if href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        
        # Pokud je odkaz relativní, doplníme absolutní URL
        absolute_url = urljoin(current_url, href)
        # Odstraníme fragment (kotvu)
        parsed = urlparse(absolute_url)
        absolute_url = urlunparse(parsed._replace(fragment=""))
        
        # Ověříme, zda URL používá podporované schéma (http/https)
        parsed_href = urlparse(absolute_url)
        if not parsed_href.scheme.startswith("http"):
            continue
        
        # Určíme, zda byl původní odkaz zapsán jako absolutní
        is_absolute = bool(urlparse(href).netloc)
        
        # Ověříme, zda se má odkaz otevírat v novém okně
        target = a_tag.get("target")
        opens_new_window = (target == "_blank")
        
        # Zjistíme, zda obsahuje atribut nofollow (v rel)
        rel = a_tag.get("rel")
        nofollow = False
        if rel:
            if isinstance(rel, list):
                nofollow = "nofollow" in [r.lower() for r in rel]
            else:
                nofollow = "nofollow" in rel.lower()
        
        # Získáme protokol (http/https)
        scheme = parsed_href.scheme
        
        # Rozhodneme, zda je odkaz interní či externí
        external = (parsed_href.netloc and (parsed_href.netloc != base_domain))
        
        # U externích odkazů se pokusíme zjistit status kód pomocí HEAD požadavku
        status_code = None
        if external:
            head_resp = get_head_response(absolute_url)
            if head_resp:
                status_code = head_resp.status_code
        
        # Sestavíme slovník s informacemi o odkazu
        link_detail = {
            "url": absolute_url,
            "is_absolute": is_absolute,
            "opens_new_window": opens_new_window,
            "scheme": scheme,
            "nofollow": nofollow,
            "external": external,
            "status_code": status_code,
        }
        page_links.append(link_detail)
        
        # Aktualizace globálního slovníku pro odkazy (links_data)
        if absolute_url not in links_data:
            links_data[absolute_url] = {
                "is_absolute": is_absolute,
                "opens_new_window": opens_new_window,
                "scheme": scheme,
                "nofollow": nofollow,
                "external": external,
                "status_code": status_code,
                "pages": set([current_url]),
            }
        else:
            links_data[absolute_url]["pages"].add(current_url)
            
    return page_links

def crawl(start_url, progress_interval=10):
    """
    Prochází webovou stránku (a její interní odkazy) rekurzivně.
      - Používá frontu (pages_to_visit) a množinu visited_pages.
      - Po každých 'progress_interval' stránkách uloží aktuální stav do JSON.
    """
    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc  # interní odkazy budou mít stejnou doménu
    visited_pages = set()
    pages_to_visit = [start_url]
    page_count = 0

    while pages_to_visit:
        current_page = pages_to_visit.pop(0)
        if current_page in visited_pages:
            continue
        print(f"Zpracovávám stránku: {current_page}")
        start_time = time.time()  # start měření doby
        response = get_response(current_page)
        if response is None:
            pages_data[current_page] = {
                "status_code": None,
                "links": []
            }
            visited_pages.add(current_page)
            continue
        status = response.status_code
        if status != 200:
            print(f"Stránka {current_page} vrátila status {status}")
            pages_data[current_page] = {
                "status_code": status,
                "links": []
            }
            visited_pages.add(current_page)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        links = process_links(soup, current_page, base_domain)
        pages_data[current_page] = {
            "status_code": status,
            "links": links
        }
        visited_pages.add(current_page)
        page_count += 1

        # Spočítáme počet interních a externích odkazů
        internal_links = sum(1 for link in links if not link["external"])
        external_links = sum(1 for link in links if link["external"])
        processing_time = time.time() - start_time  # celková doba zpracování

        print(f"OK, trvalo to {processing_time:.2f} vteřiny, nalezeno {internal_links} interních a {external_links} externích odkazů")

        # Přidáme interní odkazy do fronty
        for link in links:
            if not link["external"]:
                link_parsed = urlparse(link["url"])
                if link_parsed.netloc == base_domain and link["url"] not in visited_pages and link["url"] not in pages_to_visit:
                    pages_to_visit.append(link["url"])

        if page_count % progress_interval == 0:
            save_progress(visited_pages, pages_data, links_data)
    return visited_pages

def write_csv_reports(base_domain):
    """Vytvoří dva CSV reporty: jeden pro stránky a druhý pro odkazy."""
    with open(f"{base_domain}_stranky.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["page_url", "status_code", "links"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for page, data in pages_data.items():
            links_json = json.dumps(data["links"], ensure_ascii=False)
            writer.writerow({
                "page_url": page,
                "status_code": data["status_code"],
                "links": links_json
            })
    print(f"CSV report pro stránky uložen do {base_domain}_stranky.csv")
    
    with open(f"{base_domain}_odkazy.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["link_url", "is_absolute", "opens_new_window", "scheme", "nofollow", "external", "status_code", "page_count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for link_url, data in links_data.items():
            writer.writerow({
                "link_url": link_url,
                "is_absolute": data["is_absolute"],
                "opens_new_window": data["opens_new_window"],
                "scheme": data["scheme"],
                "nofollow": data["nofollow"],
                "external": data["external"],
                "status_code": data["status_code"],
                "page_count": len(data["pages"]) if "pages" in data else 0
            })
    print(f"CSV report pro odkazy uložen do {base_domain}_odkazy.csv")

def main():
    user_url = input("Zadejte URL: ").strip()
    if not is_valid_url(user_url):
        print("Zadaná URL není validní. Ujistěte se, že začíná http:// nebo https:// a obsahuje doménu.")
        sys.exit(1)
    
    print(f"Kontroluji URL: {user_url}")
    initial_response = get_response(user_url)
    if initial_response is None or initial_response.status_code != 200:
        print(f"Chyba: URL nevrací status 200. Prosím, zadejte přesnou URL. Status: {initial_response.status_code if initial_response else 'None'}")
        sys.exit(1)
    
    print("Spouštím procházení webu...")
    visited_pages = crawl(user_url, progress_interval=10)
    print(f"Procházení dokončeno. Navštíveno {len(visited_pages)} stránek.")
    
    # Aktualizace interních odkazů – pokud jde o interní URL, status kód získáme z pages_data
    for link_url, link_info in links_data.items():
        if not link_info["external"]:
            if link_url in pages_data:
                link_info["status_code"] = pages_data[link_url]["status_code"]
            else:
                head_resp = get_head_response(link_url)
                if head_resp:
                    link_info["status_code"] = head_resp.status_code

    parsed_start = urlparse(user_url)
    base_domain = parsed_start.netloc
    save_progress(visited_pages, pages_data, links_data, filename="progress_final.json")
    write_csv_reports(base_domain)

if __name__ == "__main__":
    main()
