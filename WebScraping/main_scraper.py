import asyncio
import os
import time
import json
import requests
from datetime import datetime
from ScrapingBoxOffice import get_boxoffice_data_with_titles, send_event as send_boxoffice_event
from ScrapingIMDbID import get_imdb_id_from_title
from ScrapingReview import scrape_imdb_reviews_from_url


BOXOFFICE_SINK_URL = os.environ.get("BOXOFFICE_SINK_URL", "http://fluentbit:9880/topBoxOffice")
REVIEWS_SINK_URL = os.environ.get("REVIEWS_SINK_URL", "http://fluentbit:9880/reviewFilm")
DELAY = float(os.environ.get("DELAY", "0.2"))
LOOP = os.environ.get("LOOP", "true").lower() in ("1", "true", "yes")
TIMEOUT = float(os.environ.get("TIMEOUT", "5"))

# Usa /app/cache se esiste (Docker), altrimenti cartella corrente
CACHE_DIR = "/app/cache" if os.path.exists("/app/cache") else "."
REVIEWS_CACHE_FILE = os.path.join(CACHE_DIR, "reviews_cache.json")
IMDB_IDS_CACHE_FILE = os.path.join(CACHE_DIR, "imdb_ids_cache.json")


def send_review_event(ev: dict):
    """
    Invia un evento recensione a Fluent.
    """
    payload = dict(ev)
    payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload["source"] = "reviews_scraper"
    r = requests.post(REVIEWS_SINK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()


def load_imdb_ids_cache():
    """Carica la cache degli ID IMDb se esiste."""
    if os.path.exists(IMDB_IDS_CACHE_FILE):
        with open(IMDB_IDS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_imdb_ids_cache(cache):
    """Salva la cache degli ID IMDb."""
    with open(IMDB_IDS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def load_reviews_cache():
    """Carica la cache delle recensioni se esiste."""
    if os.path.exists(REVIEWS_CACHE_FILE):
        with open(REVIEWS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_reviews_cache(reviews):
    """Salva la cache delle recensioni."""
    with open(REVIEWS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)


async def scrape_reviews_for_films(boxoffice_data: list, max_reviews: int = 50, 
                                   headless: bool = True, use_cache: bool = True):
    """
    Per ogni film del box office:
    1. Cerca su IMDb e ottieni l'ID (con cache)
    2. Scarica le recensioni (con cache)
    3. Aggiunge imdb_id come chiave di collegamento
    
    Args:
        boxoffice_data: Lista di dati dal box office
        max_reviews: Numero massimo di recensioni per film
        headless: Se True, browser invisibile
        use_cache: Se True, usa la cache delle recensioni
    """
    all_reviews = []
    
    # Carica cache
    if use_cache:
        cached_reviews = load_reviews_cache()
        if cached_reviews:
            print(f"📦 Trovate {len(cached_reviews)} recensioni in cache")
            return cached_reviews
    
    imdb_ids_cache = load_imdb_ids_cache()
    
    for film_data in boxoffice_data:
        title = film_data["titolo"]
        print(f"\n{'='*60}")
        print(f"🎬 Elaboro: {title}")
        print(f"{'='*60}")
        
        # Step 1: Ottieni l'ID IMDb (con cache)
        if title in imdb_ids_cache:
            imdb_id = imdb_ids_cache[title]
            print(f"📦 ID dalla cache: {imdb_id}")
        else:
            # Retry fino a 3 volte in caso di errore
            imdb_id = None
            for attempt in range(3):
                try:
                    imdb_id = await get_imdb_id_from_title(title, headless=headless)
                    if imdb_id:
                        imdb_ids_cache[title] = imdb_id
                        save_imdb_ids_cache(imdb_ids_cache)
                        break
                    else:
                        print(f"⚠️  Tentativo {attempt + 1}/3 fallito per '{title}'")
                        if attempt < 2:  # Non aspettare dopo l'ultimo tentativo
                            await asyncio.sleep(3)
                except Exception as e:
                    print(f"❌ Errore tentativo {attempt + 1}/3 per '{title}': {e}")
                    if attempt < 2:
                        await asyncio.sleep(5)
        
        if not imdb_id:
            print(f"⚠️  Salto '{title}' - ID non trovato dopo 3 tentativi")
            continue
        
        # Step 2: Costruisci l'URL e scarica le recensioni
        imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
        print(f"📥 Scarico recensioni per {imdb_url}")
        
        try:
            reviews = await scrape_imdb_reviews_from_url(
                imdb_url, 
                max_reviews=max_reviews, 
                headless=headless
            )
            
            print(f"✓ Trovate {len(reviews)} recensioni per '{title}'")
            
            # Aggiungi metadati a ogni recensione
            for review in reviews:
                review["film_title"] = title
                review["imdb_id"] = imdb_id  # ← CHIAVE DI COLLEGAMENTO
                all_reviews.append(review)
                
        except Exception as e:
            print(f"❌ Errore nello scraping di '{title}': {e}")
        
        # Pausa tra un film e l'altro
        await asyncio.sleep(2)
    
    # Salva cache delle recensioni
    save_reviews_cache(all_reviews)
    
    return all_reviews


def main():
    """
    Workflow completo:
    1. Ottieni i dati dal box office (con cache)
    2. Invia dati box office a Fluent
    3. Per ogni film, cerca su IMDb e scarica recensioni (con cache)
    4. Aggiunge imdb_id ai dati box office
    5. Invia recensioni a Fluent in loop
    """
    # Step 1: Ottieni i dati completi dal box office (usa cache)
    print("📊 Recupero dati dal box office...")
    boxoffice_data = get_boxoffice_data_with_titles(max_films=10, use_cache=True)
    print(f"✓ Trovati {len(boxoffice_data)} film")
    
    # Step 2: Scarica recensioni e ottieni imdb_id per ogni film
    print("\n🔍 Inizio scraping recensioni...")
    all_reviews = asyncio.run(
        scrape_reviews_for_films(boxoffice_data, max_reviews=30, headless=True, use_cache=True)
    )
    
    print(f"\n✅ Totale recensioni raccolte: {len(all_reviews)}")
    
    # Step 3: Crea mapping titolo -> imdb_id
    title_to_imdb = {r["film_title"]: r["imdb_id"] for r in all_reviews}
    
    # Step 4: Aggiungi imdb_id (o titolo come fallback) ai dati box office e invia a Fluent
    print(f"\n📤 Invio dati box office a {BOXOFFICE_SINK_URL}...")
    for film_data in boxoffice_data:
        # Aggiungi imdb_id come chiave di collegamento
        imdb_id = title_to_imdb.get(film_data["titolo"], None)
        
        # Se imdb_id è None, usa il titolo come chiave primaria
        film_data["primary_key"] = imdb_id if imdb_id else film_data["titolo"]
        film_data["imdb_id"] = imdb_id
        
        # Invia a Fluent
        payload = dict(film_data)
        payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        payload["source"] = "boxoffice_scraper"
        try:
            r = requests.post(BOXOFFICE_SINK_URL, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            key_info = f"primary_key: {film_data['primary_key']}"
            print(f"📤 Box office inviato: {film_data['titolo']} ({key_info})")
        except Exception as e:
            print(f"❌ Errore invio box office per {film_data['titolo']}: {e}")
        time.sleep(DELAY)
    
    # Step 5: Invia recensioni a Fluent in loop
    print(f"\n📤 Invio recensioni a {REVIEWS_SINK_URL}...")
    while True:
        for review in all_reviews:
            # Aggiungi primary_key (imdb_id o titolo come fallback)
            review["primary_key"] = review["imdb_id"] if review["imdb_id"] else review["film_title"]
            send_review_event(review)
            print(f"📤 Recensione: {review['film_title']} - {review['review_title'][:50]}...")
            time.sleep(DELAY)
        if not LOOP:
            break
    
    print("\n🎉 Completato!")


if __name__ == "__main__":
    main()