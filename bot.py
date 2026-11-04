
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.ubisoft.com/pt-br/game/the-division/the-division-2/news-updates",
    "https://www.ubisoft.com/en-us/game/the-division/the-division-2/news-updates",
]

for url in URLS:
    print("\nConsultando:", url)

    resposta = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    resposta.raise_for_status()

    soup = BeautifulSoup(resposta.text, "html.parser")

    for titulo in soup.select("h2, h3"):
        texto = titulo.get_text(" ", strip=True)
        if texto:
            print("-", texto)

