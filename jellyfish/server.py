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
<title>一只水母</title>
<style>
:root{--ink:#0b1b2b;--dim:#5b7288;--line:#dce7f0;--glow:#3ec6d8;--dead:#98a6b3}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 -apple-system,Segoe UI,Microsoft YaHei,sans-serif;color:var(--ink);
background:radial-gradient(120% 80% at 50% 0%,#eaf7fb 0%,#f7fbfd 55%,#ffffff 100%);min-height:100vh}
.wrap{max-width:860px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:19px;margin:0 0 2px;font-weight:650}
.sub{color:var(--dim);font-size:13px;margin:0}
.stage{position:relative;height:320px;margin:18px 0 6px;display:flex;align-items:center;justify-content:center;overflow:hidden}
#jelly{transition:opacity .8s, transform .8s}
.dead #jelly{opacity:.28;transform:translateY(26px) scale(.86)}
.bio{font-size:17px;line-height:1.7;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin:0 0 14px}
.bio.dead{border-color:#f0c9c9;background:#fff7f7;color:#9b2c2c}
.row{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}
button{font:inherit;padding:9px 16px;border-radius:10px;border:1px solid #c9d8e4;background:#fff;cursor:pointer}
button:hover{background:#f1f8fb}
button.primary{background:#0b1b2b;color:#fff;border-color:#0b1b2b}
table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:600;background:#fbfdff}
tr.dead td{color:#9b2c2c}
code{font-family:ui-monospace,Consolas,monospace;font-size:12px;background:#eef4f8;padding:1px 5px;border-radius:4px}
.tick-n{color:var(--dim);font-variant-numeric:tabular-nums}
</style></head><body><div class="wrap">
<h1 id="title">一只水母</h1>
<p class="sub">它会饿、会死。每一步都写进 append-only 日志，可以倒回去重看。</p>
<p class="sub" id="seedline"></p>

<div class="stage"><svg id="jelly" width="220" height="260" viewBox="0 0 220 260">
  <defs><radialGradient id="g" cx="50%" cy="40%" r="60%">
    <stop offset="0%" stop-color="#9fe8f3" stop-opacity=".95"/>
    <stop offset="100%" stop-color="#3ec6d8" stop-opacity=".75"/></radialGradient></defs>
  <ellipse id="bell" cx="110" cy="96" rx="66" ry="52" fill="url(#g)"/>
  <g id="tent" stroke="#63d6e6" stroke-width="3" fill="none" stroke-linecap="round" opacity=".85">
    <path d="M78 140 q-8 34 6 62"/><path d="M98 146 q-6 40 4 74"/>
    <path d="M122 146 q6 40 -4 74"/><path d="M142 140 q8 34 -6 62"/>
  </g>
</svg></div>

<p class="bio" id="bio">…</p>
<div class="row">
  <button class="primary" onclick="tick(1)">过一天</button>
  <button onclick="tick(5)">过五天</button>
  <button onclick="revive()">救活它</button>
<button onclick="newLife()">换一只（新种子）</button>
</div>

<table><thead><tr><th>第几天</th><th>看到</th><th>决定</th><th>为什么</th><th>体力</th><th>状态</th></tr></thead>
<tbody id="rows"></tbody></table>
</div>
<script>
function render(d){
  document.getElementById('seedline').textContent =
    '种子 ' + d.seed + ' · 性格 ' + d.policy + ' · 同一个种子会得到完全相同的一生（可以把这个网址发给别人）';
  var s=d.state, alive=s.alive, e=s.energy;
  document.body.classList.toggle('dead', !alive);
  document.getElementById('title').textContent = d.name || '一只水母';
  var bio=document.getElementById('bio');
  bio.textContent = d.biography;
  bio.classList.toggle('dead', !alive);
  var bell=document.getElementById('bell');
  var rx = 38 + Math.min(e,8)/8*34;
  bell.setAttribute('rx', rx.toFixed(1));
  bell.setAttribute('ry', (rx*0.78).toFixed(1));
  document.getElementById('tent').setAttribute('stroke', alive? '#63d6e6' : '#b9c4cd');
  var rows=d.timeline.slice().reverse().map(function(r){
    return '<tr class="'+(r.alive?'':'dead')+'"><td class=tick-n>'+r.tick+'</td><td>食物 '+((r.world||{}).food)+'</td>'+
      '<td><code>'+r.action+'</code></td><td>'+r.reason+'</td><td>'+r.energy+'</td>'+
      '<td>'+(r.alive?'活着':(r.death_reason||'死了'))+'</td></tr>';
  }).join('');
  document.getElementById('rows').innerHTML = rows || '<tr><td colspan=6 class=sub>还没有任何一天。点「过一天」。</td></tr>';
}
function load(){ fetch('/api/state').then(r=>r.json()).then(render); }
function tick(n){ fetch('/api/tick?n='+(n||1),{method:'POST'}).then(r=>r.json()).then(render); }
function revive(){ fetch('/api/revive',{method:'POST'}).then(r=>r.json()).then(render); }
function newLife(){
  var seed = Math.floor(Math.random()*100000);
  history.replaceState(null,'','?seed='+seed);
  fetch('/api/new?seed='+seed,{method:'POST'}).then(r=>r.json()).then(render);
}
var params = new URLSearchParams(location.search);
var wanted = params.get('seed');
if (wanted !== null) {
  fetch('/api/new?seed=' + encodeURIComponent(wanted), {method:'POST'}).then(r=>r.json()).then(render);
} else {
  load();
}
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
        return json.dumps({"name": self.life.name, "seed": self.life.seed, "policy": str(self.life.policy),
                           "biography": self.life.biography(),
                           "state": self.life.state(), "timeline": self.life.timeline()}, ensure_ascii=False)

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
        if parsed.path == "/api/new":
            query = parse_qs(parsed.query)
            seed = int((query.get("seed") or ["0"])[0])
            policy = (query.get("policy") or [self.life.policy])[0]
            self.life.reset_with_seed(seed, policy=policy)
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