# Fit-Kolors

O **Fit-Kolors** e uma plataforma de analise de colorimetria pessoal pelo Metodo Sazonal Expandido. O app envia uma foto para o backend, recebe um diagnostico estruturado por IA e exibe a estacao, cores detectadas, paletas sazonais, metais e dicas de maquiagem.

## Funcionalidades

- **Analise facial por IA**: deteccao de cores de pele, cabelo, olhos e labios.
- **Diagnostico sazonal**: classificacao em uma das 12 estacoes permitidas.
- **Prompt deterministico**: prioriza pele, cabelo natural, olhos e contraste real; trata maquiagem, roupa, fundo e acessorios como evidencias fracas.
- **Modelo principal via OpenRouter**: `x-ai/grok-4.1-fast` e usado como modelo principal.
- **Fallback Gemini**: `gemini-2.5-flash` fica como redundancia quando o OpenRouter falha ou nao esta configurado.
- **Dicas de maquiagem com swatches**: exemplos em HEX nas dicas de batom, blush e sombra sao renderizados visualmente no frontend.
- **Webhook para analises assíncronas**: clientes da API podem receber um evento quando a analise terminar, sem polling.
- **Fila com workers**: analises assíncronas sao enfileiradas no Redis e processadas por workers RQ separados da API.
- **Teste comparativo de modelos**: script local para comparar varios modelos OpenRouter com a mesma imagem e gerar JSON + HTML.

## Tecnologias

### Backend

- FastAPI
- Pydantic
- OpenAI SDK para OpenRouter
- Google Gen AI SDK (`google-genai`) para fallback Gemini
- python-dotenv
- Redis + RQ para fila de analises assíncronas
- httpx para entrega dos webhooks

### Frontend

- React + Vite
- Lucide React
- CSS customizado

## Estrutura

```text
Fit-Kolors/
├── backend/
│   ├── analyzer.py                 # Integracao IA, prompt e fallback
│   ├── jobs.py                     # Fila RQ, processamento e entrega de webhook
│   ├── main.py                     # API FastAPI
│   ├── test_openrouter_models.py   # Comparativo local de modelos OpenRouter
│   ├── worker.py                   # Worker RQ
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
├── CHANGELOG.md
└── README.md
```

## Instalacao

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Crie `backend/.env`:

```env
GOOGLE_API_KEY=sua_chave_gemini
GOOGLE_MODEL=gemini-2.5-flash
OPENROUTER_API_KEY=sua_chave_openrouter
OPENROUTER_MODEL=x-ai/grok-4.1-fast
OPENROUTER_TEST_MODELS=x-ai/grok-4.1-fast,google/gemini-2.5-flash
REDIS_URL=redis://localhost:6379/0
ANALYSIS_QUEUE=analysis
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://seu-site.com
API_KEYS=dev-api-key-change-me
```

`ALLOWED_ORIGINS` define quais origens de browser podem chamar a API via CORS. Em producao, remova os hosts locais e deixe apenas o dominio do seu site, por exemplo:

```env
ALLOWED_ORIGINS=https://fit-kolors.com,https://www.fit-kolors.com
```

`API_KEYS` define as chaves aceitas para endpoints protegidos. Separe multiplas chaves por virgula. Em producao, use um valor longo e aleatorio e nao exponha essa chave no frontend publico.

Todas as rotas de analise exigem o header:

```http
X-API-Key: dev-api-key-change-me
```

Observacao: CORS protege chamadas feitas por navegadores. A API key protege chamadas server-to-server, curl e Postman.

Inicie a API:

```bash
python main.py
```

Swagger: `http://localhost:8000/docs`

Para usar o endpoint assíncrono com webhook, inicie tambem Redis e o worker:

```bash
redis-server
python worker.py
```

Com Docker Compose, os servicos `redis`, `backend`, `worker` e `frontend` sobem juntos:

```bash
docker compose up --build
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

## API

### `POST /analyze`

Envia uma imagem para analise de colorimetria.

- Body: `multipart/form-data` com campo `file`
- Header obrigatorio: `X-API-Key`
- Response: JSON com:
  - `detected_colors`
  - `analysis`
  - `recommendations`
  - `makeup_tips`
- Em falha de todos os provedores de IA, retorna `502` com o motivo no campo `detail`. A API nao retorna dados mockados.

### `POST /analyze/webhook`

Agenda uma analise na fila Redis/RQ e retorna imediatamente.

- Body: `multipart/form-data`
  - `file`: imagem
  - `webhook_url`: URL HTTP/HTTPS que recebera o evento
  - `webhook_secret`: opcional; enviado no header `X-Fit-Kolors-Webhook-Secret`
- Header obrigatorio: `X-API-Key`
- Response imediata `202 Accepted`:

```json
{
  "job_id": "uuid",
  "status": "accepted",
  "webhook_url": "https://example.com/webhook"
}
```

Quando terminar, o backend envia `POST` para `webhook_url`:

```json
{
  "event": "analysis.completed",
  "job_id": "uuid",
  "status": "completed",
  "created_at": "2026-05-02T12:00:00+00:00",
  "completed_at": "2026-05-02T12:00:30+00:00",
  "result": {
    "detected_colors": {},
    "analysis": {},
    "recommendations": {},
    "makeup_tips": {}
  },
  "error": null
}
```

Em caso de falha, `event` sera `analysis.failed`, `status` sera `failed`, `result` sera `null` e `error` tera a mensagem. A API nao envia dados mockados.

### `GET /analysis/jobs/{job_id}`

Consulta metadados do job, caso o cliente queira diagnosticar fila ou falhas.

Header obrigatorio: `X-API-Key`

```json
{
  "job_id": "uuid",
  "status": "queued",
  "queue": "analysis",
  "created_at": "...",
  "enqueued_at": "...",
  "started_at": null,
  "ended_at": null
}
```

## Teste comparativo de modelos

O script abaixo testa varios modelos OpenRouter com a mesma imagem:

```bash
cd backend
python test_openrouter_models.py test.png
```

Ele le `OPENROUTER_TEST_MODELS` do `.env`, executa as chamadas em paralelo e salva:

```text
backend/openrouter_test_results/result_YYYYMMDD_HHMMSS.json
backend/openrouter_test_results/result_YYYYMMDD_HHMMSS.html
```

Use o HTML para comparar visualmente as respostas dos modelos.

## Versionamento

Versao atual: **1.3.0**

Este projeto segue versionamento semantico.
