"""
    Fetch e extração de texto do site developers.vnda.com.br.
    Funções auxiliares usadas pelas tools; sem lógica de MCP.
    Inclui crawler da navegação para descobrir páginas dinamicamente.
"""
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://developers.vnda.com.br"

# Página com sidebar completa
CRAWL_URL = f"{BASE_URL}/docs/como-funciona-a-customizacao-de-loja"
CRAWL_CACHE_TTL = 3600  # 1 hora em segundos

_crawl_cache: list[dict[str, str]] | None = None
_crawl_cache_time: float = 0

# Fallback quando o crawler falha
DOC_SECTIONS = [
    {"title": "Home", "url": "/", "category": "Geral"},
    {"title": "Guias e Tutoriais", "url": "/docs", "category": "Docs"},
    {"title": "Visão geral da customização",
        "url": "/docs/como-funciona-a-customizacao-de-loja", "category": "Docs"},
    {"title": "Configurações iniciais",
        "url": "/docs/configuracoes-iniciais", "category": "Docs"},
    {"title": "Processo de customização",
        "url": "/docs/processo-de-customizacao", "category": "Docs"},
    {"title": "Ambientes de loja", "url": "/docs/ambientes-de-loja", "category": "Docs"},
    {"title": "Liquid em Vnda", "url": "/docs/funcionamento-do-liquid", "category": "Docs"},
    {"title": "Token de acesso",
        "url": "/docs/chave-de-acesso-e-requisicoes", "category": "Docs"},
    {"title": "Webhooks", "url": "/docs/webhooks", "category": "Docs"},
    {"title": "Referência de API", "url": "/reference", "category": "API"},
    {"title": "Changelog", "url": "/changelog", "category": "Changelog"},
    # Tags Liquid (URLs conforme developers.vnda.com.br/docs/<slug>)
    {"title": "load_banners", "url": "/docs/load_banners", "category": "Tags"},
    {"title": "load_menus", "url": "/docs/load_menus", "category": "Tags"},
    {"title": "load_products", "url": "/docs/load_products", "category": "Tags"},
    {"title": "load_customizations",
        "url": "/docs/load_customizations", "category": "Tags"},
    {"title": "load_media", "url": "/docs/load_media", "category": "Tags"},
    {"title": "load_shop_images", "url": "/docs/load_shop_images", "category": "Tags"},
    {"title": "load_payment_icons",
        "url": "/docs/load_payment_icons", "category": "Tags"},
    {"title": "load_credits", "url": "/docs/load_credits", "category": "Tags"},
    {"title": "load_locals", "url": "/docs/load_locals", "category": "Tags"},
    {"title": "load_videos", "url": "/docs/load_videos", "category": "Tags"},
    {"title": "load_tag e load_tags", "url": "/docs/load_tag", "category": "Tags"},
    {"title": "getparam", "url": "/docs/getparam", "category": "Tags"},
    {"title": "opengraphfor", "url": "/docs/opengraphfor", "category": "Tags"},
    {"title": "gtm", "url": "/docs/gtm", "category": "Tags"},
    {"title": "facebook_connect_url",
        "url": "/docs/facebook_connect_url", "category": "Tags"},
    # Templates de página
    {"title": "layout.liquid", "url": "/docs/layout", "category": "Templates"},
    {"title": "home.liquid", "url": "/docs/home", "category": "Templates"},
    {"title": "product.liquid", "url": "/docs/product", "category": "Templates"},
    {"title": "cart", "url": "/docs/cart", "category": "Templates"},
    # Outros guias úteis
    {"title": "Cálculo de frete",
        "url": "/docs/calculo-de-frete-na-pagina-de-produto", "category": "Docs"},
    {"title": "Organização dos arquivos",
        "url": "/docs/organizacao-dos-arquivos", "category": "Docs"},
    # Recursos da plataforma
    {"title": "Avise-me quando chegar",
        "url": "/docs/avise-me-quando-chegar", "category": "Recursos"},
    {"title": "Auto preenchimento de endereço pelo CEP",
        "url": "/docs/auto-preenchimento-de-endereco-pelo-cep", "category": "Recursos"},
]


