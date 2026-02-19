import asyncio
import os
import time
import json
import requests
import uuid
import argparse
from datetime import datetime
from ScrapingBoxOffice import get_boxoffice_data_with_titles
from ScrapingIMDbID import get_imdb_id_from_title
from ScrapingReview import scrape_imdb_reviews_from_url


BOXOFFICE_SINK_URL = os.environ.get("BOXOFFICE_SINK_URL", "http://fluentbit:9880/topboxoffice")
REVIEWS_SINK_URL = os.environ.get("REVIEWS_SINK_URL", "http://fluentbit:9880/reviewFilm")
DELAY = float(os.environ.get("DELAY", "0.2"))
LOOP = os.environ.get("LOOP", "true").lower() in ("1", "true", "yes")
TIMEOUT = float(os.environ.get("TIMEOUT", "5"))

CACHE_DIR = "/app/cache" if os.path.exists("/app/cache") else "."
REVIEWS_CACHE_FILE = os.path.join(CACHE_DIR, "reviews_cache.json")
IMDB_IDS_CACHE_FILE = os.path.join(CACHE_DIR, "imdb_ids_cache.json")


def send_review_event(ev: dict):
    """Invia un evento recensione a Fluent/Kafka."""
    payload = dict(ev)
    payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload["source"] = "reviews_scraper"
    r = requests.post(REVIEWS_SINK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()


def load_imdb_ids_cache():
    if os.path.exists(IMDB_IDS_CACHE_FILE):
        with open(IMDB_IDS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_imdb_ids_cache(cache):
    with open(IMDB_IDS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def load_reviews_cache():
    if os.path.exists(REVIEWS_CACHE_FILE):
        with open(REVIEWS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def generate_review_id(film_title: str, review_author: str, review_date: str) -> str:
    """Genera ID univoco per la recensione."""
    return str(uuid.uuid4())


async def demo_live_scraping(imdb_id: str, film_title: str, max_reviews: int = 10, headless: bool = False):
    """
    Modalità DEMO LIVE per presentazioni:
    1. Prende un ID IMDb e un titolo
    2. Scarica recensioni in tempo reale
    3. Le invia una per una a Kafka
    """
    print("\n" + "="*70)
    print("🎬 MODALITÀ DEMO LIVE - SCRAPING IN TEMPO REALE")
    print("="*70)
    
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
    print(f"\n🎬 Film: {film_title} ({imdb_id})")
    print(f"📥 Scarico recensioni da: {imdb_url}")
    print(f"🎯 Target: {max_reviews} recensioni")
    print(f"👁️  Browser visibile: {'Sì' if not headless else 'No'}")
    
    print(f"\n⏳ Avvio scraping...")
    try:
        reviews = await scrape_imdb_reviews_from_url(
            imdb_url, 
            max_reviews=max_reviews, 
            headless=headless
        )
    except Exception as e:
        print(f"❌ Errore durante scraping: {e}")
        return
    
    if not reviews:
        print("⚠️  Nessuna recensione trovata!")
        return
    
    print(f"\n✅ Trovate {len(reviews)} recensioni!")
    print(f"\n📤 Invio a Kafka topic 'reviewFilm'...")
    print("-" * 70)
    
    for i, review in enumerate(reviews, 1):
        review_id = generate_review_id(
            film_title=film_title,
            review_author=review.get("review_author", "unknown"),
            review_date=review.get("review_date", "unknown")
        )
        review["review_id"] = review_id
        review["imdb_id"] = imdb_id
        review["film_title"] = film_title  

        try:
            send_review_event(review)
            
            print(f"\n[{i}/{len(reviews)}] ✓ Inviata recensione:")
            print(f"  🎬 Film: {film_title}")
            print(f"  📝 Titolo: {review.get('review_title', 'N/A')[:60]}...")
            print(f"  👤 Autore: {review.get('review_author', 'N/A')}")
            print(f"  ⭐ Rating: {review.get('review_rating', 'N/A')}/10")
            print(f"  🆔 Review ID: {review_id[:16]}...")
            print(f"  📊 Lunghezza testo: {len(review.get('review_text', ''))} caratteri")
            
        except Exception as e:
            print(f"  ❌ Errore invio: {e}")
        
        time.sleep(1)
    
    print("\n" + "="*70)
    print(f"🎉 DEMO COMPLETATA!")
    print(f"✓ {len(reviews)} recensioni inviate a Kafka")
    print(f"✓ Film: {film_title} ({imdb_id})")
    print("="*70)


async def scrape_reviews_for_films(boxoffice_data: list, max_reviews: int = 50, 
                                   headless: bool = True, use_cache: bool = True):
    """Funzione originale per box office (invariata)."""
    all_reviews = []
    
    imdb_ids_cache = load_imdb_ids_cache()
    
    for film_data in boxoffice_data:
        title = film_data["titolo"]
        print(f"\n{'='*60}")
        print(f"🎬 Elaboro: {title}")
        print(f"{'='*60}")
        
        if title in imdb_ids_cache:
            print(f"📦 Film già processato (ID in cache: {imdb_ids_cache[title]}), salto le recensioni.")
            continue  

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
                    if attempt < 2:
                        await asyncio.sleep(3)
            except Exception as e:
                print(f"❌ Errore tentativo {attempt + 1}/3 per '{title}': {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
    
        if not imdb_id:
            print(f"⚠️  Salto scraping per '{title}' - nessun IMDb ID")
            continue
        
        imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
        print(f"📥 Scarico recensioni per {imdb_url}")
        
        try:
            reviews = await scrape_imdb_reviews_from_url(
                imdb_url, 
                max_reviews=max_reviews, 
                headless=headless
            )
            
            print(f"✓ Trovate {len(reviews)} recensioni per '{title}'")
            
            for review in reviews:
                review_id = generate_review_id(
                    film_title=title,
                    review_author=review.get("review_author", "unknown"),
                    review_date=review.get("review_date", "unknown")
                )
                review["review_id"] = review_id
                review["imdb_id"] = imdb_id
                review["film_title"] = title 
                all_reviews.append(review)
                
        except Exception as e:
            print(f"❌ Errore nello scraping di '{title}': {e}")
        
        await asyncio.sleep(2)
    
    return all_reviews


def main():
    """Main con supporto per modalità demo."""
    
    parser = argparse.ArgumentParser(description="Scraper recensioni IMDb")
    parser.add_argument(
        "--demo",
        type=str,
        metavar="IMDB_ID",
        help="Modalità DEMO: scraping live di un film specifico (es: --demo tt0111161)"
    )
    parser.add_argument(
        "--title",                          
        type=str,
        metavar="TITOLO",
        default=None,
        help="Titolo del film per modalità demo (es: --title 'The Matrix')"
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=10,
        help="Numero massimo di recensioni (default: 10 in demo, 30 in normale)"
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Mostra browser durante scraping (utile per demo)"
    )
    
    args = parser.parse_args()
    
    # MODALITÀ DEMO
    if args.demo:
        imdb_id = args.demo
        
        # Valida formato ID
        if not imdb_id.startswith("tt"):
            imdb_id = f"tt{imdb_id}"
        
        # Titolo: usa --title se specificato, altrimenti cerca nella cache
        if args.title:
            film_title = args.title
        else:
            # Cerca nella cache imdb_ids {titolo: imdb_id} → inverti
            imdb_cache = load_imdb_ids_cache()
            inverted = {v: k for k, v in imdb_cache.items()}
            film_title = inverted.get(imdb_id, imdb_id)  # fallback: usa imdb_id
            
            if film_title == imdb_id:
                print(f"⚠️  Titolo non trovato per {imdb_id}.")
                print(f"   Suggerimento: usa --title 'Nome Film' per specificarlo")
        
        print(f"\n🎬 Avvio modalità DEMO per {film_title} ({imdb_id})")
        
        asyncio.run(demo_live_scraping(
            imdb_id=imdb_id,
            film_title=film_title,
            max_reviews=args.max_reviews,
            headless=not args.show_browser
        ))
        
        return
    
    # MODALITÀ NORMALE (originale)
    print("📊 Recupero dati dal box office...")
    boxoffice_data = get_boxoffice_data_with_titles(max_films=10, use_cache=True)
    print(f"✓ Trovati {len(boxoffice_data)} film")
    
    print("\n🔍 Inizio scraping recensioni...")
    all_reviews = asyncio.run(
        scrape_reviews_for_films(
            boxoffice_data, 
            max_reviews=args.max_reviews if args.max_reviews != 10 else 30,
            headless=not args.show_browser,
            use_cache=True
        )
    )
    
    print(f"\n✅ Totale recensioni raccolte: {len(all_reviews)}")
    
    title_to_imdb = {r.get("imdb_id"): r.get("imdb_id") for r in all_reviews if r.get("imdb_id")}
    
    print(f"\n📤 Invio dati box office a {BOXOFFICE_SINK_URL}...")
    for film_data in boxoffice_data:
        imdb_id = title_to_imdb.get(film_data["titolo"])
        film_data["imdb_id"] = imdb_id
        
        payload = dict(film_data)
        payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        payload["source"] = "boxoffice_scraper"
        
        try:
            r = requests.post(BOXOFFICE_SINK_URL, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            print(f"📤 Box office inviato: {film_data['titolo']}")
        except Exception as e:
            print(f"❌ Errore invio box office per {film_data['titolo']}: {e}")
        time.sleep(DELAY)
    
    print(f"\n📤 Invio recensioni a {REVIEWS_SINK_URL}...")
    
    while True:
        for review in all_reviews:
            send_review_event(review)
            ref = review.get("film_title", review.get("imdb_id", "unknown"))
            print(f"📤 Recensione ID={review['review_id'][:8]}... | Film={ref}")
            time.sleep(DELAY)
        if not LOOP:
            break
    
    print("\n🎉 Completato!")


if __name__ == "__main__":
    main()