"""本地服务器：一条命令，一个会跳的页面。

    python -m jellyfish serve            # 启动，打开 http://127.0.0.1:8080
    python -m jellyfish tick             # 只推进一天（命令行用）
    python -m jellyfish state            # 看现在的状态

零依赖、零凭证、零网络：只用标准库 http.server。
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .log import Life

PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>一个数字生命</title>
<style>
:root{--ink:#111;--dim:#777;--line:#e6e6e6;--ok:#1f7a3d;--bad:#b3261e}
*{box-sizing:border-box}
body{font:15px/1.6 -apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:0;color:var(--ink);background:#fafafa}
header{padding:20px 24px 8px}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--dim);font-size:13px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:12px 24px}
.energy{font-size:34px;font-weight:700;letter-spacing:-1px}
.bar{height:12px;background:#eee;border-radius:6px;overflow:hidden;margin:8px 0 4px}
.bar>i{display:block;height:100%;background:var(--ok);transition:width .3s}
.dead .bar>i{background:var(--bad)}
button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid #ccc;background:#fff;cursor:pointer;margin-right:8px}
button:hover{background:#f2f2f2}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:600}
tr.dead td{color:var(--bad)}
code{font-family:ui-monospace,Consolas,monospace;font-size:12px;background:#f3f3f3;padding:1px 5px;border-radius:4px}
.banner{margin:0 24px;padding:10px 14px;border-radius:8px;background:#ffebee;color:var(--bad);font-weight:600}
</style></head><body>
<header><h1>一个数字生命</h1>
<p class="sub">它会饿、会死、会被人复活。每一步都写进 append-only 日志，可以倒回去重看。</p></header>
<div id="banner"></div>
<div class="card" id="vitals"></div>
<div class="card"><button onclick="tick()">推进一天</button><button onclick="tick(10)">推进十天</button><button onclick="revive()">复活它</button></div>
<div class="card"><table><thead><tr><th>tick</th><th>看到什么</th><th>决定</th><th>为什么</th><th>能量</th><th>状态</th></tr></thead><tbody id="rows"></tbody></table></div>
<script>
function render(d){
  const s=d.state;
  document.body.classList.toggle('dead',!s.alive);
  document.getElementById('banner').innerHTML = s.alive ? '' : '<div class="banner">它死了 —— '+s.death_reason+'</div>';
  document.getElementById('vitals').innerHTML =
    '<div class="energy">'+s.energy+' <span style="font-size:14px;font-weight:400;color:#777">能量</span></div>'+
    '<div class="bar"><i style="width:'+Math.min(100,s.energy/12*100)+'%"></i></div>'+
    '<div class="sub">第 '+s.tick+' 天 · '+(s.alive?'活着':'已死')+' · 吃过 '+s.eaten+' 次 · 走过 '+s.moved+' 次</div>';
  const rows=d.timeline.slice().reverse().map(r=>
    '<tr class="'+(r.alive?'':'dead')+'"><td>'+r.tick+'</td><td>食物 '+((r.world||{}).food??'-')+'</td><td><code>'+r.action+'</code></td><td>'+r.reason+'</td><td>'+r.energy+'</td><td>'+(r.alive?'活着':r.death_reason||'死了')+'</td></tr>').join('');
  document.getElementById('rows').innerHTML = rows || '<tr><td colspan="6" class="sub">还没有任何一天。点「推进一天」。</td></tr>';
}
function load(){ fetch('/api/state').then(r=>r.json()).then(render); }
function tick(n){ fetch('/api/tick?n='+(n||1),{method:'POST'}).then(r=>r.json()).then(render); }
function revive(){ fetch('/api/revive',{method:'POST'}).then(r=>r.json()).then(render); }
load();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    life: Life = None

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self):
        return json.dumps({"state": self.life.state(), "timeline": self.life.timeline()}, ensure_ascii=False)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if parsed.path == "/api/state":
            query = parse_qs(parsed.query)
            if "at" in query:
                state = self.life.state_at(int(query["at"][0]))
                return self._send(200, json.dumps({"state": state}, ensure_ascii=False))
            return self._send(200, self._json())
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tick":
            n = int((parse_qs(parsed.query).get("n") or ["1"])[0])
            for _ in range(max(1, min(n, 30))):
                if self.life.state()["alive"]:
                    self.life.tick()
                else:
                    break
            return self._send(200, self._json())
        if parsed.path == "/api/revive":
            try:
                self.life.do_revive()
            except ValueError as exc:
                return self._send(400, json.dumps({"error": str(exc)}, ensure_ascii=False))
            return self._send(200, self._json())
        return self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, fmt, *args):
        pass


def serve(root=".life", host="127.0.0.1", port=8080):
    Handler.life = Life(root)
    httpd = ThreadingHTTPServer((host, port), Handler)
    print("数字生命在 http://%s:%d 活着（日志：%s）" % (host, port, Handler.life.path))
    print("Ctrl+C 结束；结束后它仍会在日志里等着被重看。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("已停止。")
    finally:
        httpd.server_close()
