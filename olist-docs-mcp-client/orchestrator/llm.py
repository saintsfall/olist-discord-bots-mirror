"""
    Integração OpenAI + MCP: obtém contexto via tools do MCP e gera resposta com ChatGPT.
    Uma única responsabilidade: orquestrar chamadas ao LLM e ao MCP.
"""
import json
import os
from typing import Any

from openai import AsyncOpenAI

from orchestrator.prompts import SYSTEM_PROMPT

# Schemas das tools em formato OpenAI (espelhando o MCP Server)
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_docs_sections",
            "description": "Lista seções e páginas disponíveis da documentação developers.vnda.com.br. Use para descobrir categorias e URLs antes de pedir contexto.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_olist_docs_context",
            "description": "Busca contexto na documentação Olist para responder à pergunta. Retorna snippets com URL de fonte. Use antes de responder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Pergunta ou termos de busca"},
                    "max_pages": {"type": "integer", "description": "Máximo de páginas a buscar", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]


async def call_mcp_tool(mcp_session, name: str, arguments: dict[str, Any]) -> str:
    """
        Chama uma tool no MCP Server e retorna o conteúdo como string para o LLM.
    """

    try:
        result = await mcp_session.call_tool(name, arguments=arguments or {})

        if getattr(result, "isError", False):
            return json.dumps({"error": "Tool returned an error"})

        content = getattr(result, "content", None) or []
        parts = []

        for block in content:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])

        return "\n\n".join(parts) if parts else json.dumps({"message": "Nenhum conteúdo retornado"})

    except Exception as e:
        return json.dumps({"error": str(e)})


def _build_history_messages(history: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """
        Inclui apenas role e content, em ordem; ignora entradas inválidas.
    """

    if not history:
        return []

    out: list[dict[str, Any]] = []

    for h in history:
        role = h.get("role")
        content = h.get("content")

        if role in ("user", "assistant") and content is not None:
            out.append({"role": role, "content": str(content)})

    return out


async def answer_with_mcp(
    user_message: str,
    mcp_session,
    *,
    history: list[dict[str, Any]] | None = None,
    model: str | None = None,
    max_tool_rounds: int = 5,
) -> str:
    """
        Envia a pergunta ao ChatGPT com as tools disponíveis; quando o modelo
        pedir tool call, chama o MCP e repassa o resultado até o modelo responder em texto.
        history: mensagens anteriores da thread (user/assistant) para follow-ups.
    """

    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *_build_history_messages(history),
        {"role": "user", "content": user_message},
    ]

    for _ in range(max_tool_rounds):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
        )
        choice = response.choices[0]
        msg = choice.message

        if not getattr(msg, "tool_calls", None):
            return (msg.content or "").strip()

        for tc in msg.tool_calls:
            name = tc.function.name

            try:
                args = json.loads(tc.function.arguments or "{}")

            except json.JSONDecodeError:
                args = {}

            content = await call_mcp_tool(mcp_session, name, args)
            messages.append({
                "role": "assistant",
                "content": msg.content or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": name, "arguments": tc.function.arguments or "{}"},
                    }
                ],
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": content,
            })

    return "Não foi possível obter uma resposta completa. Tente reformular a pergunta ou contate o suporte."
