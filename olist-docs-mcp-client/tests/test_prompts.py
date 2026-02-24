"""
    Testes de regressão do prompt do orquestrador.
    Garante que as instruções anti-omissão de código permaneçam no SYSTEM_PROMPT.
"""
import pytest

from orchestrator.prompts import SYSTEM_PROMPT


# Frases que devem estar no prompt para evitar que o LLM omita código com placeholders
REQUIRED_ANTI_OMISSION_PHRASES = [
    "NUNCA substitua partes do código por comentários descritivos",
    "placeholders ou reticências",
    "// Código para manipular",
    "// ...",
    "código omitido",
    "bloco INTEIRO na resposta",
    "sem omitir trechos",
    "Não resuma código com comentários ou",
    "código completo na resposta",
    "código literal inteiro",
]


def test_prompt_forbids_code_placeholder_comments():
    """O prompt deve proibir substituir código por comentários ou '...'."""
    for phrase in REQUIRED_ANTI_OMISSION_PHRASES:
        assert phrase in SYSTEM_PROMPT, (
            f"SYSTEM_PROMPT deve conter a instrução anti-omissão: {phrase!r}"
        )


def test_prompt_requires_full_code_when_doc_has_it():
    """O prompt deve exigir código completo quando a doc trouxer o bloco."""
    assert "código completo" in SYSTEM_PROMPT or "código literal inteiro" in SYSTEM_PROMPT
    assert "anexo" in SYSTEM_PROMPT or "sistema enviará" in SYSTEM_PROMPT.lower()
