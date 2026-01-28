import json
import csv
import re
from playwright.sync_api import sync_playwright

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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://tamburino.cinetel.it/pages/boxoffice.php?edperiodo=c3RhZ2lvbmFsZQ=", wait_until="domcontentloaded")

    # Aspetta che compaiano le righe della tabella
    page.wait_for_selector("table.tablesorter tbody tr")

    rows = page.locator("table.tablesorter tbody tr")
    data = []

    for i in range(rows.count()):
        tds = rows.nth(i).locator("td")

        # Questa tabella ha TD "nascosti" (display:none) con numeri grezzi.
        # Struttura tipica della riga:
        # 0 pos, 1 titolo, 2 data, 3 nazione, 4 distribuzione,
        # 5 incasso_raw (hidden), 6 presenze_raw (hidden), 7 incasso_al_raw (hidden), 8 presenze_al_raw (hidden),
        # 9 incasso_visibile, 10 presenze_visibile, 11 incasso_al_visibile, 12 presenze_al_visibile

        pos = tds.nth(0).inner_text().strip()
        titolo = tds.nth(1).inner_text().strip()

        # data "visibile" (es. 25/12/2025)
        prima_progr = tds.nth(2).inner_text().strip()

        # data ISO (è dentro uno span display:none tipo "'2025-12-25'")
        iso_span = tds.nth(2).locator("span").first
        prima_progr_iso = iso_span.inner_text().strip().strip("'") if iso_span.count() else None

        nazione = tds.nth(3).inner_text().strip()
        distribuzione = tds.nth(4).inner_text().strip()

        incasso_raw = tds.nth(5).inner_text().strip()        # già numerico tipo 73665455.48
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

# Salva JSON
with open("boxoffice.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Salva CSV
fieldnames = list(data[0].keys()) if data else []
with open("boxoffice.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(data)

print(f"Salvati {len(data)} record in boxoffice.json e boxoffice.csv")
print("Esempio:", data if data else None)
