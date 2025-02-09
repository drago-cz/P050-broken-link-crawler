# Broken Link Crawler (Beta)

**Broken Link Crawler** je Python skript, který prochází webové stránky a detekuje rozbité odkazy. Tento počáteční (beta) release je stále ve vývoji, a proto některé funkce nemusí být zcela implementovány či optimalizovány. Například funkce pokračování po přerušení procházení nebo vylepšené reporty jsou plánovány pro budoucí verze.

Repozitář naleznete na GitHubu: [Broken Link Crawler](https://github.com/drago-cz/P050-broken-link-crawler)

## Funkce

- **Rekurzivní procházení:** Skript začíná zadanou URL a rekurzivně navštěvuje interní odkazy na stejné doméně.
- **Analýza odkazů:** Pro každý nalezený odkaz skript:
  - Určuje, zda je odkaz zapsán jako absolutní nebo relativní.
  - Kontroluje, zda se odkaz otevírá v novém okně (pomocí `target="_blank"`).
  - Zjišťuje použitý protokol (HTTP/HTTPS).
  - Detekuje přítomnost atributu `nofollow`.
  - Určuje, zda je odkaz interní nebo externí.
  - U externích odkazů získává HTTP status kód pomocí HEAD požadavku.
- **Odstranění fragmentů:** Fragmenty (kotvy) v URL jsou odstraněny, aby nedocházelo k duplicitnímu zpracování (např. `example.com/stranka#sekce` se zpracovává jako `example.com/stranka`).
- **Ukládání průběhu:** Průběžný stav procházení je periodicky ukládán do JSON souboru, což umožňuje sledovat aktuální stav práce. Lze použít i jako zdroj dat pro další vizualizace.
- **Generování reportů:** Po dokončení procházení jsou vytvořeny dva CSV reporty:
  - Report o stránkách (se status kódy a seznamem odkazů).
  - Report o odkazech (s detaily jednotlivých odkazů a počtem stránek, kde se daný odkaz vyskytuje).

## Použité technologie a knihovny

- **Python 3.x**
- [Requests](https://docs.python-requests.org/) – pro HTTP požadavky
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) – pro parsování HTML
- [Colorama](https://pypi.org/project/colorama/) – pro barevný výstup do konzole
- Standardní Python moduly: `urllib.parse`, `csv`, `json`, `sys`, `time`

## Instalace

1. **Naklonování repozitáře:**
   ```bash
   git clone https://github.com/drago-cz/P050-broken-link-crawler.git
   ```
2. **Přechod do adresáře projektu:**
   ```bash
   cd P050-broken-link-crawler
   ```
3. **Vytvoření virtuálního prostředí (doporučeno):**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Na Linux/MacOS
   venv\Scripts\activate       # Na Windows
   ```
4. **Instalace závislostí:**
   ```bash
   pip install -r requirements.txt
   ```

## Použití

Spusťte skript pomocí Pythonu:
```bash
python script.py
```

Po spuštění budete vyzváni k zadání URL adresy, kterou chcete zkontrolovat. Skript následně:
- Projde webovou stránku a její interní odkazy.
- Analyzuje a shromažďuje data o odkazech na každé stránce.
- Pravidelně ukládá průběžný stav do JSON souboru (např. `progress.json`).
- Po dokončení vytvoří finální CSV reporty:
  - `<doména>_stranky.csv` – report o stránkách.
  - `<doména>_odkazy.csv` – report o odkazech.

## Plánovaná vylepšení aka To Dd List

- **Funkce pokračování:** Možnost pokračovat v procházení po přerušení.
- **Vylepšené reporty:** Přehlednější a detailnější CSV/JSON výstupy.
- **Optimalizace:** Lepší zpracování chyb a další vylepšení výkonu.

## Poděkování
Jedná se o víkendoví projekt, který bych takto rychle nedal bez AI pomocí **ChatGPT o3-mini-high**  (pomoc s prvotním kódem a vygenerováním dokumentace) a 
**ChatGPT 4o** za pomoc s laděním, argumentace (ne)vhodného návrhu kódu a komentáři.


## Licence

Tento projekt je uvolněn pod vlastním licenčním ujednáním, které umožňuje stažení a používání kódu ve své původní podobě. **Úprava, adaptace nebo redistribuce kódu bez výslovného povolení není dovolena.** Důvodem je, že projekt není kompletní a neprošel důsledným testování. Budoucí licence bude MIT. 

## Disclaimer

Software je poskytován "tak, jak je" bez jakékoli záruky. Používáte jej na vlastní riziko. Jelikož se jedná o beta verzi (hodně early :)), můžete narazit na chyby nebo neočekávané chování. 


