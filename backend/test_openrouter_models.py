import argparse
import asyncio
import ast
import base64
import html
import json
import mimetypes
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ANALYZER_PATH = Path(__file__).resolve().parent / "analyzer.py"
RESULTS_DIR = Path(__file__).resolve().parent / "openrouter_test_results"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Testa varios modelos da OpenRouter com a mesma imagem."
    )
    parser.add_argument(
        "image",
        help="Caminho da imagem que sera enviada para todos os modelos.",
    )
    return parser.parse_args()


def get_models():
    configured_models = os.getenv("OPENROUTER_TEST_MODELS", "").strip()
    if configured_models:
        return [
            model.strip()
            for model in configured_models.split(",")
            if model.strip()
        ]

    fallback_model = os.getenv("OPENROUTER_MODEL", "").strip()
    if fallback_model:
        return [fallback_model]

    return []


def strip_json_fence(content):
    text = (content or "").strip()
    if text.startswith("```json"):
        return text.split("```json", 1)[1].split("```", 1)[0].strip()
    if text.startswith("```"):
        return text.split("```", 1)[1].split("```", 1)[0].strip()
    return text


def parse_model_json(content):
    try:
        return json.loads(strip_json_fence(content))
    except json.JSONDecodeError:
        return None


def make_image_url(image_data, image_path):
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded_image = base64.b64encode(image_data).decode("utf-8")
    return f"data:{mime_type};base64,{encoded_image}"


def esc(value):
    return html.escape(str(value or "-"))


def load_analyzer_prompt():
    tree = ast.parse(ANALYZER_PATH.read_text(encoding="utf-8"))
    prompt = None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            is_prompt_assignment = (
                isinstance(target, ast.Attribute)
                and target.attr == "prompt"
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            )
            if is_prompt_assignment and isinstance(node.value, ast.Constant):
                prompt = node.value.value

    if prompt:
        return prompt

    raise RuntimeError(f"Nao foi possivel encontrar self.prompt em {ANALYZER_PATH}")


def call_model(api_key, model, prompt, image_url):
    started_at = time.perf_counter()

    try:
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            top_p=0.1,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
            extra_body={
                "reasoning": {
                    "enabled": True,
                    "effort": "medium",
                    "exclude": True
                }
            },
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        parsed_json = parse_model_json(raw_content)

        return {
            "model": model,
            "ok": True,
            "duration_seconds": round(time.perf_counter() - started_at, 3),
            "raw_content": raw_content,
            "parsed_json": parsed_json,
            "error": None,
        }
    except Exception as exc:
        return {
            "model": model,
            "ok": False,
            "duration_seconds": round(time.perf_counter() - started_at, 3),
            "raw_content": None,
            "parsed_json": None,
            "error": str(exc),
        }


async def run_models(api_key, models, prompt, image_url):
    tasks = [
        asyncio.to_thread(call_model, api_key, model, prompt, image_url)
        for model in models
    ]
    return await asyncio.gather(*tasks)


def extract_analysis(result):
    parsed_json = result.get("parsed_json") or {}
    analysis = parsed_json.get("analysis") or {}
    return {
        "season": analysis.get("season") or "-",
        "undertone": analysis.get("undertone") or "-",
        "contrast": analysis.get("contrast") or "-",
    }


def print_summary(results):
    print("\nResumo dos modelos testados:")
    print("-" * 100)
    print(f"{'Modelo':40} {'Status':8} {'Tempo':>8}  Estacao | Subtom | Contraste")
    print("-" * 100)

    for result in results:
        status = "OK" if result["ok"] else "ERRO"
        duration = f"{result['duration_seconds']:.3f}s"

        if result["ok"]:
            analysis = extract_analysis(result)
            details = (
                f"{analysis['season']} | "
                f"{analysis['undertone']} | "
                f"{analysis['contrast']}"
            )
        else:
            details = result["error"]

        print(f"{result['model'][:40]:40} {status:8} {duration:>8}  {details}")

    print("-" * 100)


def save_results(results, image_path):
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"result_{timestamp}.json"

    payload = {
        "image": str(image_path),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "results": results,
    }

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def render_color_dot(color, label=""):
    if not color:
        return ""

    safe_color = esc(color)
    safe_label = esc(label or color)
    return f"""
      <div class="color-item">
        <div class="color-dot" style="background:{safe_color}"></div>
        <span>{safe_label}</span>
      </div>
    """


def render_detected_colors(parsed_json):
    detected = parsed_json.get("detected_colors") or {}
    if not detected:
        return '<p class="muted">Cores detectadas indisponiveis.</p>'

    labels = {
        "skin": "Pele",
        "hair": "Cabelo",
        "eyes": "Olhos",
        "lips": "Labios",
    }
    dots = [
        render_color_dot(color, f"{labels.get(key, key)} {color}")
        for key, color in detected.items()
    ]
    return f'<div class="color-row">{"".join(dots)}</div>'


