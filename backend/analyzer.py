import google.generativeai as genai
from openai import OpenAI
import json
import os
import base64
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ColorAnalyzer")

load_dotenv()

class ColorAnalyzer:
    def __init__(self):
        # Google Setup
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            self.google_model = genai.GenerativeModel(self.google_model_name)
        
        # OpenRouter Setup
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-001")
        if self.openrouter_api_key:
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
            )
        else:
            self.openrouter_client = None

        self.prompt = """
        Atue como um especialista sênior em Colorimetria Pessoal (Método Sazonal Expandido).
        Sua tarefa é analisar a imagem do usuário e fornecer um dossiê técnico IMPECÁVEL e COERENTE.

        REGRAS CRÍTICAS DE COERÊNCIA:
        1. Se a análise diz que a pessoa é 'Suave', os HEX codes DEVEM ser tons opacos, acinzentados ou pastéis. NUNCA use cores neon ou puras.
        2. Se a análise diz que a pessoa é 'Brilhante/Viva', os HEX codes DEVEM ser saturados e nítidos.
        3. Se a estação é 'Inverno', use cores frias, profundas ou puras.
        4. Se a estação é 'Outono', use tons terrosos, quentes e levemente opacos.
        5. As recomendações para a estação detectada como 'vencedora' devem ser as mais precisas e detalhadas possíveis.

        ESTRUTURA DE ANÁLISE:
        - Subtom: (Frio, Quente, Neutro)
        - Profundidade: (Claro, Escuro, Médio)
        - Intensidade: (Suave, Brilhante)
        - Contraste: (Baixo, Médio, Alto)

        Retorne um JSON rigoroso:
        {
          "detected_colors": { "skin": "#hex", "hair": "#hex", "eyes": "#hex", "lips": "#hex" },
          "analysis": {
            "season": "Nome Completo da Estação em Português",
            "undertone": "Descrição do subtom",
            "contrast": "Nível de contraste",
            "metals": "Ouro, Prata, etc.",
            "explanation": "Explicação técnica da harmonia. DEVE ser coerente com as cores sugeridas abaixo."
          },
          "recommendations": {
            "spring": { "theory": "...", "day": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"], "night": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"] },
            "summer": { "theory": "...", "day": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"], "night": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"] },
            "autumn": { "theory": "...", "day": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"], "night": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"] },
            "winter": { "theory": "...", "day": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"], "night": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"] }
          },
          "makeup_tips": { "lipstick": "...", "blush": "...", "eyeshadow": "..." }
        }

        VERIFICAÇÃO FINAL: Antes de gerar o JSON, verifique se os códigos HEX que você escolheu realmente transmitem a 'vibe' da estação descrita. Coerência é a prioridade número 1.
        Retorne APENAS o JSON e em português.
        """

    async def analyze_face(self, image_data: bytes):
        # 1. Try Google Gemini (Default)
        if self.google_api_key:
            try:
                logger.info("Tentando análise com Google Gemini API...")
                print("\n[API] Tentando análise com Google Gemini API...")
                response = self.google_model.generate_content([
                    self.prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ])
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                
                result = json.loads(text)
                logger.info("Sucesso: Análise concluída via Google Gemini.")
                print("[API] Sucesso: Análise concluída via Google Gemini.\n")
                return result
            except Exception as e:
                logger.warning(f"Falha no Google Gemini: {e}")
                print(f"[API] Falha no Google Gemini: {e}")

        # 2. Try OpenRouter (Fallback)
        if self.openrouter_client:
            try:
                logger.info(f"Iniciando Fallback via OpenRouter ({self.openrouter_model})...")
                print(f"[API] Iniciando Fallback via OpenRouter ({self.openrouter_model})...")
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                response = self.openrouter_client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.prompt},
                                {
                                    "type": "image_url",
                                    "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                logger.info("Sucesso: Análise concluída via OpenRouter.")
                print("[API] Sucesso: Análise concluída via OpenRouter.\n")
                return result
            except Exception as e:
                logger.error(f"Falha no OpenRouter: {e}")
                print(f"[API] Falha no OpenRouter: {e}")

        # 3. Final Fallback (Mock)
        logger.warning("Nenhuma API disponível ou funcional. Retornando dados de demonstração.")
        print("[API] AVISO: Nenhuma API disponível ou funcional. Retornando MOCK DATA.")
        return self._get_mock_data()

    def _get_mock_data(self):
        return {
          "detected_colors": {
            "skin": "#f3cfb3",
            "hair": "#4a3728",
            "eyes": "#5b4e3e",
            "lips": "#d68b8b"
          },
          "analysis": {
            "season": "Outono Escuro (Exemplo)",
            "undertone": "Quente e Profundo",
            "contrast": "Médio-Alto",
            "metals": "Ouro e Cobre",
            "explanation": "Subtom quente com cores ricas e terrosas. O alto contraste entre cabelo e pele sugere um perfil de Outono. (DADOS DE TESTE)"
          },
          "recommendations": {
            "spring": { 
                "theory": "Cores vivas que iluminam o rosto",
                "day": ["#FFD700", "#FF8C00", "#FFA500", "#FF7F50", "#FF6347"], 
                "night": ["#E9967A", "#FF4500", "#CD5C5C", "#8B0000", "#B22222"] 
            },
            "summer": { 
                "theory": "Tons pastéis e suaves",
                "day": ["#87CEEB", "#D8BFD8", "#B0C4DE", "#E0FFFF", "#F0FFFF"], 
                "night": ["#4682B4", "#9370DB", "#7B68EE", "#6A5ACD", "#483D8B"] 
            },
            "autumn": { 
                "theory": "Harmonia total com tons terrosos",
                "day": ["#8B4513", "#DAA520", "#B8860B", "#CD853F", "#D2691E"], 
                "night": ["#556B2F", "#A0522D", "#800000", "#5D4037", "#3E2723"] 
            },
            "winter": { 
                "theory": "Cores puras e intensas",
                "day": ["#F0F8FF", "#B0C4DE", "#87CEFA", "#00BFFF", "#1E90FF"], 
                "night": ["#191970", "#4B0082", "#8B008B", "#000080", "#000000"] 
            }
          },
          "makeup_tips": {
            "lipstick": "Terracota, Nude Quente",
            "blush": "Pêssego Profundo",
            "eyeshadow": "Marrom Café, Bronze"
          }
        }
