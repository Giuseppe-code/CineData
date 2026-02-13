import asyncio
import re
from playwright.async_api import async_playwright


def imdb_reviews_url(imdb_url: str) -> str:
    """
    Accetta URL tipo:
      - https://www.imdb.com/title/tt22898462/
      - https://www.imdb.com/it/title/tt22898462/
      - https://www.imdb.com/it/title/tt22898462/reviews/?ref_=...
    e ritorna sempre:
      https://www.imdb.com/title/tt22898462/reviews/?ref_=ttrt_sa_3
    """
    m = re.search(r"/title/(tt\d+)", imdb_url)
    if not m:
        raise ValueError("URL IMDb non valido: non trovo /title/ttXXXXXXXX/")
    tt = m.group(1)
    return f"https://www.imdb.com/title/{tt}/reviews/?ref_=ttrt_sa_3"


async def scrape_imdb_reviews_from_url(
    imdb_url: str,
    max_reviews: int = 50,
    headless: bool = True,
):
    """
    Ritorna una lista di dict con le recensioni trovate (fino a max_reviews).
    """
    target = imdb_reviews_url(imdb_url)

    async with async_playwright() as p:
        # Anti-bot: usa user agent realistico e disabilita automation flags
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
            locale='en-US'  # Usa inglese per evitare redirect strani
        )
        
        page = await context.new_page()

        try:
            await page.goto(target, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"❌ Errore caricamento pagina recensioni: {e}")
            await browser.close()
            return []

        # Aspetta che la pagina si carichi completamente
        await page.wait_for_timeout(3000)

        # Tentativo "soft" di accettare cookie/consensi (più selettori)
        cookie_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "button:has-text('Accetta')",
            "button:has-text('Accetta tutto')",
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

        # Debug: verifica se la pagina ha caricato le recensioni
        html_content = await page.content()
        
        # Selettore del bottone "load more" (varia)
        load_more = page.locator(
            "button[data-testid='load-more-trigger'], "
            "button:has-text('Load More'), "
            "button:has-text('Carica altro'), "
            "button:has-text('Mostra altro')"
        )

        # Selettori delle card recensioni (variano nel tempo)
        cards_locator = page.locator(
            "article.user-review-item, "
            "div[data-testid='review-card-parent'], "
            ".review-container"
        )

        # Aspetta che compaiano le recensioni
        try:
            await cards_locator.first.wait_for(state="visible", timeout=10000)
        except Exception as e:
            print(f"⚠️  Nessuna recensione trovata sulla pagina: {e}")
            print(f"URL: {target}")
            # Salva screenshot per debug
            await page.screenshot(path=f"debug_reviews_{imdb_url.split('/')[-2]}.png")
            await browser.close()
            return []

        async def expand_all_visible_reviews():
            """
            Clicca i bottoni 'Mostra altro' dentro le recensioni visibili,
            così il testo completo finisce dentro ipc-html-content-inner-div.
            """
            buttons = page.locator(
                "article.user-review-item button.ipc-overflowText-overlay, "
                "div[data-testid='review-card-parent'] button.ipc-overflowText-overlay, "
                "button:has-text('more')"
            )
            n = await buttons.count()
            for i in range(n):
                try:
                    await buttons.nth(i).click(timeout=1000)
                    await page.wait_for_timeout(200)  # delay per render
                except:
                    pass  # se non cliccabile / già espanso

        reviews = []
        seen = set()  # dedup sul testo

        async def extract_all_current_cards():
            out = []
            count = await cards_locator.count()
            
            print(f"  📝 Trovate {count} card recensioni sulla pagina")

            for i in range(count):
                c = cards_locator.nth(i)

                async def pick_text(selectors):
                    for sel in selectors:
                        loc = c.locator(sel)
                        if await loc.count() > 0:
                            try:
                                t = (await loc.first.inner_text()).strip()
                                if t:
                                    return t
                            except:
                                pass
                    return ""

                # Titolo recensione (data-testid è stabile)
                title = await pick_text([
                    "[data-testid='review-summary'] h3",
                    "[data-testid='review-summary']",
                    ".title"
                ])

                # TESTO COMPLETO: sta qui (stabile) dopo "Mostra altro"
                text = await pick_text([
                    "div[data-testid='review-overflow'] .ipc-html-content-inner-div",
                    "div[data-testid='review-overflow']",
                    ".text.show-more__control",
                    ".content .text"
                ])

                # Rating: nello span con classe review-rating e numero in ipc-rating-star--rating
                rating = await pick_text([
                    "span.review-rating span.ipc-rating-star--rating",
                    "span.review-rating",
                    ".ipc-rating-star--rating"
                ])

                # Autore e data
                author = await pick_text([
                    "a[data-testid='author-link']",
                    ".display-name-link"
                ])
                date = await pick_text([
                    "li.review-date",
                    ".review-date"
                ])

                if text:
                    out.append({
                        "imdb_reviews_url": target,
                        "review_title": title,
                        "review_text": text,
                        "review_rating": rating,
                        "review_author": author,
                        "review_date": date,
                    })
                else:
                    # Debug: stampa cosa ha trovato
                    print(f"    ⚠️  Card {i+1}: nessun testo trovato (title={bool(title)})")

            return out

        # Ciclo: estrai, poi carica altre se servono
        iterations = 0
        max_iterations = 20  # Previeni loop infiniti
        
        while len(reviews) < max_reviews and iterations < max_iterations:
            iterations += 1
            
            await expand_all_visible_reviews()
            current = await extract_all_current_cards()
            
            new_reviews = 0
            for r in current:
                key = r["review_text"]
                if key not in seen:
                    seen.add(key)
                    reviews.append(r)
                    new_reviews += 1

                    if len(reviews) >= max_reviews:
                        break
            
            print(f"  ✓ Iterazione {iterations}: {new_reviews} nuove recensioni (totale: {len(reviews)})")

            if len(reviews) >= max_reviews:
                break

            # Se non ci sono nuove recensioni e non c'è il bottone load more, esci
            if new_reviews == 0 and await load_more.count() == 0:
                print("  ℹ️  Nessuna nuova recensione e nessun bottone 'Load More'")
                break

            # Se c'è il bottone load more, cliccalo
            if await load_more.count() > 0:
                try:
                    await load_more.first.click(timeout=4000)
                    await page.wait_for_timeout(2000)  # Aumentato da 1200 a 2000
                    await expand_all_visible_reviews()
                except Exception as e:
                    print(f"  ⚠️  Errore clic su 'Load More': {e}")
                    break
            else:
                # Nessun bottone, esci
                break

        await browser.close()
        print(f"✅ Totale recensioni estratte: {len(reviews)}")
        return reviews[:max_reviews]


if __name__ == "__main__":
    imdb_link = "https://www.imdb.com/title/tt1757678/"
    out = asyncio.run(scrape_imdb_reviews_from_url(imdb_link, max_reviews=30, headless=True))
    print("\n" + "="*60)
    print(f"Recensioni estratte: {len(out)}")
    print("="*60)
    for i, r in enumerate(out, 1):
        print("\n---", i, "---")
        print("Titolo:", r["review_title"])
        print("Rating:", r["review_rating"])
        print("Autore:", r["review_author"])
        print("Data:", r["review_date"])
        print("Testo:", r["review_text"][:200], "..." if len(r["review_text"]) > 200 else "")