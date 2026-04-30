# 📜 Changelog - Fit-Kolors

Todas as mudanças notáveis no projeto **Fit-Kolors** serão documentadas neste arquivo.

## [1.0.0] - 2026-04-30

### ✨ Adicionado
- **Conversão para API RESTful**: Refatoração completa do backend utilizando FastAPI e Pydantic para respostas estruturadas.
- **Dossiê de Colorimetria Profissional**: Implementação do "Estudo Aprofundado" com o método das 12 estações.
- **Recomendação de Metais e Maquiagem**: Novos campos na análise para orientar o uso de acessórios e cosméticos.
- **Teoria Sazonal**: Descrições explicativas de como o usuário se adapta a cada paleta de cores.
- **Documentação Automática**: Integração com Swagger UI em `/docs`.

### 🚀 Melhorias
- **Prompt Engineering**: Refinamento das instruções da IA para garantir coerência entre o diagnóstico textual e os códigos HEX sugeridos.
- **Sistema Híbrido de IA**: Estabilização do fallback automático entre Google Gemini (padrão) e OpenRouter (redundância).
- **Interface Glassmorphism**: Polimento visual no frontend para exibir o novo relatório de análise de forma limpa e moderna.
- **Configuração via .env**: Todos os modelos de IA agora são parametrizáveis.

### 🛡️ Corrigido
- **Erro de Porta 8000**: Resolução de conflitos de processos órfãos que impediam o reinício do servidor.
- **Coerência Cromática**: Correção de bugs onde a IA sugeria cores vibrantes para perfis de intensidade "Suave".
- **Tratamento de Quota (429)**: Melhoria na captura de erros de limite de requisições da API do Google.

---
*Este projeto segue o versionamento semântico.*
