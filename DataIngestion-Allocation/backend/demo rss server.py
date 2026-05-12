#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape as html_escape
from xml.sax.saxutils import escape as xml_escape
import threading

HOST = "127.0.0.1"
PORT = 5000

entries = []
lock = threading.Lock()


def rss_item(title: str, description: str, pub_date: datetime, guid: str) -> str:
    return f"""  <item>
    <title>{xml_escape(title)}</title>
    <description>{xml_escape(description)}</description>
    <pubDate>{format_datetime(pub_date)}</pubDate>
    <guid isPermaLink="false">{xml_escape(guid)}</guid>
  </item>"""


def render_root() -> bytes:
    with lock:
        latest = list(reversed(entries[-10:]))

    items_html = ""
    if latest:
        for e in latest:
            items_html += f"""
            <div class="item">
              <div class="title">{html_escape(e["title"])}</div>
              <div class="meta">{html_escape(e["when"])}</div>
              <div class="body">{html_escape(e["article"][:240])}{'...' if len(e["article"]) > 240 else ''}</div>
            </div>"""
    else:
        items_html = '<div class="empty">No entries yet.</div>'

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Demo RSS Server</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #f6f7f8;
      margin: 0;
      padding: 24px;
      color: #111;
    }}
    .wrap {{
      max-width: 980px;
      margin: 0 auto;
    }}
    .card {{
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 12px;
      padding: 18px;
      margin-bottom: 18px;
    }}
    h1, h2 {{
      margin: 0 0 12px 0;
    }}
    input, textarea {{
      width: 100%;
      box-sizing: border-box;
      border: 1px solid #ccc;
      border-radius: 10px;
      padding: 12px;
      font-size: 14px;
      margin-bottom: 12px;
      background: #fff;
    }}
    textarea {{
      min-height: 180px;
      resize: vertical;
    }}
    button {{
      border: 0;
      border-radius: 10px;
      padding: 12px 16px;
      background: #111;
      color: #fff;
      cursor: pointer;
      font-size: 14px;
    }}
    .item {{
      border-top: 1px solid #eee;
      padding: 12px 0;
    }}
    .item:first-child {{
      border-top: 0;
      padding-top: 0;
    }}
    .title {{
      font-weight: 700;
      margin-bottom: 4px;
    }}
    .meta {{
      font-size: 12px;
      color: #666;
      margin-bottom: 8px;
    }}
    .body {{
      white-space: pre-wrap;
      line-height: 1.45;
      color: #222;
    }}
    .empty {{
      color: #666;
      font-style: italic;
    }}
    .small {{
      font-size: 13px;
      color: #555;
    }}
    a {{
      color: #111;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Demo RSS Server</h1>
      <div class="small">Feed: <a href="/feed.xml">/feed.xml</a></div>
    </div>

    <div class="card">
      <h2>Add entry</h2>
      <form method="POST" action="/">
        <input type="text" name="title" placeholder="News title" required />
        <textarea name="article" placeholder="Full news article" required></textarea>
        <button type="submit">Publish</button>
      </form>
    </div>

    <div class="card">
      <h2>Recent entries</h2>
      {items_html}
    </div>
  </div>
</body>
</html>"""
    return html.encode("utf-8")


def render_feed(host: str) -> bytes:
    with lock:
        current = list(reversed(entries))

    items = "\n".join(
        rss_item(
            e["title"],
            e["article"],
            e["dt"],
            e["guid"],
        )
        for e in current
    )

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Demo RSS Feed</title>
    <link>http://{xml_escape(host)}/</link>
    <description>Minimal demo RSS feed generated from entered news items.</description>
    <language>en-us</language>
    <lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
{items}
  </channel>
</rss>
"""
    return xml.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self._send(200, render_root(), "text/html; charset=utf-8")
            return

        if path == "/feed.xml":
            host = self.headers.get("Host", f"{HOST}:{PORT}")
            self._send(200, render_feed(host), "application/rss+xml; charset=utf-8")
            return

        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(raw)

        title = form.get("title", [""])[0].strip()
        article = form.get("article", [""])[0].strip()

        if title and article:
            now = datetime.now(timezone.utc)
            entry = {
                "title": title,
                "article": article,
                "dt": now,
                "when": now.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                "guid": f"{int(now.timestamp() * 1000000)}-{len(entries) + 1}",
            }
            with lock:
                entries.append(entry)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}")
    print(f"RSS feed on http://{HOST}:{PORT}/feed.xml")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
