# Changelog - Fit-Kolors

Todas as mudancas notaveis do projeto serao documentadas neste arquivo.

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
