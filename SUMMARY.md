# 这 12 轮做了什么（以及每一条怎么复跑）

> 2026-10-26 · 19 个提交 · 47 条测试 · 零第三方依赖

## 一句话

**一只会饿死的水母，它的一生是一条可以完整重放的日志。**

## 三条入口（陌生人视角，全部无需凭证）

```bash
curl -s https://raw.githubusercontent.com/hansei996/jellyfish/main/jellyfish.py | python - tick --times 30
python jellyfish.py serve        # 打开 http://127.0.0.1:8080 看它活着/死掉
python jellyfish.py card  --out card.svg   # 1200x630 分享卡
```

## 每条主张与它的复跑方式

| 主张 | 怎么验 |
|---|---|
| 决定论重放：同一份日志永远重放同一只 | `pytest tests/test_life.py::test_state_is_a_pure_function_of_the_log` |
| 改一个字节立刻被发现 | `pytest tests/test_life.py::test_tampering_with_the_log_is_detected` |
| 不同种子给出不同的一生 | `pytest tests/test_life.py::test_different_seeds_give_different_lives` |
| 四种性格都会死 | `pytest tests/test_life.py::test_no_policy_is_immortal` |
| 单文件与包逐字节一致 | `pytest tests/test_single_file.py` |
| README 里每条命令都能跑 | `pytest tests/test_readme.py` |
| README 的数字与实际一致 | `pytest tests/test_stats.py` |
| 零第三方依赖 | `python tools/stats.py`（用 ast 扫全部 import） |
| 全仓脚本都钉了 UTF-8 | `pytest tests/test_encoding.py` |
| 推送前四道闸门 | `python tools/preflight.py` |

## 数字（都是算出来的，不是抄的）

```
测试            47（全部离线）
包              862 行
单文件          848 行 / 36.7 KB
第三方依赖       0
CI              ubuntu + windows × py3.10 / 3.12
提交            19
stars / forks  0 / 0
近 14 天访客      0
```

## 十二轮里被自己的测试否掉的东西

| 我原本写的 | 被什么否掉 |
|---|---|
| `(tick * 7) % 7` 决定食物 | 恒为 0，世界是死的，「饿死」根本不会发生 |
| `(tick * 3 + seed * 13) % 7` | 种子差 7 的倍数时完全相同，分享链接是假的 |
| 示例/构建脚本直接 `print` 中文 | Windows cp936 直接崩（同一个坑踩了三次，最后做成全仓 lint） |
| README 命令逐条独立跑 | 读者是**按顺序**跑的，独立跑等于没验证 |
| 手写的「43 条测试」 | 实际 47，测试当场抓住 |
| 纪律「推送前必须全绿」 | 我违约两次，改成 `preflight.py` 之后才没再犯 |

## 卡在哪

**M4（有外部反馈）完全阻塞在「发布」这一步**，而发布需要账号，不是技术问题。

`docs/LAUNCH.md` 里写了 4 步（社交预览图 / 首帖 / 给我链接 / 48 小时看数），中英模板都备好了。

## 如果继续，下一步做什么

先发，再看数，再改。**在没有人来过之前继续改代码，等于盲改。**
