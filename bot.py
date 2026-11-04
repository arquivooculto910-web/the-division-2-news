
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
    pt = buscar_noticias(BASE_URLS[0])
    en = buscar_noticias(BASE_URLS[1])

    ingles_por_url = {n["url"]: n for n in en}
    noticias = []

    # Prioriza a página em português.
    for noticia in pt:
        noticias.append(noticia)

    # Usa notícias em inglês que não aparecem na página portuguesa.
    urls_pt = {n["url"] for n in pt}
    for noticia in en:
        if noticia["url"] not in urls_pt:
            noticias.append(noticia)

    print("Notícias encontradas:", len(noticias))

    # Processa primeiro as publicações mais recentes da página.
    for item in noticias[:15]:
        try:
            detalhe = detalhes_noticia(item["url"], item["titulo"])

            if ja_publicada(detalhe["url"]):
                print("Já publicada:", detalhe["title"])
                continue

            publicar(detalhe)
            break

        except Exception as erro:
            print("Erro ao processar notícia:", erro)

    print("Verificação concluída.")

if __name__ == "__main__":
    main()
