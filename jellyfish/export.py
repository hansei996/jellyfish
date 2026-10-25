"""导出一份**单文件**的人生：把时间轴塞进 HTML，双击就能看，不需要服务器。

这是「可截图、可转发」的那一面：一个文件 = 一个生命的一生。
"""
from __future__ import annotations

import json
from pathlib import Path


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_page(life, out="life.html") -> str:
    timeline = life.timeline()
    state = life.state()
    payload = json.dumps({"state": state, "timeline": timeline}, ensure_ascii=False)
    html = (
        "<!DOCTYPE html><html lang=zh-CN><head><meta charset=utf-8>"
        "<title>一个数字生命的一生</title>"
        "<style>body{font:15px/1.6 -apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:24px;color:#111}"
        "h1{font-size:20px}table{border-collapse:collapse;width:100%;font-size:13px}"
        "th,td{border-bottom:1px solid #eee;padding:6px 8px;text-align:left;vertical-align:top}"
        "th{color:#777}tr.dead td{color:#b3261e}code{background:#f3f3f3;padding:1px 5px;border-radius:4px}"
        ".big{font-size:32px;font-weight:700}.card{background:#f6f6f6;border-radius:10px;padding:14px 18px;font-size:17px;line-height:1.7}</style></head><body>"
        "<h1>" + _esc(life.name) + " 的一生</h1>"
        "<p class=card>" + _esc(life.biography()) + "</p>"
        "<p class=big id=energy></p><p id=meta class=sub></p><p id=death></p>"
        "<table><thead><tr><th>tick</th><th>看到什么</th><th>决定</th><th>为什么</th><th>能量</th><th>状态</th></tr></thead>"
        "<tbody id=rows></tbody></table>"
        "<script>var DATA=" + payload + ";"
        "var s=DATA.state;document.getElementById('energy').textContent=s.energy+' 能量';"
        "document.getElementById('meta').textContent='第 '+s.tick+' 天 · 吃过 '+s.eaten+' 次 · 走过 '+s.moved+' 次';"
        "if(!s.alive){document.getElementById('death').textContent='死因：'+s.death_reason;}"
        "document.getElementById('rows').innerHTML=DATA.timeline.map(function(r){return '<tr class=\"'+(r.alive?'':'dead')+'\"><td>'+r.tick+'</td><td>食物 '+((r.world||{}).food)+'</td><td><code>'+r.action+'</code></td><td>'+r.reason+'</td><td>'+r.energy+'</td><td>'+(r.alive?'活着':(r.death_reason||'死了'))+'</td></tr>';}).join('');"
        "</script></body></html>"
    )
    path = Path(out)
    path.write_text(html, encoding="utf-8")
    return str(path)