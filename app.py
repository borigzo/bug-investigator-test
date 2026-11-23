import html
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 8080


def calculate_share(part: float, total: float) -> float:
    return part / total


def extract_user_role(payload: dict) -> str:
    return payload["user"]["role"]


def parse_discount_percent(raw_value: str) -> int:
    value = int(raw_value.strip())
    if value < 0 or value > 100:
        raise ValueError(f"Discount out of range [0..100]: {value}")
    return value


def get_latest_item(items: list[str]) -> str:
    return items[5]


SCENARIOS = {
    "zero_division": {
        "title": "1. ZeroDivisionError",
        "desc": "Деление на ноль при расчёте доли (part=100, total=0)",
        "action": lambda: calculate_share(100, 0),
    },
    "key_error": {
        "title": "2. KeyError",
        "desc": "Отсутствует ключ 'role' в payload пользователя",
        "action": lambda: extract_user_role({"user": {"name": "Alice"}}),
    },
    "value_error": {
        "title": "3. ValueError",
        "desc": "Скидка передана со знаком процента ('15%' -> int)",
        "action": lambda: parse_discount_percent("15%"),
    },
    "index_error": {
        "title": "4. IndexError",
        "desc": "Обращение к несуществующему индексу [5] списка из 2 элементов",
        "action": lambda: get_latest_item(["first", "second"]),
    },
}


def render_page(selected_key: str | None = None, tb_text: str = "", summary: str = "") -> bytes:
    buttons_html = []
    for key, item in SCENARIOS.items():
        active_cls = " active" if key == selected_key else ""
        buttons_html.append(
            f'<button type="submit" name="scenario" value="{html.escape(key)}" class="btn{active_cls}">'
            f'<div class="btn-title">{html.escape(item["title"])}</div>'
            f'<div class="btn-desc">{html.escape(item["desc"])}</div>'
            f"</button>"
        )

    tb_block = ""
    if tb_text:
        tb_block = f"""
        <div class="result-box">
          <div class="result-header">
            <span class="badge">{html.escape(summary)}</span>
            <button type="button" class="copy-btn" onclick="copyTraceback()">Копировать traceback</button>
          </div>
          <pre id="tb-content">{html.escape(tb_text)}</pre>
        </div>
        """

    page = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title>Error Generator — Bug Investigator Test Bench</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      margin: 0;
      padding: 32px;
    }}
    .wrap {{
      max-width: 860px;
      margin: 0 auto;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 24px;
    }}
    p.sub {{
      margin: 0 0 24px;
      color: #94a3b8;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .btn {{
      text-align: left;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 14px 16px;
      color: #f8fafc;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s;
    }}
    .btn:hover {{
      border-color: #38bdf8;
      background: #243247;
    }}
    .btn.active {{
      border-color: #f97316;
      background: #2a211b;
    }}
    .btn-title {{
      font-weight: 700;
      font-size: 15px;
      margin-bottom: 4px;
    }}
    .btn-desc {{
      font-size: 13px;
      color: #94a3b8;
    }}
    .result-box {{
      background: #020617;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 16px;
    }}
    .result-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      gap: 12px;
    }}
    .badge {{
      color: #fca5a5;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
    }}
    .copy-btn {{
      background: #2563eb;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 8px 14px;
      font-size: 13px;
      cursor: pointer;
    }}
    .copy-btn:hover {{
      background: #1d4ed8;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      line-height: 1.5;
      color: #f1f5f9;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Генератор реальных ошибок для теста агента</h1>
    <p class="sub">Нажми кнопку, чтобы выполнить функцию и получить настоящий traceback для вставки в Chainlit.</p>
    <form method="POST" class="grid">
      {"".join(buttons_html)}
    </form>
    {tb_block}
  </div>
  <script>
    function copyTraceback() {{
      const el = document.getElementById("tb-content");
      if (!el) return;
      navigator.clipboard.writeText(el.innerText).then(() => {{
        const btn = document.querySelector(".copy-btn");
        if (btn) {{
          const prev = btn.innerText;
          btn.innerText = "Скопировано";
          setTimeout(() => btn.innerText = prev, 1500);
        }}
      }});
    }}
  </script>
</body>
</html>
"""
    return page.encode("utf-8")


class ErrorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = render_page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        params = parse_qs(raw)
        key = params.get("scenario", [""])[0]

        tb_text = ""
        summary = ""
        if key in SCENARIOS:
            try:
                SCENARIOS[key]["action"]()
            except Exception as exc:
                summary = f"{type(exc).__name__}: {exc}"
                tb_text = traceback.format_exc()

        body = render_page(selected_key=key, tb_text=tb_text, summary=summary)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), ErrorHandler)
    print(f"Error generator running at http://{HOST}:{PORT} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
