"""动画 SVG：必须是合法、自包含、真的在动。"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jellyfish.log import Life  # noqa: E402
from jellyfish.movie import build  # noqa: E402


def _life(tmp_path, ticks=20):
    life = Life(tmp_path, seed=0, name="小水母", policy="opportunist")
    for _ in range(ticks):
        if life.state()["alive"]:
            life.tick()
    return life


def test_movie_is_valid_svg(tmp_path):
    root = ET.fromstring(build(_life(tmp_path)))
    assert root.tag.endswith("svg")


def test_movie_actually_animates(tmp_path):
    svg = build(_life(tmp_path))
    assert svg.count("<animate") >= 5, "动画元素太少，等于一张静态图"
    assert svg.count('repeatCount="indefinite"') >= 5, "不循环就只能看一遍"


def test_movie_is_self_contained(tmp_path):
    svg = build(_life(tmp_path))
    rest = svg.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in rest and "https://" not in rest


def test_movie_refuses_an_empty_life(tmp_path):
    empty = Life(tmp_path / "empty", seed=0, name="空")
    with pytest.raises(ValueError):
        build(empty)


def test_demo_svg_in_docs_is_valid():
    path = ROOT / "docs" / "demo.svg"
    assert path.exists(), "README 内嵌的动画不见了"
    text = path.read_text(encoding="utf-8")
    ET.fromstring(text)
    assert "<animate" in text
