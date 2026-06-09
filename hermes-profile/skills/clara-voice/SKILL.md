name: clara-voice
description: Skill inicial da CLARA dentro do Hermes (voz, memória, perfil). Não é para produção ainda.
---

## clara-voice

Etapas iniciais para integrar voz e memória da CLARA no Hermes.

### Passo 1 — Criar profile

```bash
hermes profiles create companheiro
cp assistente-clara/hermes-profile/.env.example \
   ~/.hermes/profiles/companheiro/.env
# editar OPENAI_BASE_URL / OPENAI_API_KEY conforme ambiente
```

### Passo 2 — Ação sugerida

1. Atualizar `clara/SOUL.md` como prompt base do profile.
2. Habilitar busca web, clima e notícias na config do Hermes.
3. Quando `main.py` ganhar endpoints HTTP, ligar face.py como
   app sidecar.
