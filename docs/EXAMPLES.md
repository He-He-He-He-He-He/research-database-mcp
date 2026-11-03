# 使用示例：从提问到实际查询

[返回首页](../README.md) · [数据源清单](DATA_SOURCES.md) · [配置进度](CONFIGURATION.md)

先确认 MCP 已连接，且 `research_setup(action="status")` 有所选模式。下面 JSON 均是**工具的参数**，不是 shell 命令，也不是已经查询得到的数据。每个例子都应先看 `research_help`；日期和数量可按问题调整。

## 1. 比较国家人口变化

可以对 AI 说：

> 比较法国和日本 2020—2023 年的人口变化。使用同一来源和指标，保留原始值，标注缺失年份，不要混用人口预测与历史统计。

先用 `research_discover`：

```json
{"keyword":"世界银行","starter_only":true,"limit":5}
```

查看 `research_help`：

```json
{"command":"wb-series"}
```

分别调用 `research_query`：

```json
{"command":"wb-series","args":["FRA","SP.POP.TOTL","--start","2020","--end","2023"]}
```

```json
{"command":"wb-series","args":["JPN","SP.POP.TOTL","--start","2020","--end","2023"]}
```

也应通过 `wb-indicator` 获取 `SP.POP.TOTL` 的元数据，核对指标定义。`wb-countries` 可按国家名/代码查找目录记录。

AI 应输出：来源与指标、国家与年份、原始值、缺失值说明及比较结论。跨来源比较时还要核对统计定义，不能只把两个同名列拼在一起。

## 2. 找论文、DOI 和原始链接

可以对 AI 说：

> 帮我查可再生能源政策研究的文献。先返回少量可核对的题录，列出标题、年份、作者、DOI 和来源链接；某字段没有返回就注明缺失。

`research_query`：

```json
{"command":"crossref","args":["renewable energy policy","--rows","5"]}
```

如需按时间范围查询，先看 `crossref-advanced` 的帮助，再使用：

```json
{"command":"crossref-advanced","args":["renewable energy policy","--start","2020-01-01","--end","2025-12-31","--rows","5"]}
```

对候选 DOI，可用 `crossref-work` 进一步核对。Crossref 检索结果是题录元数据及检索相关性结果，不能把它当作论文全文，也不能只凭题目就总结作者结论。

## 3. 查预印本或医学相关研究

预印本检索：

```json
{"command":"arxiv","args":["renewable energy","--size","3"]}
```

医学相关文献检索：

```json
{"command":"pubmed-search","args":["urban heat health","--size","3"]}
```

PubMed 检索可能先返回文献 ID 与分页信息；取得 ID 后，再按 `pubmed-summary` 帮助查询文献概要元数据。不要自己编造文献 ID，也不要把概要元数据当作论文正文或文章摘要。

对预印本，应保留其版本、提交时间和预印本性质；是否已发表需另行核验。

## 4. 查法律法规

可以对 AI 说：

> 检索消费者权益相关法律法规，列出候选条目、发布信息和效力状态。逐项核对标题，不把检索总数当作严格匹配数。

```json
{"command":"law-search","args":["消费者权益保护法","--size","3","--page","1"]}
```

该入口访问国家法律法规数据库的公开检索。站方可能对关键词分词并返回相关性结果；当前适配器特别提示：总数可能随请求条件变化，不能用它直接做法律文本数量统计。返回条目、全文权限和效力信息应分别核对。

`partial` 只开放此起步检索命令。若需要目录中的其他详情或扩展命令，可切换 full，再确认该命令的具体要求；切换模式本身不要求注册。

## 5. 找国家统计局经济运行报告入口

可以对 AI 说：

> 查国家统计局公开的国民经济运行报告入口，先给我报告标题和官网链接，再说明需要继续阅读哪些原文才能提取指标。

```json
{"command":"nbs-macro-list","args":["--page","1"]}
```

这个命令返回特定公开栏目的相关报告目录。它本身不是“查询国家统计局任意指标”的统一数据接口；正文、原表和指标时间序列需要适用的后续入口，不能凭目录标题生成数值。

最高检工作报告公开目录可另用：

```json
{"command":"spp-reports","args":[]}
```

## 6. 查指定地点的气候或地震记录

NASA POWER 日数据示例：

```json
{"command":"nasa-power-daily","args":["0","0","2024-01-01","2024-01-03","--parameters","T2M,PRECTOTCORR"]}
```

先通过 `nasa-power-configuration` 及返回元数据核对参数、单位和适用范围。这里的坐标和日期是演示条件，不代表用户的实际研究地点。不要将某类遥感/再分析产品自动表述为某个气象站的实测记录。

USGS 地震目录示例：

```json
{"command":"usgs-earthquakes","args":["2024-01-01","2024-01-02","--min-magnitude","5","--limit","5"]}
```

检查目录的时间范围、震级类型、坐标、分页及数量限制。单次返回五条不意味着这一时段只发生五次事件。

## 7. 先找数据集，再按维度查询

ONS 数据集发现：

```json
{"command":"ons-dataset-discover","args":["population","--max-pages","1","--limit","3"]}
```

CBS 数据集发现：

```json
{"command":"cbs-datasets","args":["--query","population","--top","3"]}
```

FAOSTAT 数据域发现：

```json
{"command":"faostat-api-domains","args":["--keyword","production","--limit","3"]}
```

BIS 数据流发现：

```json
{"command":"bis-dataflows","args":["exchange"]}
```

这几类查询通常分为：发现数据集/数据流 → 读取版本与维度 → 查询维度代码 → 提取观测值。后续 ID 和代码必须使用实际返回值，不应猜测。

尤其要核对：ONS 不同数据集的地域范围、CBS 编码及单位、FAOSTAT 的地域/商品/要素、BIS 的频率与序列键。发现列表有扫描页数和返回上限时，不能称为完整目录。

## 8. 逐步配置自己的 API，并在中途暂停

可以对 AI 说：

> 我希望增加能源数据查询。请从 EIA 的配置步骤开始，用我的账号，遇到密码和协议让我本人处理；如果要等待审批，就先跳过。

顺序调用 `research_setup`：

```json
{"action":"select","mode":"full"}
```

```json
{"action":"next","source":"eia"}
```

完成网站说明核对后，记录对应步骤：

```json
{"action":"mark","source":"eia","step":"read_terms"}
```

保存凭据后调用 `research_verify`：

```json
{"source":"eia"}
```

暂停与继续均用 `research_setup`：

```json
{"action":"pause"}
```

```json
{"action":"resume"}
```

凭据不要放进上述 JSON。具体保存方式和阶段含义见 [配置说明](CONFIGURATION.md)。

## 如何验收 AI 给出的研究结果？

建议要求 AI 至少保留：来源/链接、执行的筛选条件、时间与地域、单位/指标定义、分页与截断、缺失值、结果中的警示字段。

`ok: true` 表示工具执行得到相应返回，不代表数据完整、字段已被人工核验或所有查询条件都获得授权。若得到目录、帮助页或零结果，AI 应如实说明，并继续选择适合的查询步骤。
