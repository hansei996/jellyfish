# 发布稿与投放点（对外发布前需用户确认）

## 一句话（英文，发 HN / Reddit / X 用）

> A jellyfish with a lifespan you can starve to death - and its entire life replays byte-for-byte from an append-only log. Pure stdlib, single file, no API keys.

## 一段话（中文，发群/朋友圈用）

> 写了个小东西：一只会死的水母。它每天要决定吃还是走，体力归零就饿死。
> 有意思的地方是——它的一生是一条 sha256 链的日志，任何一天的状态都能重算出来，所以你可以把它的一生倒回去重看，也可以换掉它的「性格」再养一只。
> 单文件、零依赖、不用任何 key。`python jellyfish.py serve` 就有一个会动的水母。

## 三条可发的素材（都要真实，不许编）

| 素材 | 内容 | 状态 |
|---|---|---|
| 寿命对比 | 五种活法：balanced 8 天 / frugal 7 天 / adventurous 5 天 / opportunist 14 天 / gambler 3 天 | ✅ 可复跑 `python examples/03_compare.py` |
| 死亡瞬间 | 小水母 活了 10 天，第 10 天饿死。它吃了 3 次，走了 4 次。 | ✅ `python jellyfish.py export` |
| 重放保证 | 改日志一个字节，重放立刻报错 | ✅ 有测试 |

## 投放点（按预期回报排序，都需要用户账号或确认）

| 渠道 | 为什么可能有效 | 阻塞 |
|---|---|---|
| GitHub topics（已加：agent / simulation / digital-life / python） | 被动流量，零成本 | 已做 |
| Hacker News「Show HN」 | OpenClaw 就是靠自然分享起量的 | 需要 HN 账号 |
| r/Simulated / r/artificial / r/Python 的周末 show-off 帖 | 有明确的展示文化 | 需要 Reddit 账号 |
| V2EX / 即刻 / 少数派 | 中文开发者聚集 | 需要账号 |
| 掘金 / B站动态 | 老板有 B站账号 | 需要老板动手 |

## 我不做的事

- 不刷 star、不互 star
- 不注册新账号
- 不写「它会自己乱来」这类恐怖叙事（它没有行动力）
