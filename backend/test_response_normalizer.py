import unittest

from response_normalizer import normalize_analysis_response
from schemas import ColorAnalysisResponse


class ResponseNormalizerTest(unittest.TestCase):
    def test_normalizes_complete_contract(self):
        payload = normalize_analysis_response(
            {
                "model_version": "1.4.0",
                "confidence": 0.87,
                "photo_flags": ["low_light"],
                "detected_colors": {
                    "skin": "#f5d5c0",
                    "hair": "#4a2b0f",
                    "eyes": "#6b4226",
                    "lips": "#e87c8a",
                },
                "analysis": {
                    "season": "Verao Claro",
                    "undertone": "Frio",
                    "contrast": "Medio",
                    "depth": "Clara",
                    "metals": ["prata", "ouro branco"],
                    "explanation": "Pele clara com subtom frio.",
                },
                "recommendations": {
                    "Verao Claro": {
                        "theory": "Tons frios e suaves.",
                        "day": ["#a8d8ea"],
                        "night": ["#5b8db8"],
                    }
                },
                "makeup_tips": {
                    "lipstick": "Roses frios.",
                    "blush": "Rose.",
                    "eyeshadow": "Cinza.",
                },
                "makeup": {
                    "lipstick": ["#e8a0b4"],
                    "blush": ["#f4c2c2"],
                    "eyeshadow": ["#9b8ea8"],
                    "foundation_undertone": "frio/rosado",
                },
                "hair": {
                    "recommended_tones": ["#8b5e3c"],
                    "highlights": ["#d4b896"],
                    "notes": "Preferir acinzentados.",
                },
                "colors_to_avoid": [
                    {"hex": "#ff8c00", "reason": "Quente demais."}
                ],
            }
        )

        self.assertEqual(payload["detected_colors"]["skin"], "#F5D5C0")
        self.assertEqual(payload["makeup"]["lipstick"], ["#E8A0B4"])
        ColorAnalysisResponse.model_validate(payload)

    def test_accepts_aliases_and_normalizes_values(self):
        payload = normalize_analysis_response(
            {
                "modelVersion": "old",
                "quality": {
                    "confidence": 87,
                    "photo_flags": ["low_light", "invalid_flag"],
                },
                "detected_colors": {
                    "skin": "f5d5c0",
                    "hair": "4a2b0f",
                    "eyes": "6b4226",
                    "lips": "e87c8a",
                },
                "analysis": {
                    "season": "Verao Claro",
                    "undertone": "Frio",
                    "contrast": "Medio",
                    "profundidade": "Clara",
                    "metals": "prata, ouro branco",
                    "explanation": "Pele clara com subtom frio.",
                },
                "recommendations": {
                    "Verao Claro": {
                        "teoria": "Tons frios e suaves.",
                        "dia": ["a8d8ea"],
                        "noite": ["5b8db8"],
                    }
                },
                "makeup_tips": {
                    "batom": "Roses frios.",
                    "blush": "Rose.",
                    "sombras": "Cinza.",
                },
                "makeup": {
                    "batom": ["e8a0b4"],
                    "blush": ["f4c2c2"],
                    "sombras": ["9b8ea8"],
                    "foundationUndertone": "frio/rosado",
                },
                "hair": {
                    "recommendedTones": ["8b5e3c"],
                    "luzes": ["d4b896"],
                    "observacoes": "Preferir acinzentados.",
                },
                "colors_to_avoid": [
                    {"color": "ff8c00", "motivo": "Quente demais."},
                    {"value": "8b4513", "reason": "Terroso demais."},
                    {"hex": "ffffff"},
                ],
            },
            api_version="1.4.0",
        )

        self.assertEqual(payload["model_version"], "1.4.0")
        self.assertEqual(payload["confidence"], 0.87)
        self.assertEqual(payload["photo_flags"], ["low_light"])
        self.assertEqual(payload["analysis"]["depth"], "Clara")
        self.assertEqual(payload["analysis"]["metals"], ["prata", "ouro branco"])
        self.assertEqual(payload["recommendations"]["Verao Claro"]["day"], ["#A8D8EA"])
        self.assertEqual(payload["makeup_tips"]["lipstick"], "Roses frios.")
        self.assertEqual(payload["makeup"]["eyeshadow"], ["#9B8EA8"])
        self.assertEqual(payload["hair"]["recommended_tones"], ["#8B5E3C"])
        self.assertEqual(
            payload["colors_to_avoid"],
            [
                {"hex": "#FF8C00", "reason": "Quente demais."},
                {"hex": "#8B4513", "reason": "Terroso demais."},
            ],
        )
        ColorAnalysisResponse.model_validate(payload)

    def test_fills_missing_model_version_from_api_version(self):
        payload = normalize_analysis_response({}, api_version="2.0.0")

        self.assertEqual(payload["model_version"], "2.0.0")
        self.assertEqual(payload["confidence"], 0.0)
        self.assertEqual(payload["photo_flags"], [])

    def test_keeps_zero_confidence_and_empty_root_flags(self):
        payload = normalize_analysis_response(
            {
                "confidence": 0,
                "photo_flags": [],
                "quality": {
                    "confidence": 87,
                    "photo_flags": ["low_light"],
                },
            }
        )

        self.assertEqual(payload["confidence"], 0.0)
        self.assertEqual(payload["photo_flags"], [])


if __name__ == "__main__":
    unittest.main()
