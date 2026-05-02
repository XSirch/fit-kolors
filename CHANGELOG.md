# Changelog - Fit-Kolors

Todas as mudancas notaveis do projeto serao documentadas neste arquivo.

## [1.3.0] - 2026-05-02

### Adicionado

- Configuracao `ALLOWED_ORIGINS` para restringir origens CORS permitidas.
- Autenticacao por API key via header `X-API-Key` nos endpoints de analise.
- Fila Redis/RQ para processar analises assíncronas fora do processo da API.
- Worker dedicado em `backend/worker.py`.
- Modulo `backend/jobs.py` para enfileiramento, processamento e entrega de webhooks.
- Endpoint `GET /analysis/jobs/{job_id}` para consultar metadados do job.
- Servicos `redis` e `worker` no `docker-compose.yml`.
- Variaveis `REDIS_URL` e `ANALYSIS_QUEUE`.

### Alterado

- `POST /analyze/webhook` agora enfileira jobs em Redis/RQ em vez de usar `BackgroundTasks` do FastAPI.
- Se a fila estiver indisponivel, a API retorna `503`.

## [1.2.0] - 2026-05-02

### Adicionado

- Endpoint `POST /analyze/webhook` para analises assíncronas com notificacao por webhook.
- Evento `analysis.completed` com resultado completo e evento `analysis.failed` com erro.
- Header opcional `X-Fit-Kolors-Webhook-Secret` para consumidores validarem a origem do webhook.
- Dependencia explicita `httpx` para entrega dos webhooks.

### Alterado

- Removido fallback com dados mockados quando todos os provedores de IA falham.
- `/analyze` agora retorna `502` com o motivo quando todos os provedores falham.
- Webhooks de analise agora notificam falhas reais via `analysis.failed` com mensagem em `error`.

## [1.1.1] - 2026-05-02

### Migrado

- Fallback Gemini atualizado do pacote encerrado `google-generativeai` para o SDK atual `google-genai`.

## [1.1.0] - 2026-05-02

### Adicionado

- Script `backend/test_openrouter_models.py` para comparar varios modelos OpenRouter com a mesma imagem.
- Geracao de relatorios locais em JSON e HTML para os testes comparativos.
- Renderizacao de swatches no frontend para exemplos HEX presentes em dicas de maquiagem.
- Ignorado `backend/openrouter_test_results/` no Git.

### Alterado

- Modelo principal do backend alterado para OpenRouter com `x-ai/grok-4.1-fast`.
- Google Gemini `gemini-2.5-flash` passou a ser fallback.
- Prompt de colorimetria reescrito com regras mais deterministicas, matriz de decisao e lista fechada de 12 estacoes.
- Chamadas de IA configuradas com menor aleatoriedade (`temperature=0`, `top_p=0.1`).
- `.env.example` atualizado com modelos atuais.
- Documentacao atualizada para refletir o fluxo Grok principal + Gemini fallback.

### Corrigido

- Evita falha de import quando `google-generativeai` nao esta instalado, mantendo OpenRouter funcional.
- Melhora a compatibilidade do frontend com respostas do Grok que incluem exemplos de cores em texto.

## [1.0.0] - 2026-04-30

### Adicionado

- Backend FastAPI com respostas estruturadas via Pydantic.
- Analise de colorimetria pessoal pelo Metodo Sazonal Expandido.
- Recomendacoes de metais, maquiagem e paletas sazonais.
- Documentacao automatica via Swagger em `/docs`.
- Frontend React com interface responsiva.

### Melhorado

- Prompt inicial para coerencia entre diagnostico textual e codigos HEX.
- Configuracao de modelos via `.env`.

---

Este projeto segue versionamento semantico.
