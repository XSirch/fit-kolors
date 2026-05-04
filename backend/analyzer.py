import base64
import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

from config import API_VERSION

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ColorAnalyzer")

load_dotenv()


class AnalysisProviderError(Exception):
    pass


class ColorAnalyzer:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
        if self.google_api_key and genai:
            self.google_client = genai.Client(api_key=self.google_api_key)
        else:
            self.google_client = None
            if self.google_api_key and not genai:
                logger.warning("google-genai nao esta instalado; fallback Gemini desativado.")

        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4.1-fast")
        if self.openrouter_api_key:
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
            )
        else:
            self.openrouter_client = None

        self.prompt = f"""
        Atue como especialista senior em Colorimetria Pessoal pelo Metodo Sazonal Expandido.
        Analise a imagem com uma metodologia conservadora, consistente e baseada nas caracteristicas naturais.

        OBJETIVO
        Gerar uma analise tecnica de colorimetria em JSON, reduzindo vies causado por maquiagem, roupa, fundo, iluminacao artificial ou acessorios.

        PRIORIDADE DAS EVIDENCIAS
        1. Pele natural visivel no rosto, pescoco, colo e bracos: evidencia mais importante para subtom e profundidade.
        2. Cabelo natural aparente na raiz e massa geral: evidencia importante para profundidade e contraste.
        3. Olhos: evidencia secundaria para profundidade e contraste.
        4. Contraste real entre pele, cabelo e olhos: evidencia importante para intensidade.
        5. Batom, maquiagem, roupa branca/preta/colorida, fundo, filtros e acessorios: evidencia fraca. Use apenas como contexto visual, nunca como prova principal.

        REGRAS CONTRA VIESES COMUNS
        - Nao classifique como Inverno apenas porque ha cabelo escuro, roupa branca/preta ou batom vermelho.
        - Nao classifique como Primavera apenas porque ha batom vivo, pele iluminada ou cores saturadas no styling.
        - Nao classifique como Outono apenas porque ha joia dourada. Ouro/prata sao pistas fracas, nao decisivas.
        - Se maquiagem ou roupa entram em conflito com pele/cabelo/olhos naturais, ignore o styling e explique isso.
        - Se houver duvida entre duas estacoes, escolha a que melhor explica as caracteristicas naturais, nao a que melhor explica a roupa ou maquiagem.

        ESTACOES PERMITIDAS
        O campo analysis.season DEVE ser exatamente uma destas 12 opcoes:
        - Primavera Clara
        - Primavera Quente
        - Primavera Brilhante
        - Verao Claro
        - Verao Frio
        - Verao Suave
        - Outono Suave
        - Outono Quente
        - Outono Profundo
        - Inverno Profundo
        - Inverno Frio
        - Inverno Brilhante

        MATRIZ DE DECISAO
        Use esta matriz como regra principal:
        - Quente + claro/luminoso + baixo/medio contraste = Primavera Clara ou Primavera Quente.
        - Quente + alto brilho + cores limpas + contraste medio/alto = Primavera Brilhante.
        - Quente + escuro/profundo + medio/alto contraste = Outono Profundo.
        - Quente + medio + terroso/opaco + contraste medio = Outono Quente.
        - Quente/neutro + suave/opaco + baixo/medio contraste = Outono Suave.
        - Frio + claro + baixo/medio contraste = Verao Claro.
        - Frio + nitidamente frio + contraste medio = Verao Frio.
        - Frio/neutro + suave/acinzentado + baixo contraste = Verao Suave.
        - Frio + escuro/profundo + alto contraste = Inverno Profundo.
        - Frio + muito frio + contraste medio/alto = Inverno Frio.
        - Frio/neutro-frio + alto contraste + cores puras/nitidas = Inverno Brilhante.

        REGRAS DE COERENCIA DAS PALETAS
        - Se analysis.season for Outono, as melhores cores devem ser quentes, terrosas, ricas e levemente opacas. Evite neon, azul eletrico, magenta puro e branco optico como melhores cores.
        - Se analysis.season for Inverno, as melhores cores devem ser frias, puras, profundas ou de alto contraste. Evite pessego, mostarda, terracota e bege dourado como melhores cores.
        - Se analysis.season for Primavera, as melhores cores devem ser quentes, luminosas e limpas. Evite paletas muito escuras, pesadas ou acinzentadas.
        - Se analysis.season for Verao, as melhores cores devem ser frias, suaves, rosadas, azuladas ou acinzentadas. Evite laranja, ferrugem e cores neon.

        EXPLICACAO OBRIGATORIA
        O campo analysis.explanation deve conter, em texto corrido:
        1. quais caracteristicas naturais sustentam a estacao escolhida;
        2. quais elementos foram tratados como styling ou evidencia fraca, se existirem;
        3. qual era a alternativa mais proxima e por que ela perdeu.

        Retorne um JSON rigoroso exatamente neste formato:
        {{
          "model_version": "{API_VERSION}",
          "confidence": 0.87,
          "photo_flags": [],
          "detected_colors": {{ "skin": "#hex", "hair": "#hex", "eyes": "#hex", "lips": "#hex" }},
          "analysis": {{
            "season": "Uma das 12 estacoes permitidas",
            "undertone": "Quente, Frio ou Neutro + breve justificativa",
            "contrast": "Baixo, Medio ou Alto + breve justificativa",
            "depth": "Clara, Media ou Profunda + breve justificativa",
            "metals": ["ouro", "bronze"],
            "explanation": "Explicacao tecnica seguindo as 3 obrigacoes acima."
          }},
          "recommendations": {{
            "Primavera Brilhante": {{ "theory": "...", "day": ["#hex1", "#hex2", "#hex3"], "night": ["#hex1", "#hex2", "#hex3"] }},
            "Verao Claro": {{ "theory": "...", "day": ["#hex1", "#hex2", "#hex3"], "night": ["#hex1", "#hex2", "#hex3"] }},
            "Outono Suave": {{ "theory": "...", "day": ["#hex1", "#hex2", "#hex3"], "night": ["#hex1", "#hex2", "#hex3"] }},
            "Inverno Profundo": {{ "theory": "...", "day": ["#hex1", "#hex2", "#hex3"], "night": ["#hex1", "#hex2", "#hex3"] }}
          }},
          "makeup_tips": {{
            "lipstick": "Texto com nomes de cores e 2 a 4 exemplos em HEX, ex: #A0522D",
            "blush": "Texto com nomes de cores e 2 a 4 exemplos em HEX, ex: #D2691E",
            "eyeshadow": "Texto com nomes de cores e 3 a 5 exemplos em HEX, ex: #654321"
          }},
          "makeup": {{
            "lipstick": ["#hex1", "#hex2", "#hex3"],
            "blush": ["#hex1", "#hex2"],
            "eyeshadow": ["#hex1", "#hex2", "#hex3"],
            "foundation_undertone": "quente/dourado, frio/rosado ou neutro"
          }},
          "hair": {{
            "recommended_tones": ["#hex1", "#hex2", "#hex3"],
            "highlights": ["#hex1", "#hex2"],
            "notes": "Texto curto sobre tons indicados e tons a evitar."
          }},
          "colors_to_avoid": [
            {{ "hex": "#hex1", "reason": "Motivo especifico ligado ao subtom, contraste ou profundidade" }},
            {{ "hex": "#hex2", "reason": "Motivo especifico ligado ao subtom, contraste ou profundidade" }},
            {{ "hex": "#hex3", "reason": "Motivo especifico ligado ao subtom, contraste ou profundidade" }}
          ]
        }}

        REGRAS DE CONTRATO
        - model_version deve ser exatamente "{API_VERSION}".
        - confidence deve ser numero entre 0 e 1.
        - photo_flags deve conter apenas estes valores quando aplicaveis: "low_light", "heavy_filter", "face_not_centered", "wearing_sunglasses", "heavy_makeup", "multiple_faces", "no_face_detected".
        - detected_colors e todos os arrays de cores devem usar HEX com #.
        - analysis.metals deve ser array de strings, nao texto unico.
        - recommendations deve conter objetos com theory, day e night.
        - makeup, hair e colors_to_avoid devem sempre estar presentes com dados coerentes.

        Retorne APENAS o JSON, sem markdown, sem comentarios fora do JSON e em portugues.
        """

    async def analyze_face(self, image_data: bytes):
        errors = []

        if self.openrouter_client:
            try:
                return self._analyze_with_openrouter(image_data)
            except Exception as e:
                message = f"OpenRouter ({self.openrouter_model}): {e}"
                errors.append(message)
                logger.error(f"Falha no {message}")
                print(f"[API] Falha no {message}")
        else:
            errors.append("OpenRouter: OPENROUTER_API_KEY nao configurada.")

        if self.google_client:
            try:
                return self._analyze_with_gemini(image_data)
            except Exception as e:
                message = f"Google Gemini ({self.google_model_name}): {e}"
                errors.append(message)
                logger.warning(f"Falha no {message}")
                print(f"[API] Falha no {message}")
        else:
            errors.append("Google Gemini: GOOGLE_API_KEY nao configurada ou SDK google-genai indisponivel.")

        error_message = "Falha ao processar analise em todos os provedores: " + " | ".join(errors)
        logger.error(error_message)
        raise AnalysisProviderError(error_message)

    def _analyze_with_openrouter(self, image_data: bytes):
        logger.info(f"Tentando analise via OpenRouter ({self.openrouter_model})...")
        print(f"\n[API] Tentando analise via OpenRouter ({self.openrouter_model})...")
        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = self.openrouter_client.chat.completions.create(
            model=self.openrouter_model,
            temperature=0,
            top_p=0.1,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        logger.info("Sucesso: Analise concluida via OpenRouter.")
        print("[API] Sucesso: Analise concluida via OpenRouter.\n")
        return result

    def _analyze_with_gemini(self, image_data: bytes):
        logger.info(f"Iniciando fallback via Google Gemini ({self.google_model_name})...")
        print(f"[API] Iniciando fallback via Google Gemini ({self.google_model_name})...")

        response = self.google_client.models.generate_content(
            model=self.google_model_name,
            contents=[
                self.prompt,
                genai_types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/jpeg",
                ),
            ],
            config=genai_types.GenerateContentConfig(
                temperature=0,
                top_p=0.1,
                response_mime_type="application/json",
            ),
        )

        text = self._strip_json_fence(response.text)
        result = json.loads(text)
        logger.info("Sucesso: Analise concluida via Google Gemini.")
        print("[API] Sucesso: Analise concluida via Google Gemini.\n")
        return result

    def _strip_json_fence(self, text: str):
        text = text.strip()
        if "```json" in text:
            return text.split("```json", 1)[1].split("```", 1)[0].strip()
        if text.startswith("```"):
            return text.split("```", 1)[1].split("```", 1)[0].strip()
        return text
