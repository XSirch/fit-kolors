# 🎨 Fit-Kolors

O **Fit-Kolors** é uma plataforma avançada de análise de colorimetria pessoal (Método Sazonal Expandido) que utiliza Inteligência Artificial para identificar as paletas de cores que melhor harmonizam com o tom de pele, cabelo e olhos do usuário.

---

## 🚀 Funcionalidades

- **Análise Facial por IA**: Detecção automática de cores de pele, cabelo, olhos e lábios.
- **Diagnóstico de Estação**: Classificação em uma das 12 estações sazonais (ex: Inverno Escuro, Outono Suave).
- **Estudo Aprofundado**:
    - Recomendações de metais (Ouro, Prata, etc.).
    - Dicas de maquiagem (Batom, Blush, Sombras).
    - Paletas personalizadas para Dia e Noite para todas as estações.
- **API RESTful**: Backend robusto com documentação automática via Swagger.
- **Sistema Híbrido de IA**: Suporte nativo a Google Gemini 2.0 Flash com fallback automático para OpenRouter.
- **Interface Premium**: Design em *Glassmorphism* moderno, responsivo e interativo.

---

## 🛠️ Tecnologias

### Backend
- **FastAPI**: Framework web de alta performance.
- **Pydantic**: Validação de dados e estruturação de resposta.
- **Google Generative AI SDK**: Integração com Gemini 2.0 Flash.
- **OpenAI SDK**: Utilizado para o fallback via OpenRouter.

### Frontend
- **React + Vite**: Framework moderno para UI.
- **Lucide-React**: Conjunto de ícones minimalistas.
- **Vanilla CSS**: Estilização premium personalizada.

---

## 📦 Estrutura do Projeto

```text
color-face/
├── backend/            # API FastAPI
│   ├── analyzer.py     # Lógica central da IA e Prompts
│   ├── main.py         # Endpoints e Servidor
│   ├── .env            # Configurações sensíveis (API Keys)
│   └── requirements.txt
├── frontend/           # App React
│   ├── src/
│   │   ├── App.jsx     # Componente principal e UI
│   │   └── index.css   # Estilos globais (Glassmorphism)
│   └── package.json
└── README.md
```

---

## 🔧 Instalação e Execução

### 1. Requisitos
- Python 3.9+
- Node.js 18+
- Chave de API do Google Gemini ou OpenRouter.

### 2. Configuração do Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
Crie um arquivo `.env` na pasta `backend/`:
```env
GOOGLE_API_KEY=sua_chave_aqui
GOOGLE_MODEL=gemini-2.0-flash
OPENROUTER_API_KEY=sua_chave_aqui
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```
Inicie o servidor:
```bash
python main.py
```
Acesse a documentação em: `http://localhost:8000/docs`

### 3. Configuração do Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 Documentação da API

### `POST /analyze`
Envia uma imagem para análise técnica.
- **Body**: `multipart/form-data` contendo o campo `file` (imagem).
- **Response**: JSON estruturado com `detected_colors`, `analysis`, `recommendations` e `makeup_tips`.

---

## 📄 Licença
Este projeto é para fins de demonstração de capacidades técnicas em IA e desenvolvimento Full-stack.
