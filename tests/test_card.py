"""分享卡片：必须是合法 SVG、自包含、且带真实的一生数据。"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jellyfish.card import build  # noqa: E402
from jellyfish.log import Life  # noqa: E402


def _life(tmp_path, policy="opportunist", seed=0):
    life = Life(tmp_path, seed=seed, name="小水母", policy=policy)
    for _ in range(40):
        if life.state()["alive"]:
            life.tick()
    return life


def test_card_is_valid_svg(tmp_path):
    svg = build(_life(tmp_path))
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert root.get("width") == "1200" and root.get("height") == "630"


def test_card_carries_the_name_and_the_biography(tmp_path):
    life = _life(tmp_path)
    svg = build(life)
    assert "小水母" in svg
    assert life.biography() in svg


def test_card_is_self_contained(tmp_path):
    """除了 svg 命名空间，不许出现任何外部 URL —— 贴到哪儿都得能显示。"""
    svg = build(_life(tmp_path))
    assert "http://www.w3.org/2000/svg" in svg
    for banned in ("http://", "https://"):
        rest = svg.replace("http://www.w3.org/2000/svg", "")
        assert banned not in rest, "卡片里有外部引用：" + banned


def test_card_records_the_log_tail_hash(tmp_path):
    life = _life(tmp_path)
    svg = build(life)
    assert life.records()[-1]["hash"][:16] in svg, "卡片上应当能对回日志"


def test_example_card_in_docs_is_valid():
    path = ROOT / "docs" / "example-card.svg"
    assert path.exists(), "README 内嵌的示例卡不见了"
    ET.fromstring(path.read_text(encoding="utf-8"))
