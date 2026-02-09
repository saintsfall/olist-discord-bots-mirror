from typing import Final

# Lista dos canais permitidos (ID)
ALLOWED_CHANNEL_IDS: Final[list[int]] = [
    1451223826862968902,
    1448786609603608677,
    1448679548454441044,
    1463970153753608347
]

# Canal onde o bot recebe mensagens do webhook n8n
WEBHOOK_CHANNEL_ID: Final[int] = 1461435767636103262

# Canal de suporte para threads que precisam de atendimento humano
SUPPORT_CHANNEL_ID: Final[int] = 1463970153753608347
