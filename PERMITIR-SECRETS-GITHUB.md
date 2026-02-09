# Permitir Secrets Temporariamente no GitHub

O GitHub está bloqueando porque detectou tokens no commit antigo `3ad85ae`. Você pode permitir temporariamente esses secrets para que o push funcione:

## Links para Permitir os Secrets:

1. **Token do Jurandir Bot:**
   https://github.com/saintsfall/olist-discord-bots-mirror/security/secret-scanning/unblock-secret/39Rp1syxJisPMPNsDcEa6DIj9cD

2. **Token do Sebastião Bot:**
   https://github.com/saintsfall/olist-discord-bots-mirror/security/secret-scanning/unblock-secret/39Rp1uqJAlan6dLdm8quHsyu0aH

## Passos:

1. Acesse cada um dos links acima
2. Clique em "Allow secret" ou "Permitir secret"
3. O GitLab poderá fazer o mirror
4. **IMPORTANTE**: Depois que o mirror funcionar, você deve:
   - Revogar os tokens antigos no Discord Developer Portal
   - Criar novos tokens
   - Atualizar os arquivos `.env` com os novos tokens

## Alternativa: Reescrever Histórico Completamente

Se preferir não permitir os secrets, podemos criar um histórico completamente novo sem o commit problemático.