def _crawl_docs_index(timeout: int = 15) -> list[dict[str, str]]:
    """
        Faz fetch da página de docs e extrai links do sidebar (href começando com /docs/).
        Retorna lista [{title, url, category}]. Em caso de erro, retorna lista vazia.
    """

    sections: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    try:
        resp = requests.get(CRAWL_URL, timeout=timeout, headers={
                            "User-Agent": "OlistDocsMCP/1.0"})

        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Coleta somente o host (dominio + porta) para validação posterior
        base_host = urlparse(BASE_URL).netloc

        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()

            # Pula a varredura caso o link esteja em branco, seja para documentação externa ou seja pagina de login
            if not href or "docs.google.com" in href or "/login" in href:
                continue

            parsed = urlparse(href)

            # Pula a varredura caso o seja o mesmo host
            if parsed.netloc and parsed.netloc != base_host:
                continue

            path = parsed.path or href

            if not path.startswith("/docs/") or path == "/docs" or path == "/docs/":
                continue

            path = path.rstrip("/")

            if path in seen_paths:
                continue

            title = link.get_text(strip=True)

            if not title or len(title) < 2:
                title = path.split("/")[-1].replace("-", " ").replace("_", " ")

            seen_paths.add(path)
            sections.append({"title": title, "url": path, "category": "Docs"})

    except Exception:
        pass

    return sections


def get_doc_sections() -> list[dict[str, str]]:
    """
        Retorna a lista de seções da doc. Usa crawler com cache (TTL 1h).
        Se o crawler falhar ou retornar vazio, usa DOC_SECTIONS como fallback.
    """

    global _crawl_cache, _crawl_cache_time

    now = time.monotonic()

    if _crawl_cache is not None and (now - _crawl_cache_time) < CRAWL_CACHE_TTL:
        return _crawl_cache

    crawled = _crawl_docs_index()

    if crawled:
        _crawl_cache = crawled
        _crawl_cache_time = now
        return crawled

    # Fallback para as URLs estáticas
    return DOC_SECTIONS


def fetch_page_text(url: str, timeout: int = 15) -> tuple[str, str]:
    """
        Faz GET na URL, extrai texto do HTML (conteúdo principal) e retorna (texto_limpo, url_final).
        Usa seletores semânticos (main, article) para reduzir quebra se o layout mudar.
    """

    full_url = url if url.startswith("http") else urljoin(BASE_URL, url)

    resp = requests.get(full_url, timeout=timeout, headers={
                        "User-Agent": "VndaDocsMCP/1.0"})

    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    parts = soup.find_all("main") + soup.find_all("article")

    if not parts:
        parts = [soup.body] if soup.body else []

    if not parts:
        return "", full_url

    text = "\n\n".join(p.get_text(separator="\n", strip=True)
                       for p in parts if p)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text, full_url


def relevant_sections(text: str, query: str, max_chars: int = 12000) -> str:
    """
        Filtra trechos que contenham termos da query e limita tamanho.
    """

    query_lower = query.lower()

    terms = [t.strip() for t in query_lower.split() if len(t.strip()) > 2]

    if not terms:
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    paragraphs = text.split("\n\n")
    scored = []

    for p in paragraphs:
        if len(p.strip()) < 20:
            continue

        pl = p.lower()

        score = sum(1 for t in terms if t in pl)

        if score > 0:
            scored.append((score, p))

    if not scored:
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    scored.sort(key=lambda x: -x[0])
    out = []
    total = 0

    for _, p in scored:
        if total + len(p) > max_chars:
            break

        out.append(p)
        total += len(p)

    return "\n\n".join(out) if out else text[:max_chars] + ("..." if len(text) > max_chars else "")
