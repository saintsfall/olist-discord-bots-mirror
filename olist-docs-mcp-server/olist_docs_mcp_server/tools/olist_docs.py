"""
    Tools MCP de acesso à documentação developers.vnda.com.br.
    Apenas as funções das tools e o registro; lógica de fetch em doc_fetcher.
"""
import re
from typing import Any
from urllib.parse import urljoin

from olist_docs_mcp_server.tools.doc_fetcher import (
    BASE_URL,
    fetch_page_text,
    get_doc_sections,
    relevant_sections,
)

# Padrão para extrair slugs de doc da query (ex.: load_banners em "{% load_banners %}")
DOC_SLUG_PATTERN = re.compile(
    r"(?:^|[\s{%])(load_[a-z_]+|load_tag[s]?|getparam|opengraphfor|gtm|facebook_connect_url)(?:[\s%}]|$)",
    re.IGNORECASE,
)

# Mapeamento: termo na query -> slug da doc (recursos/features que não seguem load_xxx)
QUERY_TO_SLUG = {
    "avise-me": "avise-me-quando-chegar",
    "avise me": "avise-me-quando-chegar",
    "_form_notify": "avise-me-quando-chegar",
    "form_notify": "avise-me-quando-chegar",
    "notify.js": "avise-me-quando-chegar",
}


def _extract_doc_slugs(query: str) -> list[str]:
    """
        Extrai possíveis slugs de página da doc a partir da query (ex.: load_banners, avise-me).
    """

    slugs = []
    q = query.lower()

    for m in DOC_SLUG_PATTERN.finditer(query):
        slug = m.group(1).lower().replace("load_tags", "load_tag")

        if slug not in slugs:
            slugs.append(slug)

    for term, slug in QUERY_TO_SLUG.items():
        if term in q and slug not in slugs:
            slugs.append(slug)

    return slugs


def list_docs_sections() -> list[dict[str, Any]]:
    """
        Lista seções e páginas disponíveis da documentação developers.vnda.com.br.
        Usa crawler da navegação (cache 1h); fallback para lista estática se falhar.
    """

    sections = get_doc_sections()

    return [
        {"title": s["title"], "url": urljoin(
            BASE_URL, s["url"]), "category": s["category"]}
        for s in sections
    ]


def get_olist_docs_context(query: str, max_pages: int = 5) -> list[dict[str, Any]]:
    """
        Busca contexto na documentação Olist para responder à pergunta.
        Faz fetch direto ao site developers.vnda.com.br, extrai texto das páginas
        relevantes e retorna snippets com URL de fonte. Resposta apenas com esse contexto.
        (Equivalente ao Get Context do Context7.)
    """

    results = []
    seen_urls = set()

    # 1) Se a query mencionar um slug de doc (ex.: load_banners, getparam), buscar essa página primeiro
    for slug in _extract_doc_slugs(query):
        doc_url = f"/docs/{slug}"

        if doc_url in seen_urls:
            continue

        try:
            text, full_url = fetch_page_text(doc_url)

            if text.strip():
                snippet = relevant_sections(text, query)

                if not snippet.strip():
                    snippet = text[:12000] + \
                        ("..." if len(text) > 12000 else "")

                results.append({
                    "title": slug,
                    "content": snippet,
                    "source": full_url,
                })

                seen_urls.add(doc_url)

                if len(results) >= max_pages:
                    return results

        except Exception:
            continue

    # 2) Buscar nas seções (crawler com fallback estático; scoring por título/URL)
    sections = get_doc_sections()
    query_lower = query.lower()
    query_terms = [t for t in query_lower.split() if len(t.strip()) > 2]
    query_terms += [m.group(1).lower()
                    for m in DOC_SLUG_PATTERN.finditer(query)]
    query_terms = list(dict.fromkeys(query_terms))
    scored = []

    for s in sections:
        title_lower = s["title"].lower()
        url_lower = s["url"].lower()
        score = sum(
            1 for w in query_terms if w in title_lower or w in url_lower)
        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    to_fetch = [s for _, s in scored[: max_pages * 2]]

    if not to_fetch:
        to_fetch = sections[:max_pages]

    for section in to_fetch:
        if len(results) >= max_pages:
            break

        url = section["url"]

        if url in seen_urls:
            continue

        try:
            text, full_url = fetch_page_text(url)

            if not text.strip():
                continue

            snippet = relevant_sections(text, query)

            if snippet.strip():
                results.append({
                    "title": section["title"],
                    "content": snippet,
                    "source": full_url,
                })
                seen_urls.add(url)

        except Exception:
            continue

    if not results and sections:
        s = sections[0]

        try:
            text, full_url = fetch_page_text(s["url"])

            if text.strip():
                results.append(
                    {"title": s["title"], "content": text[:8000], "source": full_url})

        except Exception:
            pass

    return results


def register_tools(mcp) -> None:
    """
        Registra as tools no FastMCP.
    """
    mcp.tool()(list_docs_sections)
    mcp.tool()(get_olist_docs_context)
