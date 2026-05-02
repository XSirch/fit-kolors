# Fit-Kolors

O **Fit-Kolors** e uma plataforma de analise de colorimetria pessoal pelo Metodo Sazonal Expandido. O app envia uma foto para o backend, recebe um diagnostico estruturado por IA e exibe a estacao, cores detectadas, paletas sazonais, metais e dicas de maquiagem.

## Funcionalidades

- **Analise facial por IA**: deteccao de cores de pele, cabelo, olhos e labios.
- **Diagnostico sazonal**: classificacao em uma das 12 estacoes permitidas.
- **Prompt deterministico**: prioriza pele, cabelo natural, olhos e contraste real; trata maquiagem, roupa, fundo e acessorios como evidencias fracas.
- **Modelo principal via OpenRouter**: `x-ai/grok-4.1-fast` e usado como modelo principal.
- **Fallback Gemini**: `gemini-2.5-flash` fica como redundancia quando o OpenRouter falha ou nao esta configurado.
- **Dicas de maquiagem com swatches**: exemplos em HEX nas dicas de batom, blush e sombra sao renderizados visualmente no frontend.
- **Teste comparativo de modelos**: script local para comparar varios modelos OpenRouter com a mesma imagem e gerar JSON + HTML.

## Tecnologias

### Backend

- FastAPI
- Pydantic
- OpenAI SDK para OpenRouter
- Google Generative AI SDK para fallback Gemini
- python-dotenv

### Frontend

- React + Vite
- Lucide React
- CSS customizado

## Estrutura

```text
Fit-Kolors/
├── backend/
│   ├── analyzer.py                 # Integracao IA, prompt e fallback
│   ├── main.py                     # API FastAPI
│   ├── test_openrouter_models.py   # Comparativo local de modelos OpenRouter
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
```

Inicie a API:

```bash
python main.py
```

Swagger: `http://localhost:8000/docs`

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
- Response: JSON com:
  - `detected_colors`
  - `analysis`
  - `recommendations`
  - `makeup_tips`

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

Versao atual: **1.1.0**

Este projeto segue versionamento semantico.
