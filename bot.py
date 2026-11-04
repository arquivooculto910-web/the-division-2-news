
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

BASE_URLS = [
    "https://www.ubisoft.com/pt-br/game/the-division/the-division-2/news-updates",
    "https://www.ubisoft.com/en-us/game/the-division/the-division-2/news-updates",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Division2NewsBot/1.0)"
}

DISCORD_HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

API = "https://discord.com/api/v10"


def buscar_noticias():
    noticias = []

    for pagina in BASE_URLS:
        try:
            resposta = requests.get(
                pagina,
                headers=HEADERS,
                timeout=30
            )
            resposta.raise_for_status()

            soup = BeautifulSoup(resposta.text, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link["href"]
                titulo = link.get_text(" ", strip=True)

                if not titulo or len(titulo) < 8:
                    continue

                url = urljoin(pagina, href)

                if "ubisoft.com" not in url:
                    continue

                if "news" not in url.lower():
                    continue

                imagem = None
                img = link.find("img")

                if img:
                    imagem = img.get("src") or img.get("data-src")

                if imagem:
                    imagem = urljoin(pagina, imagem)

                noticia = {
                    "titulo": titulo,
                    "url": url,
                    "imagem": imagem,
                    "idioma": "pt" if "/pt-br/" in pagina else "en"
                }

                if not any(n["url"] == url for n in noticias):
                    noticias.append(noticia)

        except requests.RequestException as erro:
            print(f"Erro ao consultar {pagina}: {erro}")

    return noticias


def buscar_mensagens_publicadas():
    url = f"{API}/channels/{CHANNEL_ID}/messages"

    resposta = requests.get(
        url,
        headers=DISCORD_HEADERS,
        params={"limit": 100},
        timeout=20
    )

    if resposta.status_code != 200:
        print("Erro ao consultar histórico:", resposta.status_code)
        print(resposta.text[:500])
        return None

    mensagens = resposta.json()
    urls = set()

    for mensagem in mensagens:
        for embed in mensagem.get("embeds", []):
            link = embed.get("url")
            if link:
                urls.add(link)

    return urls


def publicar_noticia(noticia):
    embed = {
        "title": noticia["titulo"][:256],
        "url": noticia["url"],
        "description": (
            "Confira esta atualização oficial de "
            "Tom Clancy's The Division 2 no site da Ubisoft."
        ),
        "color": 0xD6A52A,
        "footer": {
            "text": "THE DIVISION 2 NEWS • Fonte oficial: Ubisoft"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if noticia.get("imagem"):
        embed["image"] = {"url": noticia["imagem"]}

    url = f"{API}/channels/{CHANNEL_ID}/messages"

    resposta = requests.post(
        url,
        headers=DISCORD_HEADERS,
        json={"embeds": [embed]},
        timeout=20
    )

    if resposta.status_code == 200:
        print("Notícia publicada:", noticia["titulo"])
        return True

    print("Erro ao publicar:", resposta.status_code)
    print(resposta.text[:500])
    return False


def main():
    if not TOKEN or not CHANNEL_ID:
        print("ERRO: configure DISCORD_TOKEN e DISCORD_CHANNEL_ID.")
        return

    print("Buscando notícias oficiais da Ubisoft...")

    publicadas = buscar_mensagens_publicadas()

    if publicadas is None:
        print("Não foi possível consultar o canal. Publicação cancelada.")
        return

    noticias = buscar_noticias()

    if not noticias:
        print("Nenhuma notícia encontrada nas páginas consultadas.")
        return

    novas = [
        noticia for noticia in noticias
        if noticia["url"] not in publicadas
    ]

    if not novas:
        print("Nenhuma notícia nova encontrada.")
        return

    # Publica no máximo 3 notícias por execução.
    for noticia in novas[:3]:
        publicar_noticia(noticia)


if __name__ == "__main__":
    main()