def render_palette(title, colors):
    if not colors:
        return ""

    dots = "".join(render_color_dot(color) for color in colors)
    return f"""
      <div class="palette-block">
        <h4>{esc(title)}</h4>
        <div class="color-row compact">{dots}</div>
      </div>
    """


def render_recommendations(parsed_json):
    recommendations = parsed_json.get("recommendations") or {}
    if not recommendations:
        return '<p class="muted">Paletas indisponiveis.</p>'

    cards = []
    for season, data in recommendations.items():
        data = data or {}
        cards.append(
            f"""
            <section class="season-card">
              <h3>{esc(season).title()}</h3>
              <p class="muted">{esc(data.get("theory"))}</p>
              {render_palette("Dia", data.get("day"))}
              {render_palette("Noite", data.get("night"))}
            </section>
            """
        )

    return f'<div class="season-grid">{"".join(cards)}</div>'


def render_makeup(parsed_json):
    makeup = parsed_json.get("makeup_tips") or {}
    if not makeup:
        return '<p class="muted">Dicas indisponiveis.</p>'

    return f"""
      <div class="tip-grid">
        <div><strong>Batom</strong><span>{esc(makeup.get("lipstick"))}</span></div>
        <div><strong>Blush</strong><span>{esc(makeup.get("blush"))}</span></div>
        <div><strong>Sombras</strong><span>{esc(makeup.get("eyeshadow"))}</span></div>
      </div>
    """


def render_result_card(result):
    status_class = "ok" if result.get("ok") else "error"
    status_label = "Sucesso" if result.get("ok") else "Erro"
    parsed_json = result.get("parsed_json") or {}
    analysis = parsed_json.get("analysis") or {}

    if not result.get("ok"):
        return f"""
          <article class="model-card error-card">
            <div class="model-header">
              <div>
                <span class="eyebrow">OpenRouter</span>
                <h2>{esc(result.get("model"))}</h2>
              </div>
              <span class="status {status_class}">{status_label}</span>
            </div>
            <div class="meta-row">
              <span>{esc(result.get("duration_seconds"))}s</span>
            </div>
            <pre>{esc(result.get("error"))}</pre>
          </article>
        """

    raw_json = json.dumps(parsed_json, ensure_ascii=False, indent=2)
    return f"""
      <article class="model-card">
        <div class="model-header">
          <div>
            <span class="eyebrow">OpenRouter</span>
            <h2>{esc(result.get("model"))}</h2>
          </div>
          <span class="status {status_class}">{status_label}</span>
        </div>

        <div class="meta-row">
          <span>{esc(result.get("duration_seconds"))}s</span>
          <span>{esc(analysis.get("undertone"))}</span>
          <span>{esc(analysis.get("contrast"))}</span>
        </div>

        <section class="hero-result">
          <h3>Sua Estacao: {esc(analysis.get("season"))}</h3>
          <p>{esc(analysis.get("explanation"))}</p>
          <div class="chip-row">
            <span>{esc(analysis.get("undertone"))}</span>
            <span>{esc(analysis.get("contrast"))} Contraste</span>
            <span>Metais: {esc(analysis.get("metals"))}</span>
          </div>
        </section>

        <section>
          <h3>Cores Detectadas</h3>
          {render_detected_colors(parsed_json)}
        </section>

        <section>
          <h3>Dicas de Beleza</h3>
          {render_makeup(parsed_json)}
        </section>

        <section>
          <h3>Estudo de Harmonizacao Cromatica</h3>
          {render_recommendations(parsed_json)}
        </section>

        <details>
          <summary>JSON bruto</summary>
          <pre>{esc(raw_json or result.get("raw_content"))}</pre>
        </details>
      </article>
    """


