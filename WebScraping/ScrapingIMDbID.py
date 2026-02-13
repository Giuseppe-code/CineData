import asyncio
import re
from playwright.async_api import async_playwright


async def get_imdb_id_from_title(film_title: str, headless: bool = True) -> str:
    """
    Cerca un film su IMDb e ritorna l'ID (es. 'tt31434030').
    
    Args:
        film_title: Nome del film da cercare
        headless: Se True, browser invisibile
    
    Returns:
        L'ID IMDb (es. 'tt31434030') o None se non trovato
    """
    async with async_playwright() as p:
        # Usa un user agent realistico per evitare blocchi anti-bot
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='it-IT'
        )
        
        page = await context.new_page()
        
        # Vai su IMDb
        try:
            await page.goto("https://www.imdb.com/", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"⚠️  Errore caricamento IMDb: {e}")
            await browser.close()
            return None
        
        # Aspetta un po' per far caricare la pagina
        await page.wait_for_timeout(2000)
        
        # Accetta cookie se compaiono (prova vari selettori comuni)
        cookie_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Accetta')",
            "button:has-text('Accetta tutto')",
            "button:has-text('Accept all')",
            "button[data-testid='accept-button']",
            ".ipc-btn--accept"
        ]
        
        for selector in cookie_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    await btn.click(timeout=2000)
                    await page.wait_for_timeout(1000)
                    break
            except:
                pass
        
        # Trova la barra di ricerca con timeout più lungo
        try:
            search_input = page.locator('input[data-testid="suggestion-search"]')
            await search_input.wait_for(state="visible", timeout=10000)
        except Exception as e:
            print(f"⚠️  Barra di ricerca non trovata per '{film_title}': {e}")
            print(f"URL corrente: {page.url}")
            
            # Salva screenshot per debug
            await page.screenshot(path=f"debug_imdb_{film_title[:20]}.png")
            await browser.close()
            return None
        
        # Digita il titolo
        await search_input.fill(film_title)
        await page.wait_for_timeout(2000)  # Aumentato timeout per i suggerimenti
        
        # Aspetta che compaiano i risultati nel dropdown
        try:
            suggestions_container = page.locator('div#react-autowhatever-navSuggestionSearch')
            await suggestions_container.wait_for(state="visible", timeout=8000)
        except Exception as e:
            print(f"⚠️  Suggerimenti non apparsi per '{film_title}': {e}")
            await browser.close()
            return None
        
        # Prendi il primo link suggerito
        first_result = suggestions_container.locator('a[href*="/title/tt"]').first
        
        if await first_result.count() == 0:
            print(f"❌ Nessun risultato trovato per '{film_title}'")
            await browser.close()
            return None
        
        # Clicca il primo risultato
        try:
            await first_result.click(timeout=5000)
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception as e:
            print(f"⚠️  Errore clic su risultato per '{film_title}': {e}")
            await browser.close()
            return None
        
        # Estrai l'ID dall'URL corrente
        current_url = page.url
        match = re.search(r'/title/(tt\d+)', current_url)
        
        if match:
            imdb_id = match.group(1)
            print(f"✓ Film '{film_title}' → ID: {imdb_id}")
            await browser.close()
            return imdb_id
        else:
            print(f"❌ Errore: non riesco a estrarre l'ID dall'URL {current_url}")
            await browser.close()
            return None


async def process_multiple_films(film_titles: list[str], headless: bool = True) -> dict:
    """
    Processa una lista di film e ritorna un dizionario {titolo: imdb_id}.
    
    Args:
        film_titles: Lista di titoli di film
        headless: Se True, browser invisibile
    
    Returns:
        Dizionario con titolo → ID IMDb
    """
    results = {}
    
    for title in film_titles:
        print(f"\n🔍 Cerco: {title}")
        imdb_id = await get_imdb_id_from_title(title, headless=headless)
        results[title] = imdb_id
        await asyncio.sleep(1)  # Pausa tra una ricerca e l'altra
    
    return results


# Esempio d'uso
if __name__ == "__main__":
    # Lista di film da cercare
    films = [
        "Dracula",
        "Nosferatu",
        "Mufasa",
        "Il Gladiatore II",
        "Wicked",
        "Sonic 3",
        "Napoli - New York",
        "Conclave",
        "Oceania 2",
        "Better Man"
    ]
    
    # Ottieni gli ID
    results = asyncio.run(process_multiple_films(films, headless=False))
    
    print("\n" + "="*60)
    print("RISULTATI:")
    print("="*60)
    for title, imdb_id in results.items():
        print(f"{title:<30} → {imdb_id}")