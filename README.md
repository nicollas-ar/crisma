# Defensores da Esperança — Advento

Jogo de catequese em Flask, Canvas e PostgreSQL (Neon). A cada onda, uma pergunta sobre o Advento; erro encerra a partida. Ranking persistente no Neon.

## Render
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Health check: `/saude`
- Environment: `DATABASE_URL` (Neon PostgreSQL), `SECRET_KEY` (valor secreto aleatório)

As tabelas são criadas automaticamente na inicialização. Não envie credenciais ao repositório.