def save_html_results(results, image_path, image_url):
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"result_{timestamp}.html"
    cards = "".join(render_result_card(result) for result in results)

    content = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fit-Kolors - Comparativo OpenRouter</title>
  <style>
    :root {{
      --primary: #c48eff;
      --secondary: #ff8ec4;
      --bg: #0a0a0c;
      --panel: rgba(255,255,255,0.06);
      --panel-strong: rgba(255,255,255,0.1);
      --border: rgba(255,255,255,0.13);
      --text: #ffffff;
      --muted: #a1a1aa;
      --ok: #74d99f;
      --error: #ff7a90;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top right, rgba(196,142,255,0.18), transparent 38%),
        radial-gradient(circle at bottom left, rgba(255,142,196,0.14), transparent 42%),
        var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .page {{
      width: min(1440px, 100%);
      margin: 0 auto;
      padding: 32px;
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 220px;
      align-items: center;
      gap: 24px;
      margin-bottom: 28px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 1;
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    h2, h3, h4, p {{ margin-top: 0; }}
    .subtitle, .muted {{ color: var(--muted); }}
    .source-image {{
      width: 220px;
      aspect-ratio: 1;
      object-fit: cover;
      border-radius: 20px;
      border: 1px solid var(--border);
      box-shadow: 0 18px 45px rgba(0,0,0,0.35);
    }}
    .comparison-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 24px;
      align-items: start;
    }}
    .model-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.28);
    }}
    .model-card section {{ margin-top: 24px; }}
    .model-header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 16px;
    }}
    .model-header h2 {{
      font-size: 1.2rem;
      line-height: 1.25;
      overflow-wrap: anywhere;
      margin-bottom: 0;
    }}
    .eyebrow {{
      display: block;
      color: var(--primary);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }}
    .status {{
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 0.78rem;
      font-weight: 700;
      white-space: nowrap;
    }}
    .status.ok {{ background: rgba(116,217,159,0.16); color: var(--ok); }}
    .status.error {{ background: rgba(255,122,144,0.16); color: var(--error); }}
    .meta-row, .chip-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .meta-row span, .chip-row span {{
      background: rgba(196,142,255,0.16);
      color: #dec8ff;
      border: 1px solid rgba(196,142,255,0.22);
      border-radius: 12px;
      padding: 7px 10px;
      font-size: 0.86rem;
      font-weight: 650;
    }}
    .hero-result {{
      padding: 18px;
      background: var(--panel-strong);
      border: 1px solid var(--border);
      border-radius: 16px;
    }}
    .color-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .color-row.compact {{ gap: 8px; }}
    .color-item {{
      display: grid;
      justify-items: center;
      gap: 6px;
      min-width: 54px;
      color: var(--muted);
      font-size: 0.72rem;
      text-align: center;
    }}
    .color-dot {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 2px solid rgba(255,255,255,0.78);
      box-shadow: 0 6px 16px rgba(0,0,0,0.28);
    }}
    .season-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .season-card {{
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
    }}
    .season-card h3 {{ text-transform: capitalize; }}
    .palette-block {{ margin-top: 14px; }}
    .palette-block h4 {{
      margin-bottom: 8px;
      color: var(--text);
      font-size: 0.88rem;
    }}
    .tip-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
    }}
    .tip-grid div {{
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
    }}
    .tip-grid strong, .tip-grid span {{ display: block; }}
    .tip-grid span {{ color: var(--muted); margin-top: 4px; }}
    details {{
      margin-top: 22px;
      border-top: 1px solid var(--border);
      padding-top: 14px;
    }}
    summary {{ cursor: pointer; color: var(--primary); font-weight: 700; }}
    pre {{
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: rgba(0,0,0,0.28);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      color: #e7e7ee;
    }}
    .error-card {{ border-color: rgba(255,122,144,0.35); }}
    @media (max-width: 720px) {{
      .page {{ padding: 20px; }}
      header {{ grid-template-columns: 1fr; }}
      .source-image {{ width: 100%; max-height: 280px; aspect-ratio: 16 / 10; }}
      .comparison-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div>
        <h1>Fit-Kolors</h1>
        <p class="subtitle">Comparativo visual de respostas por modelo via OpenRouter.</p>
        <p class="muted">Imagem: {esc(image_path)}</p>
      </div>
      <img class="source-image" src="{image_url}" alt="Imagem analisada">
    </header>
    <section class="comparison-grid">
      {cards}
    </section>
  </main>
</body>
</html>
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


async def main():
    load_dotenv()
    args = parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "Erro: configure OPENROUTER_API_KEY no .env antes de rodar o teste."
        )

    models = get_models()
    if not models:
        raise SystemExit(
            "Erro: configure OPENROUTER_TEST_MODELS ou OPENROUTER_MODEL no .env."
        )

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.is_file():
        raise SystemExit(f"Erro: imagem nao encontrada: {image_path}")

    image_data = image_path.read_bytes()
    image_url = make_image_url(image_data, image_path)
    prompt = load_analyzer_prompt()

    print(f"Testando {len(models)} modelo(s) via OpenRouter...")
    print(f"Imagem: {image_path}")

    results = await run_models(api_key, models, prompt, image_url)
    print_summary(results)
    json_path = save_results(results, image_path)
    html_path = save_html_results(results, image_path, image_url)
    print(f"\nResultado JSON salvo em: {json_path}")
    print(f"Resultado HTML salvo em: {html_path}")


if __name__ == "__main__":
    asyncio.run(main())
