# 换一种活法：三步

水母的行为只有两个可换的点，都在 `jellyfish/core.py`。它们都是**纯函数**，所以你换完之后，它的一生仍然可以被完整重放。

## 第 1 步：换它看到什么

```python
def default_world(tick, seed=0):
    return {"weather": 2, "food": 1}       # 返回一个 dict，随便什么字段
```

真实例子（`examples/01_custom_world.py`）：

```python
def weather_world(tick, seed=0):
    kind = (tick * 5 + seed * 7) % 3        # 0 雨 / 1 多云 / 2 晴
    return {"weather": kind, "food": 1 if kind == 2 else 0}
```

接天气、股价、你仓库今天的 commit 数都行——只要**同一个 tick 永远得到同一个观测**。

## 第 2 步：换它怎么决定

两种方式：

**A. 用内置性格**（字符串）：`balanced` / `frugal` / `adventurous` / `opportunist`

```bash
python -m jellyfish tick --root demo --policy opportunist --times 30
```

**B. 传一个函数**（不需要改库）：

```python
def gambler(state, world, roll):
    if state["energy"] <= 1 and world.get("food"):
        return {"action": "eat", "reason": "赌徒：不成就没命了"}
    if world.get("food") and roll < 0.15:
        return {"action": "eat", "reason": "赌徒：手气到了"}
    return {"action": "move", "reason": "赌徒：下一格更好"}

state, record = step(state, world, roll, gambler)
```

**必须遵守两条**，否则重放会坏掉：

1. 不读时间、不读环境、不联网 —— 只依赖传入的 `state` / `world` / `roll`
2. 不改 `state` 本身（要改就返回新的）

## 第 3 步：看它活多久

```bash
python examples/03_compare.py
```

实测（40 个种子）：

| 活法 | 中位寿命 | 最短/最长 | 平均 吃/走 |
|---|---|---|---|
| balanced | 8 | 3/14 | 1.6 / 3.0 |
| frugal | 7 | 4/7 | 0.6 / 1.0 |
| adventurous | 5 | 3/7 | 1.0 / 4.0 |
| opportunist | 14 | 4/26 | 3.9 / 3.7 |
| gambler（自定义） | 3 | 3/7 | 0.5 / 3.5 |

赌是最短的活法——它在有吃的 85% 的情况里选择继续走。这就是「性格」在数据里的样子。

## 怎么验证你的改动没破坏重放

```bash
python -m pytest tests -q      # 里面有一条专门测「状态是日志的纯函数」
```

如果你写的 policy 读了时间或随机数，这条测试会红——因为它换一个进程重算，结果就对不上了。
