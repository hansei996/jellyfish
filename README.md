# jellyfish

**养一只会死的水母。它的一生可以被完整重放。**

> Raise a jellyfish that can starve to death. Its whole life is a replayable log.

```bash
python -m jellyfish serve        # → http://127.0.0.1:8080
```

零依赖、零凭证、零网络（纯 Python 标准库）。

## 你会看到什么

打开页面：一条能量条、每天它「看到什么 / 决定什么 / 为什么」，以及**它第几天会饿死**。

```text
$ python -m jellyfish tick --root demo --name 小水母 --times 30
{"tick": 18, "energy": 0, "alive": false,
 "death_reason": "饿死：第 18 个 tick 能量归零", "eaten": 6, "moved": 5}

$ python -m jellyfish export --root demo --out life.html
已导出 life.html        # 单文件，双击就开
```

导出页顶部就是那句话：

```text
小水母 的一生
小水母 活了 18 天，第 18 天饿死。它吃了 6 次，走了 5 次。
```

不同种子活的天数不同（40 个种子实测：中位数 17 天，最短 3 天）。

## 为什么是这个形状

| 特性 | 怎么做到的 |
|---|---|
| **决定论重放** | `step()` 是纯函数，随机值由调用方给出并写进日志；同一份日志永远重放出同一只水母 |
| **会死** | 能量归零即饿死；死亡不可撤销（只能由人复活，复活也是一条日志） |
| **可审计** | 每步记录观测、决策、理由、状态哈希；日志是 sha256 链，改一个字节立刻报错 |
| **可分享** | `export` 生成单文件人生，不联网也能看 |

## 换成你自己的水母

三个地方，都在 `jellyfish/core.py`：

| 换什么 | 函数 | 例子 |
|---|---|---|
| 它看到什么 | `default_world()` | 天气、股价、你仓库的 commit 数 |
| 它怎么决定 | `decide()` | LLM、规则、强化学习策略 |
| 它怎么死 | `step()` 里的死亡条件 | 负债、超时、触到红线 |

只要 `decide()` 保持纯函数、随机值走参数，**你的水母的一生也能被完整重放**。

## 日志格式

`life.jsonl`，一行一步：

```json
{"kind":"tick","world":{"food":1},"roll":0.42,"prev":null,"hash":"..."}
```

- `prev` / `hash`：sha256 链
- `roll`：这一 tick 的随机值 —— **必须在日志里**，否则不可重放
- 状态不落盘：状态永远由日志重算

## 边界

- 不是游戏引擎：没渲染、没物理、没寻路
- 不是 agent 框架：没工具调用、没 LLM（那是你要换的 decide）
- 不预测未来：它只记录已经发生的一生

## 测试

```bash
python -m pytest tests -q     # 11 passed，全部离线
```

## English in one breath

A jellyfish with a lifespan. It forages, starves, dies; you can rewind its entire life because every
decision is a pure function of an append-only hash-chained log. Swap decide() or default_world() and
it becomes your creature - still replayable. No deps, no keys, no network.
