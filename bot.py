
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]

BASE_URLS = [
    "https://www.ubisoft.com/pt-br/game/the-division/the-division-2/news-updates",
    "https://www.ubisoft.com/en-us/game/the-division/the-division-2/news-updates",
]

HEADERS = {"User-Agent": "Mozilla/5.0"}
DISCORD_HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

def buscar_noticias(url):
    resposta = requests.get(url, headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    soup = BeautifulSoup(resposta.text, "html.parser")

    noticias = []
    base = url.rstrip("/") + "/"

    for link in soup.find_all("a", href=True):
        href = urljoin(base, link["href"])
        if "/news-updates/" not in href:
            continue

        partes = href.rstrip("/").split("/")
        if len(partes) < 2:
            continue

        titulo = link.get_text(" ", strip=True)
        if not titulo or titulo.lower() in ("leia mais", "read more"):
            titulo = ""

        noticias.append({"url": href, "titulo": titulo})

    return noticias

def detalhes_noticia(url, titulo_lista):
    resposta = requests.get(url, headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    soup = BeautifulSoup(resposta.text, "html.parser")

    def meta(nome):
        tag = soup.find("meta", property=nome)
        if not tag:
            tag = soup.find("meta", attrs={"name": nome})
        return tag.get("content", "").strip() if tag else ""

    titulo = meta("og:title") or titulo_lista
    descricao = meta("og:description") or meta("description")
    imagem = meta("og:image")

    if not titulo:
        h1 = soup.find("h1")
        titulo = h1.get_text(" ", strip=True) if h1 else "Notícia oficial Ubisoft"

    return {
        "title": titulo[:250],
        "description": descricao[:1500],
        "image": imagem,
        "url": url
    }

def ja_publicada(url):
    endpoint = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    resposta = requests.get(
        endpoint,
        headers=DISCORD_HEADERS,
        params={"limit": 100},
        timeout=30
    )
    resposta.raise_for_status()

    for mensagem in resposta.json():
        for embed in mensagem.get("embeds", []):
            if embed.get("url") == url:
                return True
    return False

def publicar(noticia):
    endpoint = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

    embed = {
        "title": noticia["title"],
        "url": noticia["url"],
        "description": noticia["description"] or "Confira a notícia oficial da Ubisoft.",
        "color": 0xD6A84F,
        "footer": {"text": "THE DIVISION 2 NEWS • Fonte oficial Ubisoft"}
    }

    if noticia["image"]:
        embed["image"] = {"url": noticia["image"]}

    resposta = requests.post(
        endpoint,
        headers=DISCORD_HEADERS,
        json={"embeds": [embed]},
        timeout=30
    )
    resposta.raise_for_status()
    print("Notícia publicada:", noticia["title"])


def main():
    print("Testando acesso ao Discord...")

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}"

    resposta = requests.get(
        url,
        headers=DISCORD_HEADERS,
        timeout=20
    )

    print("Código de resposta:", resposta.status_code)

    if resposta.status_code == 200:
        canal = resposta.json()
        print("ACESSO CONFIRMADO!")
        print("Nome do canal:", canal.get("name"))
        print("ID do canal:", canal.get("id"))

    elif resposta.status_code == 401:
        print("ERRO: token do bot não foi aceito.")

    elif resposta.status_code == 404:
        print("ERRO: canal não encontrado ou inacessível ao bot.")

    else:
        print("Resposta do Discord:", resposta.text[:500])


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
