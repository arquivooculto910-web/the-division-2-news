
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

ARQUIVO_CONTROLE = "noticias_publicadas.json"

PAGINAS = [
    {
        "url": "https://www.ubisoft.com/pt-br/game/the-division/the-division-2/news-updates",
        "idioma": "pt"
    },
    {
        "url": "https://www.ubisoft.com/en-us/game/the-division/the-division-2/news-updates",
        "idioma": "en"
    }
]

HEADERS_SITE = {
    "User-Agent": "Mozilla/5.0 (compatible; Division2NewsBot/1.0)"
}

HEADERS_DISCORD = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

API = "https://discord.com/api/v10"


def carregar_controle():
    try:
        with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as arquivo:
            return set(json.load(arquivo))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def salvar_controle(urls):
    with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as arquivo:
        json.dump(sorted(urls), arquivo, ensure_ascii=False, indent=2)


def buscar_noticias():
    noticias = {}

    for pagina in PAGINAS:
        try:
            resposta = requests.get(
                pagina["url"],
                headers=HEADERS_SITE,
                timeout=30
            )
            resposta.raise_for_status()

            soup = BeautifulSoup(resposta.text, "html.parser")

            for link in soup.find_all("a", href=True):
                titulo = link.get_text(" ", strip=True)
                url = urljoin(pagina["url"], link["href"])

                if not titulo or len(titulo) < 8:
                    continue

                if "ubisoft.com" not in url:
                    continue

                if "news" not in url.lower():
                    continue

                imagem = None
                img = link.find("img")

                if img:
                    imagem = img.get("src") or img.get("data-src")

                if imagem:
                    imagem = urljoin(pagina["url"], imagem)

                chave = url.split("?")[0].rstrip("/")

                noticia = {
                    "titulo": titulo,
                    "url": url,
                    "imagem": imagem,
                    "idioma": pagina["idioma"]
                }

                if chave not in noticias or pagina["idioma"] == "pt":
                    noticias[chave] = noticia

        except requests.RequestException as erro:
            print(f"Erro ao consultar {pagina['url']}: {erro}")

    return list(noticias.items())


def publicar_noticia(noticia):
    embed = {
        "title": noticia["titulo"][:256],
        "url": noticia["url"],
        "description": (
            "Confira esta notícia oficial de "
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

    resposta = requests.post(
        f"{API}/channels/{CHANNEL_ID}/messages",
        headers=HEADERS_DISCORD,
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
        print("ERRO: secrets do Discord não configurados.")
        return

    print("Consultando notícias oficiais da Ubisoft...")

    noticias = buscar_noticias()

    if not noticias:
        print("Nenhuma notícia encontrada.")
        return

    conhecidas = carregar_controle()

    # Primeira execução: registra as notícias existentes sem publicá-las.
    if not conhecidas:
        conhecidas = {chave for chave, noticia in noticias}
        salvar_controle(conhecidas)
        print("Marco inicial criado. Notícias antigas não serão publicadas.")
        return

    novas = [
        (chave, noticia)
        for chave, noticia in noticias
        if chave not in conhecidas
    ]

    if not novas:
        print("Nenhuma notícia nova encontrada.")
        return

    # Publica primeiro as notícias novas em português, quando disponíveis.
    novas.sort(key=lambda item: item[1]["idioma"] != "pt")

    for chave, noticia in novas[:3]:
        if publicar_noticia(noticia):
            conhecidas.add(chave)
            salvar_controle(conhecidas)


if __name__ == "__main__":
    main()
