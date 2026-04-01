#!/usr/bin/env python3
"""
Scraper de eventos e programas em Sao Paulo.
Fontes: Catraca Livre, Sympla, Ingresso.com, Veja SP, G1 Guia SP, Guia Folha
Roda automaticamente seg/qua/sex via GitHub Actions.
Gera suggestions.json consumido pelo front-end.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time
import re
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ============================================================
# SCRAPERS
# ============================================================

def scrape_catracalivre():
    """Catraca Livre - programas gratuitos e culturais em SP."""
    items = []
    url = "https://catracalivre.com.br/gira/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for article in soup.select("article.post")[:15]:
            title_el = article.select_one("h2.entry-title a, h3.entry-title a")
            desc_el  = article.select_one(".entry-summary p, .entry-content p")
            link_el  = article.select_one("a[href]")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            desc  = desc_el.get_text(strip=True)[:120] if desc_el else ""
            link  = title_el.get("href") or (link_el.get("href") if link_el else "")

            category = classify_category(title + " " + desc)
            items.append({
                "name": title,
                "category": category,
                "desc": desc,
                "address": "Sao Paulo, SP",
                "date": "",
                "hours": "",
                "tags": auto_tags(title + " " + desc, category),
                "source": "Catraca Livre",
                "link": link,
            })

        print(f"  [Catraca Livre] {len(items)} items")
    except Exception as e:
        print(f"  [Catraca Livre] ERRO: {e}")
    return items


def scrape_sympla():
    """Sympla - eventos pagos e gratuitos em SP."""
    items = []
    url = "https://www.sympla.com.br/eventos/sao-paulo-sp"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("a.sympla-card, div[class*='EventCard'], article[class*='event']")[:15]:
            title_el = card.select_one("h2, h3, [class*='title'], [class*='name']")
            date_el  = card.select_one("[class*='date'], time, [class*='when']")
            local_el = card.select_one("[class*='location'], [class*='venue'], [class*='local']")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 4:
                continue

            date  = date_el.get_text(strip=True)[:50] if date_el else ""
            local = local_el.get_text(strip=True)[:80] if local_el else "Sao Paulo, SP"
            link  = card.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.sympla.com.br" + link

            category = classify_category(title)
            items.append({
                "name": title,
                "category": category,
                "desc": "",
                "address": local,
                "date": date,
                "hours": "",
                "tags": auto_tags(title, category),
                "source": "Sympla",
                "link": link,
            })

        print(f"  [Sympla] {len(items)} items")
    except Exception as e:
        print(f"  [Sympla] ERRO: {e}")
    return items


def scrape_ingresso():
    """Ingresso.com - shows, teatro e cinema em SP."""
    items = []
    url = "https://www.ingresso.com/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("div[class*='card'], article[class*='event'], li[class*='item']")[:15]:
            title_el = card.select_one("h2, h3, h4, [class*='title'], [class*='name']")
            date_el  = card.select_one("[class*='date'], time")

            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 4:
                continue

            date = date_el.get_text(strip=True)[:50] if date_el else ""
            link_el = card.select_one("a[href]")
            link = link_el.get("href", "") if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.ingresso.com" + link

            category = classify_category(title)
            items.append({
                "name": title,
                "category": category,
                "desc": "",
                "address": "Sao Paulo, SP",
                "date": date,
                "hours": "",
                "tags": auto_tags(title, category),
                "source": "Ingresso.com",
                "link": link,
            })

        print(f"  [Ingresso.com] {len(items)} items")
    except Exception as e:
        print(f"  [Ingresso.com] ERRO: {e}")
    return items


def scrape_vejaSP():
    """Veja SP - guia de bares, restaurantes e programas."""
    items = []
    url = "https://vejasp.abril.com.br/estabelecimento/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for article in soup.select("article, div[class*='post'], div[class*='card']")[:15]:
            title_el = article.select_one("h2 a, h3 a, h2, h3")
            desc_el  = article.select_one("p")

            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 4:
                continue

            desc = desc_el.get_text(strip=True)[:120] if desc_el else ""
            link = title_el.get("href", "") if title_el.name == "a" else ""

            category = classify_category(title + " " + desc)
            items.append({
                "name": title,
                "category": category,
                "desc": desc,
                "address": "Sao Paulo, SP",
                "date": "",
                "hours": "",
                "tags": auto_tags(title + " " + desc, category),
                "source": "Veja SP",
                "link": link,
            })

        print(f"  [Veja SP] {len(items)} items")
    except Exception as e:
        print(f"  [Veja SP] ERRO: {e}")
    return items


def scrape_guia_folha():
    """Guia Folha - o que fazer em SP."""
    items = []
    url = "https://guia.folha.uol.com.br/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for article in soup.select("div[class*='c-headline'], article, div[class*='news']")[:15]:
            title_el = article.select_one("h2 a, h3 a, h2, h3, a[class*='title']")
            desc_el  = article.select_one("p, [class*='summary']")

            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 4:
                continue

            desc = desc_el.get_text(strip=True)[:120] if desc_el else ""
            link = title_el.get("href", "")
            if link and link.startswith("/"):
                link = "https://guia.folha.uol.com.br" + link

            category = classify_category(title + " " + desc)
            items.append({
                "name": title,
                "category": category,
                "desc": desc,
                "address": "Sao Paulo, SP",
                "date": "",
                "hours": "",
                "tags": auto_tags(title + " " + desc, category),
                "source": "Guia Folha",
                "link": link,
            })

        print(f"  [Guia Folha] {len(items)} items")
    except Exception as e:
        print(f"  [Guia Folha] ERRO: {e}")
    return items


def scrape_g1_guia():
    """G1 Guia SP - agenda cultural."""
    items = []
    url = "https://g1.globo.com/guia/guia-sp/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for article in soup.select("div[class*='feed-post'], div[class*='bastian-feed-item']")[:15]:
            title_el = article.select_one("a.feed-post-link, h2 a, h3 a, a[class*='title']")
            desc_el  = article.select_one("div[class*='summary'], p")

            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 4:
                continue

            desc = desc_el.get_text(strip=True)[:120] if desc_el else ""
            link = title_el.get("href", "")

            category = classify_category(title + " " + desc)
            items.append({
                "name": title,
                "category": category,
                "desc": desc,
                "address": "Sao Paulo, SP",
                "date": "",
                "hours": "",
                "tags": auto_tags(title + " " + desc, category),
                "source": "G1 Guia SP",
                "link": link,
            })

        print(f"  [G1 Guia SP] {len(items)} items")
    except Exception as e:
        print(f"  [G1 Guia SP] ERRO: {e}")
    return items


# ============================================================
# CLASSIFICACAO AUTOMATICA
# ============================================================

CATEGORY_KEYWORDS = {
    "sesc": ["sesc"],
    "musical": ["musical", "teatro musical", "broadway", "encenacao", "peca musical"],
    "cinema": ["cinema", "filme", "movie", "estreia no cinema", "em cartaz"],
    "show": ["show", "concert", "banda", "cantor", "cantora", "rock", "sertanejo",
             "mpb", "jazz", "pagode", "samba", "rap", "funk", "eletronica", "turnê", "turne"],
    "bar": ["bar ", "barzinho", "pub", "cerveja", "chopp", "drinks", "coquetel", "balada"],
    "restaurante": ["restaurante", "gastronomia", "chef", "culinaria", "comida",
                    "pizza", "hamburguer", "sushi", "jantar", "almoco", "brunch",
                    "cafe ", "cafeteria", "bistr"],
    "evento": ["festival", "feira", "exposicao", "exposição", "mostra", "evento",
               "encontro", "conferencia", "workshop", "inauguracao"],
    "passeio": ["parque", "museu", "galeria", "mirante", "tour", "passeio",
                "caminhada", "trilha", "jardim", "zoologico", "aquario"],
}

def normalize(text):
    replacements = {
        "á":"a","à":"a","ã":"a","â":"a","é":"e","ê":"e",
        "í":"i","ó":"o","ô":"o","õ":"o","ú":"u","ü":"u","ç":"c",
    }
    text = text.lower()
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def classify_category(text):
    t = normalize(text)
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return cat
    return "evento"


AUTO_TAG_MAP = {
    "gratuito": ["gratuito", "gratis", "free", "entrada franca"],
    "ao-ar-livre": ["ao ar livre", "parque", "praca", "jardim"],
    "infantil": ["infantil", "crianca", "familia", "kids"],
    "pizza": ["pizza"],
    "hamburguer": ["hamburguer", "burger"],
    "japones": ["japones", "sushi", "temaki", "nikkei"],
    "italiano": ["italiano", "massas", "pasta"],
    "rock": ["rock"],
    "samba": ["samba", "pagode"],
    "MPB": ["mpb"],
    "sertanejo": ["sertanejo"],
    "jazz": ["jazz", "blues"],
    "teatro": ["teatro", "peca", "encenacao"],
    "musical": ["musical"],
    "estreia": ["estreia"],
    "festival": ["festival"],
    "feira": ["feira"],
    "exposicao": ["exposicao", "exposição", "mostra"],
    "rooftop": ["rooftop", "terraço", "terraco"],
    "cerveja-artesanal": ["cerveja artesanal", "craft beer"],
}

def auto_tags(text, category):
    t = normalize(text)
    tags = []
    for tag, keywords in AUTO_TAG_MAP.items():
        for kw in keywords:
            if normalize(kw) in t:
                tags.append(tag)
                break
    return list(set(tags))[:4]


# ============================================================
# DEDUPLICACAO
# ============================================================

def deduplicate(items):
    seen = set()
    unique = []
    for item in items:
        key = normalize(item["name"])[:40]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("  Buscando novidades em Sao Paulo")
    print("=" * 60)

    all_items = []

    scrapers = [
        ("Catraca Livre", scrape_catracalivre),
        ("Sympla",        scrape_sympla),
        ("Ingresso.com",  scrape_ingresso),
        ("Veja SP",       scrape_vejaSP),
        ("Guia Folha",    scrape_guia_folha),
        ("G1 Guia SP",    scrape_g1_guia),
    ]

    for name, fn in scrapers:
        print(f"\nRodando: {name}...")
        results = fn()
        all_items.extend(results)
        time.sleep(1.5)

    print(f"\n--- Total bruto: {len(all_items)} ---")
    all_items = deduplicate(all_items)
    # Filtrar titulos muito curtos ou genericos
    all_items = [i for i in all_items if len(i["name"]) > 5]
    print(f"--- Apos deduplicacao: {len(all_items)} ---")

    output = {
        "updated_at": datetime.now().strftime("%d/%m/%Y as %H:%M"),
        "items": all_items,
    }

    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "suggestions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] suggestions.json gerado com {len(all_items)} items")


if __name__ == "__main__":
    main()
