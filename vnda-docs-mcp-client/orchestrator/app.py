"""
    FastAPI app: rota POST /answer recebe payload do bot e devolve resposta (content, attachment_content, guardrail_triggered).
    Habilita/desabilita: o bot usa este serviço apenas se ORCHESTRATOR_URL estiver definida.
    - attachment_content: quando a resposta tem > 2000 caracteres, content vira preview (500 chars) e o texto completo vai em attachment_content (bot envia como anexo).
    - guardrail_triggered: quando a mensagem do usuário é sinalizada pela moderação (OpenAI Moderation), retornamos True e uma mensagem de bloqueio.
"""
from orchestrator.llm import answer_with_mcp
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import logging
import os
from typing import Any, Literal

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Limite do Discord para mensagem em texto; acima disso enviamos preview + anexo (igual N8N)
MAX_MESSAGE_LENGTH = 2000
PREVIEW_LENGTH = 500
GUARDRAIL_MESSAGE = (
    "Sua mensagem foi bloqueada pelos guardrails de segurança. "
    "Revise o conteúdo e tente novamente com uma pergunta relacionada à documentação da plataforma."
)


def _prepare_content_and_attachment(full_content: str) -> tuple[str, str | None]:
    """
        Se a resposta tiver mais de MAX_MESSAGE_LENGTH caracteres, devolve preview (PREVIEW_LENGTH chars)
        em content e o texto completo em attachment_content; senão content = full_content e attachment = None.
        Alinhado ao comportamento do N8N (Validação e preparação).
    """

    size = len(full_content)

    if size <= MAX_MESSAGE_LENGTH:
        return full_content, None

    preview = full_content[:PREVIEW_LENGTH]
    suffix = f"\n\n...\n\n*Resposta completa em arquivo anexado ({size} caracteres)*"

    return preview + suffix, full_content


async def _check_guardrails(user_message: str) -> bool:
    """
        Verifica a mensagem do usuário com OpenAI Moderation API.
        Retorna True se algum critério for sinalizado (mensagem deve ser bloqueada).
    """

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        mod = await client.moderations.create(input=user_message)

        if mod.results and len(mod.results) > 0:
            return mod.results[0].flagged

    except Exception as e:
        logger.warning("Guardrails (Moderation) não disponível: %s", e)

    return False


def _format_exception(e: BaseException) -> str:
    """
        Desempacota ExceptionGroup/BaseExceptionGroup para mostrar a causa real.
    """

    if getattr(e, "exceptions", None) is not None:
        parts = [str(e)]

        for sub in e.exceptions:
            parts.append(f"  -> {_format_exception(sub)}")

        return "\n".join(parts)

    cause = getattr(e, "__cause__", None) or getattr(e, "__context__", None)

    if cause and cause is not e:
        return f"{e!r}\n  causa: {_format_exception(cause)}"

    return repr(e)


app = FastAPI(title="Vnda Docs MCP Orchestrator", version="0.1.0")


class HistoryMessage(BaseModel):
    """
        Uma mensagem do histórico da conversa (pergunta ou resposta anterior).
    """

    role: Literal["user", "assistant"]
    content: str


class DiscordPayload(BaseModel):
    """
        Contrato igual ao enviado ao N8N pelo bot.
        history: opcional, mensagens anteriores da thread para follow-ups (ex.: "não entendi", "me envie o código completo").
    """

    message: str
    discord: dict[str, str]
    author: dict[str, str]
    history: list[HistoryMessage] | None = None


class AnswerResponse(BaseModel):
    """
        Contrato de resposta para o bot.
    """

    content: str
    attachment_content: str | None = None
    guardrail_triggered: bool = False


@app.post("/answer", response_model=AnswerResponse)
async def answer(payload: DiscordPayload) -> AnswerResponse:
    """
        Recebe a pergunta do bot (mesmo payload do N8N), conecta ao MCP Server,
        usa OpenAI com as tools do MCP e devolve a resposta.
    """

    mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")

    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500, detail="OPENAI_API_KEY não configurada")

    try:
        from mcp.client.session import ClientSession
        from mcp.client.streamable_http import streamable_http_client

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dependência MCP client não disponível: {e}. Instale com: uv sync",
        ) from e

    # Guardrails: moderação da mensagem do usuário (equivalente ao nó Guardrails do N8N)
    if await _check_guardrails(payload.message):
        return AnswerResponse(
            content=GUARDRAIL_MESSAGE,
            attachment_content=None,
            guardrail_triggered=True,
        )

    try:
        async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                history = [{"role": m.role, "content": m.content}
                           for m in (payload.history or [])]
                full_content = await answer_with_mcp(payload.message, session, history=history)

                # Preview + anexo quando > 2000 caracteres (Discord limita mensagem; igual N8N)
                content, attachment_content = _prepare_content_and_attachment(
                    full_content)
                return AnswerResponse(
                    content=content,
                    attachment_content=attachment_content,
                    guardrail_triggered=False,
                )

    except Exception as e:
        msg = _format_exception(e)
        logger.exception("Erro ao usar MCP ou OpenAI: %s", msg)
        raise HTTPException(
            status_code=502, detail=f"Erro ao usar MCP ou OpenAI: {msg}") from e


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check para o Shard Cloud."""
    return {"status": "ok"}
