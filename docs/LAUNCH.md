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

## 发布前自查清单（每条都能一条命令验证）

- [x] README 首屏有图：`docs/example-card.svg`
- [x] README 里的命令都能跑：`python -m pytest tests/test_readme.py -q`
- [x] 陌生人不用凭证：`python jellyfish.py serve`（零依赖、零 key）
- [x] 有可发的图：`python jellyfish.py card --out card.svg`
- [x] 有可 fork 的路径：`docs/EXTEND.md` + `examples/03_compare.py`
- [x] CI 四平台绿：`gh run list --repo hansei996/jellyfish --limit 1`
- [ ] 社交预览图：仓库 Settings 里把 Social preview 设成 `docs/example-card.svg`（需要人点，1200×630 正好是 OG 尺寸）
- [ ] 一句话简介：仓库 description 现在是中文，可换成英文以匹配 GitHub 搜索

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
## 发布后 48 小时看什么（只看三个数，别自我安慰）

| 指标 | 怎么看 | 判读 |
|---|---|---|
| **独立访客** | `gh api repos/hansei996/jellyfish/traffic/views` | < 50 → 帖子没被看见（渠道问题）；> 200 → 渠道通了 |
| **star 转化** | stars ÷ 独立访客 | < 2% → 首屏没说服人（产品问题）；> 8% → 首屏对了 |
| **fork / issue** | `gh api repos/hansei996/jellyfish` | 有 fork 说明有人真动手；有 issue 说明有人在意细节 |

**两个失败模式要分开**：没人来 = 渠道问题；来了不 star = 首屏问题。修的东西完全不同。

## 48 小时后按结果分支

| 情况 | 下一步 |
|---|---|
| 访客 < 50 | 换渠道，不改代码 |
| 访客 > 200 但 star < 2% | 改首屏（第一张图、第一句话），不改功能 |
| 有 star 但无 fork | 补「改成自己那只」的极简路径（现在是三步，可压到一步） |
| 有 issue | 48 小时内回，这是唯一能自己制造势头的动作 |

## 我在发布后会自动做的事

- 每 24 小时读一次 traffic 与 star，写进 `docs/LAUNCH-LOG.md`
- 不刷、不求 star、不互 star
---

# 需要你动手的 4 步（我全权做不了的部分）

| # | 做什么 | 具体位置 | 耗时 |
|---|---|---|---|
| 1 | 设社交预览图 | 仓库 Settings → Social preview → 上传 `docs/example-card.svg`（若 GitHub 不收 SVG，先截图成 PNG，1200×630） | 1 分钟 |
| 2 | 选一个渠道发第一帖 | 见下方「首帖模板」，HN / Reddit / V2EX 任选一个 | 5 分钟 |
| 3 | 发完把链接给我 | 我用 `tools/traffic.py` 记每天的数 | 10 秒 |
| 4 | 48 小时后一起看数 | `docs/LAUNCH-LOG.md` | 2 分钟 |

## 首帖模板（英文，HN / Reddit 用）

标题：**Show HN: A jellyfish with a lifespan, whose whole life replays from a hash-chained log**

正文：

> I wanted a tiny thing that makes agent state auditable in a way you can actually watch.
> So it's a jellyfish: it forages, starves, dies. Every tick writes one line to an append-only
> sha256-chained log, and its state is a pure function of that log - so its whole life replays
> byte-for-byte, and tampering with one byte is detected immediately.
>
> Swap `decide_with()` or `default_world()` and it becomes your creature, still replayable.
> Pure stdlib, single file, no API keys: `curl -s <raw url> | python - tick --times 30`.
>
> What I'm unsure about: whether 'a life that can die' is actually more engaging than a dashboard,
> or just a gimmick. Feedback welcome.

## 首帖模板（中文，V2EX / 即刻 / B站动态）

> 写了个小东西：一只会死的水母。它每天决定吃还是走，体力归零就饿死。
> 有意思的是它的一生是一条 sha256 链的日志 —— 任何一天的状态都能重算，所以可以倒回去重看，
> 也可以换个种子再养一只（同一个种子一定是同一只）。单文件、零依赖、不用任何 key。
