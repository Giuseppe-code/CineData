import json
import csv
import re
import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright


SINK_URL = os.environ.get("SINK_URL", "http://fluentbit:9880/topBoxOffice")
DELAY = float(os.environ.get("DELAY", "0.2"))
LOOP = os.environ.get("LOOP", "true").lower() in ("1", "true", "yes")
TIMEOUT = float(os.environ.get("TIMEOUT", "5"))

# Usa /app/cache se esiste (Docker), altrimenti cartella corrente
CACHE_DIR = "/app/cache" if os.path.exists("/app/cache") else "."
CACHE_FILE = os.path.join(CACHE_DIR, "boxoffice_cache.json")


def clean_number(s: str) -> float:
    """
    Converte stringhe tipo "€ 73.665.455" o "9.178.654" o "25477068.30" in numero.
    """
    if s is None:
        return None
    s = s.strip()
    # rimuovi euro, spazi, punti migliaia, NBSP ecc.
    s = s.replace("€", "").replace("\xa0", " ").strip()
    s = s.replace(".", "")  # separatore migliaia
    s = s.replace(",", ".") # se mai capitasse virgola decimale
    # lascia solo cifre e punto
    s = re.sub(r"[^0-9.]", "", s)
    if s == "":
        return None
    return float(s)


def scrape_boxoffice_data(use_cache: bool = True):
    """
    Scarica i dati dal box office e ritorna lista di dizionari.
    Se use_cache=True e il file cache esiste, usa quello invece di fare scraping.
    """
    # Controlla se esiste la cache
    if use_cache and os.path.exists(CACHE_FILE):
        print(f"📦 Carico dati dalla cache: {CACHE_FILE}")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    print("🔍 Scraping box office in corso...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://tamburino.cinetel.it/pages/boxoffice.php?edperiodo=c2NvcnNhc2V0dGltYW5hbGU=", 
                  wait_until="domcontentloaded")

        # Aspetta che compaiano le righe della tabella
        page.wait_for_selector("table.tablesorter tbody tr")

        rows = page.locator("table.tablesorter tbody tr")
        data = []

        for i in range(rows.count()):
            tds = rows.nth(i).locator("td")

            pos = tds.nth(0).inner_text().strip()
            titolo = tds.nth(1).inner_text().strip()

            # data "visibile" (es. 25/12/2025)
            prima_progr = tds.nth(2).inner_text().strip()

            # data ISO (è dentro uno span display:none tipo "'2025-12-25'")
            iso_span = tds.nth(2).locator("span").first
            prima_progr_iso = iso_span.inner_text().strip().strip("'") if iso_span.count() else None

            nazione = tds.nth(3).inner_text().strip()
            distribuzione = tds.nth(4).inner_text().strip()

            incasso_raw = tds.nth(5).inner_text().strip()
            presenze_raw = tds.nth(6).inner_text().strip()
            incasso_al_raw = tds.nth(7).inner_text().strip()
            presenze_al_raw = tds.nth(8).inner_text().strip()

            record = {
                "pos": int(pos) if pos.isdigit() else pos,
                "titolo": titolo,
                "prima_progr": prima_progr,
                "prima_progr_iso": prima_progr_iso,
                "nazione": nazione,
                "distribuzione": distribuzione,
                "incasso": float(incasso_raw) if incasso_raw else None,
                "presenze": int(float(presenze_raw)) if presenze_raw else None,
                "incasso_al": float(incasso_al_raw) if incasso_al_raw else None,
                "presenze_al": int(float(presenze_al_raw)) if presenze_al_raw else None,
            }
            data.append(record)

        browser.close()
        
        # Salva nella cache
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Dati salvati in cache: {CACHE_FILE}")
        
        return data


def send_event(ev: dict):
    """
    Invia un evento a Fluent.
    """
    payload = dict(ev)
    payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload["source"] = "boxoffice_scraper"
    r = requests.post(SINK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()


def get_boxoffice_data_with_titles(max_films: int = 10, use_cache: bool = True):
    """
    Ritorna lista completa dei dati box office (primi max_films).
    Usato dal main_scraper per avere tutti i dati da inviare a Fluent.
    """
    data = scrape_boxoffice_data(use_cache=use_cache)
    return data[:max_films]


def main():
    """
    Scarica i dati e li invia a Fluent in loop.
    """
    data = scrape_boxoffice_data(use_cache=False)  # Forza scraping
    
    print(f"✅ Raccolti {len(data)} record dal box office")
    
    while True:
        for ev in data:
            send_event(ev)
            print(f"📤 Inviato: {ev['titolo']}")
            time.sleep(DELAY)
        if not LOOP:
            break


if __name__ == "__main__":
    main()