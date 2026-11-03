# 数据源与能力清单

[返回首页](../README.md) · [使用示例](EXAMPLES.md) · [可选来源配置](CONFIGURATION.md)

## 先分清三个层级

| 层级 | 现在能做什么 | 使用要求 |
|---|---|---|
| 免登录起步层 | 42 个允许在 partial 下执行的命令，见下表 | 基础依赖、可访问的上游网络；无数据库账号要求 |
| 可选 API 引导层 | 13 个来源/产品的逐步配置及示例测试入口 | 自己申请的账号、凭据与相应产品权限 |
| 其他扩展代码 | 保留的公开/机构适配器、浏览器辅助代码与文件解析器 | 视命令可能需要机构访问、公开文件、依赖、浏览器环境或代码适配 |

没有任何层级意味着绕过源站登录、订阅或申请。`full` 允许配置/尝试扩展，但不为其授予权限。

## 免登录起步：42 个命令

这些命令来自当前版本的 `starter` 清单。每个命令的准确参数用 `research_help` 获取；数据集 ID、维度和版本使用实际返回值。此前实测是抽样请求，不是这 42 个命令所有参数的穷尽验收。

### 世界银行

国家目录、指标定义和年度序列。 [官方入口](https://api.worldbank.org/v2/)。

| 命令 | 用途 |
|---|---|
| `wb-countries` | 按国家名称或代码查目录 |
| `wb-indicator` | 读取指定指标的元数据 |
| `wb-series` | 查询国家与指标的年度序列 |

### 中国公开统计与司法资料

以下是特定公开栏目或检索入口，不代表全站所有资料均已接通。

| 命令 | 用途 |
|---|---|
| `nbs-macro-list` | 国家统计局国民经济运行相关报告目录 |
| `law-search` | 国家法律法规数据库关键词检索 |
| `spp-reports` | 最高检工作报告公开目录 |

### Crossref

文献与 DOI 元数据检索、筛选和详情；不代表全文访问。 [官方入口](https://api.crossref.org/)。

| 命令 | 用途 |
|---|---|
| `crossref` | 按关键词检索作品元数据 |
| `crossref-advanced` | 日期、类型、ISSN 等筛选检索 |
| `crossref-work` | 按 DOI 获取作品元数据 |

### arXiv

预印本检索与记录详情；需要保留版本及预印本性质。 [官方入口](https://export.arxiv.org/api/query)。

| 命令 | 用途 |
|---|---|
| `arxiv` | 关键词检索预印本记录 |
| `arxiv-detail` | 按 arXiv ID 读取详情 |

### PubMed / NCBI

检索可先返回 ID，再读取概要元数据；概要不等于文章正文或摘要。 [官方入口](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/)。

| 命令 | 用途 |
|---|---|
| `pubmed-search` | PubMed 关键词检索及 ID/分页 |
| `pubmed-summary` | 按 PubMed ID 获取概要元数据 |
| `ncbi-databases` | 列出 Entrez 数据库 |
| `ncbi-search` | 指定 Entrez 数据库检索 |
| `ncbi-summaries` | 按数据库与 ID 获取概要元数据 |

### NASA POWER

查询产品参数信息及点位日数据；应核对单位、坐标、时间标准和产品来源。 [官方入口](https://power.larc.nasa.gov/)。

| 命令 | 用途 |
|---|---|
| `nasa-power-configuration` | 读取参数及配置信息 |
| `nasa-power-daily` | 指定坐标、日期和参数的日数据 |

### USGS

地震目录查询，须核对震级、时间范围、分页与返回限制。 [官方入口](https://earthquake.usgs.gov/)。

| 命令 | 用途 |
|---|---|
| `usgs-earthquakes` | 查询时段内符合条件的地震记录 |

### 荷兰 CBS

OData 数据集目录 → 属性/维度/代码 → 观测值；不要跳过编码和单位的解释。 [官方入口](https://datasets.cbs.nl/odata/v1/CBS/)。

| 命令 | 用途 |
|---|---|
| `cbs-datasets` | 发现数据集 |
| `cbs-properties` | 读取数据集属性 |
| `cbs-dimensions` | 读取维度 |
| `cbs-codes` | 读取测度或维度代码 |
| `cbs-observations` | 按过滤条件获取观测值 |

### 英国 ONS

按数据集、edition、version 和维度查询。不同数据集地域范围并不相同。 [官方入口](https://api.beta.ons.gov.uk/v1/)。

| 命令 | 用途 |
|---|---|
| `ons-dataset-discover` | 按关键词扫描发现数据集 |
| `ons-editions` | 获取数据集 edition |
| `ons-dimensions` | 获取指定版本的维度 |
| `ons-options` | 获取某个维度的取值 |
| `ons-metadata` | 读取指定版本元数据 |
| `ons-observations` | 按维度条件读取观测值 |

### FAOSTAT

农业统计数据域、维度及代码到观测数据的查询流程。 [官方入口](https://www.fao.org/faostat/)。

| 命令 | 用途 |
|---|---|
| `faostat-api-domains` | 发现数据域 |
| `faostat-api-dimensions` | 查看数据域维度 |
| `faostat-api-codes` | 查看维度代码 |
| `faostat-api-data` | 按域、地区、项目、要素和年份查询 |

### BIS

先发现数据流，再读取结构并构造序列键，避免混用频率或计量口径。 [官方入口](https://data.bis.org/)。

| 命令 | 用途 |
|---|---|
| `bis-dataflows` | 发现数据流 |
| `bis-structure` | 获取数据流结构 |
| `bis-series` | 按数据流与序列键查询时段 |

中国公开来源的对应入口：[国家统计局最新发布](https://www.stats.gov.cn/sj/zxfb/)、[国家法律法规数据库](https://flk.npc.gov.cn/)、[最高检工作报告](https://www.spp.gov.cn/spp/gzbg/index.shtml)。这组命令分别提供其适配范围内的目录或检索结果，不能统一描述为“所有统计、法律或案例全文”。

## 13 个可选 API 引导项

下表列的是本版向导使用的标识和现有测试命令。需要先从实际官方门户核验申请、产品范围和凭据，再用 `research_verify` 执行；帮助页或注册成功不能算查询通过。官网界面、审批与产品条件可能变化。

| `source` | 来源/产品与官方入口 | 本版示例测试入口 |
|---|---|---|
| `eia` | [美国能源信息署 EIA](https://www.eia.gov/opendata/register.php) | `eia-v2-browse` |
| `cinii` | [CiNii Research](https://support.nii.ac.jp/en/cinii/api/developer) | `cinii-research-search` |
| `asean` | [ASEANstats](https://api.aseanstats.org/login) | `aseanstats-query` |
| `undp` | [UNDP DataPrism](https://dataprism.hdrdata.org/) | `undp-prism-metadata` |
| `elsevier` | [Elsevier Scopus / ScienceDirect](https://dev.elsevier.com/) | `elsevier-scopus-structured` |
| `wto` | [世界贸易组织 WTO](https://apiportal.wto.org/) | `wto-indicators` |
| `springer` | [Springer Nature Meta](https://dev.springernature.com/) | `springer-meta-open` |
| `wos` | [Web of Science Starter](https://developer.clarivate.com/) | `wos-starter-structured` |
| `iom-baseline` | [IOM DTM Baseline](https://dtmapi.iom.int/) | `iom-dtm-countries` |
| `iom-hna` | [IOM Humanitarian Needs Assessment](https://dtmapi.iom.int/) | `iom-hna-countries` |
| `iati` | [IATI Datastore](https://developer.iatistandard.org/) | `iati-datastore` |
| `un-population` | [联合国人口数据](https://population.un.org/dataportalapi/token/index.html) | `un-population-portal-data` |
| `cas` | [CAS Common Chemistry](https://commonchemistry.cas.org/api) | `cas-common-search` |

其中 IOM Baseline/HNA 是两个不同产品项；Elsevier 多种产品也不能仅凭一枚密钥推定全部获权。CAS Common Chemistry 适配的是公开子集产品，不是完整 CAS REGISTRY 或 SciFinder。

## 其他扩展代码怎样理解？

机器可读索引 [`command_catalog.json`](../command_catalog.json) 当前列出 3,753 个命令入口。一个数据库可能对应多个命令，另一些命令是目录、元数据、文件解析或已保留的历史适配入口，所以不能直接把命令数当作接通数据库数。

| 索引字段 | 含义 | 限制 |
|---|---|---|
| `command` | MCP 查询入口名 | 使用前仍需查看帮助 |
| `modules` | 静态识别的直接相关模块 | 不是完整运行时依赖清单 |
| `starter` | 是否在 partial 中开放 | 属于模式门控，不是联网健康状态 |
| `credential` | 静态扫描提示可能读取凭据 | 大多是模块依赖层提示，不能取代逐命令实测 |
| `institution` | 静态扫描提示可能有机构/学校条件 | 不能推断接收者已满足条件 |
| `may_need_public_file` | 可能引用本地公开资料文件 | 文件不随包提供，路径和格式需实际核验 |
| `readiness` | 起步/凭据/机构/待核验等分类 | 不是“实时已连接”的状态 |

本轮文档版修正了 `law-search` 被相关模块依赖误标为需凭据/机构的元数据；它仍是公开免登录起步入口。其他扩展标记可能粗略，以帮助、代码要求和实际响应共同判断。

### 浏览器辅助模块

`engine/*.mjs` 需要 AI 拥有适合的浏览器专用执行通道，并提供实际页面/响应上下文。它们不等于 MCP 自带浏览器驱动，也不自动读取任意浏览器会话。有些保留特定学校页面判断，换机构需适配。

### 官方文件解析模块

部分适配器用于读取指定官方 PDF、Excel、HTML 等文件。它们交付的是解析/查询代码，不附带发送者下载的文件或研究资料。缺文件时应报告具体缺失，不返回伪造的零结果。

## 怎样判断一个来源现在能否用？

先用 discover 找命令、help 读参数及要求，再按自己的网络和权限发起少量请求。确认响应确实属于预期来源、字段与条件一致、分页及截断明确、结果不是登录页。一次成功只证明该次请求；需要全文、其他数据集或更多年份时仍须分别核验。

源站改版、访问限制或接口停用可能使已有适配失效。本项目不会把失败、缺文件或等待注册自动解释为“无数据”。

## v1.2.0：新增开放的 5 个中国公开命令

这些入口原已存在，本版修正了凭据误标并开放给 partial；不是新订购数据库，也不需要 API 密钥。

| 命令 | 返回层级 | 用途 |
|---|---|---|
| `nbs-annual-discover` | 目录/候选 | 查找年度指标及其官方代码 |
| `nbs-annual-metadata` | 元数据 | 核对选定年度指标定义及单位 |
| `nbs-annual-series` | 数值 | 查询年度序列 |
| `nbs-frequency-discover` | 目录/候选 | 按年、季或月查找指标 |
| `nbs-frequency-series` | 数值 | 查询指定频率、时期和地区的序列 |

### 按返回层级发现

起步命令现在提供 `result_kind`：`observations`（观测数值）、`catalog`（目录/候选/ID）、`metadata`（定义与编码）、`bibliographic`（题录）、`text_search`（文本检索）。未整理的扩展可能仍为 `unclassified`。

`research_discover` 可加 `kind` 筛选。比如查询中国宏观数值时使用 `kind="observations"`，避免只拿到报告标题或数据流目录。

部分命令还提供 `count_option` 与 `example_args`，明确数量参数是 `--size`、`--rows`、`--limit` 还是 `--top`。它们不能随意互换；错误调用会返回简短的 `invalid_arguments`、本命令 usage 和可用选项。
