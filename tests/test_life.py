"""生命内核：纯函数、可重放、会死、可复活、日志不可篡改。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jellyfish import Life, initial_state, revive, step  # noqa: E402
from jellyfish.core import default_world  # noqa: E402


def test_step_is_pure_and_deterministic():
    state = initial_state(0)
    world = {"food": 1}
    a, rec_a = step(state, world, 0.3)
    b, rec_b = step(state, world, 0.3)
    assert a == b and rec_a == rec_b
    assert state["tick"] == 0, "step 不许改动入参"


def test_eating_raises_energy_and_moving_costs_more():
    hungry = dict(initial_state(0), energy=1)
    full, _ = step(hungry, {"food": 1}, 0.1)
    assert full["energy"] > hungry["energy"]
    moved, _ = step(dict(initial_state(0), energy=6), {"food": 0}, 0.1)
    assert moved["moved"] == 1 and moved["energy"] < 6


def test_energy_zero_kills_and_says_why():
    state, _ = step(dict(initial_state(0), energy=1), {"food": 0}, 0.9)
    assert state["alive"] is False
    assert "饿死" in state["death_reason"]


def test_revive_keeps_history_and_continues_ticks():
    dead = dict(initial_state(0), tick=9, energy=0, alive=False, death_reason="饿死")
    back = revive(dead)
    assert back["alive"] is True and back["tick"] == 10 and back["energy"] > 0


def test_state_is_a_pure_function_of_the_log(tmp_path):
    life = Life(tmp_path, seed=3)
    for _ in range(12):
        if life.state()["alive"]:
            life.tick()
    first = json.dumps(life.state(), sort_keys=True)
    again = json.dumps(Life(tmp_path, seed=3).state(), sort_keys=True)
    assert first == again


def test_state_at_reconstructs_earlier_days(tmp_path):
    life = Life(tmp_path, seed=1)
    for _ in range(10):
        if life.state()["alive"]:
            life.tick()
    now = life.state()
    earlier = life.state_at(3)
    assert earlier["tick"] <= now["tick"]
    assert json.dumps(life.state_at(now["tick"]), sort_keys=True) == json.dumps(now, sort_keys=True)


def test_tampering_with_the_log_is_detected(tmp_path):
    life = Life(tmp_path, seed=0)
    life.tick()
    path = tmp_path / "life.jsonl"
    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    record["roll"] = 0.99
    path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True) + chr(10), encoding="utf-8")
    with pytest.raises(ValueError):
        Life(tmp_path, seed=0).state()


def test_some_lives_actually_die_within_60_days():
    """如果所有生命都长命百岁，"会死"就只是个说法。"""
    deaths = 0
    for seed in range(10):
        life_state = initial_state(seed)
        for _ in range(60):
            world = default_world(life_state["tick"], seed)
            roll = ((life_state["tick"] * 2654435761 + seed) % 1000) / 1000.0
            life_state, _ = step(life_state, world, roll)
            if not life_state["alive"]:
                deaths += 1
                break
    assert deaths >= 8, "10 个种子里只有 %d 个死了，说明能量系统太宽松" % deaths


def test_export_writes_a_self_contained_page(tmp_path):
    from jellyfish.export import write_page

    life = Life(tmp_path / "l", seed=2)
    for _ in range(6):
        if life.state()["alive"]:
            life.tick()
    out = write_page(life, tmp_path / "life.html")
    html = Path(out).read_text(encoding="utf-8")
    assert "一个数字生命的一生" in html
    assert "http://" not in html and "https://" not in html
    assert "tick" in html


def test_biography_says_how_it_lived_and_died(tmp_path):
    """一句话传记 —— 这是要发出去的那句话，必须写清活几天、怎么死的。"""
    life = Life(tmp_path / "b", seed=0, name="阿水")
    for _ in range(30):
        if life.state()["alive"]:
            life.tick()
    text = life.biography()
    assert "阿水" in text
    assert "活了" in text
    if not life.state()["alive"]:
        assert "饿死" in text


def test_export_carries_the_name_and_the_biography(tmp_path):
    from jellyfish.export import write_page

    life = Life(tmp_path / "n", seed=1, name="小水母")
    for _ in range(5):
        if life.state()["alive"]:
            life.tick()
    html = Path(write_page(life, tmp_path / "p.html")).read_text(encoding="utf-8")
    assert "小水母 的一生" in html
    assert life.biography() in html


def test_food_actually_varies_over_time():
    """真出过的事故：乘数等于模数时 (tick*7) % 7 恒为 0，世界永远是常数。"""
    from jellyfish.core import default_world

    values = {default_world(t, 0)["food"] for t in range(30)}
    assert values == {0, 1}, "30 天内食物必须有/没有都出现过，否则世界是死的：%r" % values


def test_no_policy_is_immortal():
    """四种性格都必须会死 —— 否则「它会死」就只是个说法。"""
    from jellyfish.core import POLICIES, default_world

    for policy in POLICIES:
        for seed in range(6):
            state = initial_state(seed)
            for _ in range(120):
                world = default_world(state["tick"], seed)
                roll = ((state["tick"] * 2654435761 + seed) % 1000) / 1000.0
                state, _ = step(state, world, roll, policy)
                if not state["alive"]:
                    break
            assert not state["alive"], "%s 在 seed %d 上活过了 120 天" % (policy, seed)


def test_personalities_produce_different_lifespans():
    """如果四种性格活一样久，性格就没有意义。"""
    from jellyfish.core import POLICIES, default_world

    def life_days(policy, seed):
        state = initial_state(seed)
        for _ in range(120):
            world = default_world(state["tick"], seed)
            roll = ((state["tick"] * 2654435761 + seed) % 1000) / 1000.0
            state, _ = step(state, world, roll, policy)
            if not state["alive"]:
                break
        return state["tick"]

    averages = {p: sum(life_days(p, s) for s in range(12)) / 12 for p in POLICIES}
    spread = max(averages.values()) - min(averages.values())
    assert spread >= 2, "性格之间差异太小：%r" % averages


def test_different_seeds_give_different_lives():
    """分享链接的前提：种子不同，一生必须不同。"""
    from jellyfish.core import default_world

    lives = set()
    for seed in (0, 7, 42, 99):
        state = initial_state(seed)
        for _ in range(15):
            world = default_world(state["tick"], seed)
            roll = ((state["tick"] * 2654435761 + seed) % 1000) / 1000.0
            state, _ = step(state, world, roll, "balanced")
            if not state["alive"]:
                break
        lives.add((state["tick"], state["eaten"], state["moved"]))
    assert len(lives) >= 3, "不同种子几乎活成了一样：%r" % lives
