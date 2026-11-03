# 实测能力与内容层级

[返回首页](../README.md) · [验证记录](VALIDATION.md) · [数据源清单](DATA_SOURCES.md)

此页说明 v1.5.0 的抽样证据与边界。代码目录有3,753条命令，但不是3,753个已接通数据库。42条starter是历史起步回归样例；其他公开命令仍可在一般模式尝试。每个入口均有结果类型或明确的 `unclassified`，未知类型不冒充已验证。

机器可读的样例在 [verified_capabilities.json](../src/data/verified_capabilities.json)。`research_discover(verified_only=true)` 只显示收录了非空样例的命令；默认仍可发现尚未测试的入口。`sample_verified` 对应具体参数、日期、环境和结果层级，不表示全库权限或现在一定在线。没有证据的入口标为 `not_tested`；仅空结果与已观察失败分别标为 `sample_empty_only`、`sample_failed`。

## 如何读一次返回

| 字段 | 意义 |
|---|---|
| `ok` / `execution_ok` | 此次请求/解析是否完成；有效的零命中仍可为true |
| `result_status` | 目录、题录、正文单元、数值、零命中、缺失或尚未核验 |
| `record_count` / `has_records` | 返回的匹配记录，可能只是目录；不知结构时为null |
| `content_level` / `has_content` | 实际返回的正文单元、谱表或数值；目录和短命中片段不算正文 |
| `numeric_observation_count` / `data_verified` | 仅计入明确测量字段的数值；日期、ID、总条数不计入 |
| `has_data` | 当前返回包含声明的正文单元/谱表/数值；不能代替效力、真实性或权限核验 |
| `catalog_verification` | 发行版收录的历史样例证据，与本次实时响应分开 |
| `content_level_hint` / `followup_template` | 预期输出层级和目录字段绑定规则，是调用提示，不是联网证明 |

`empty_result/no_match` 是当前过滤条件零命中；`no_matching_observations` 是当前条件无观测行；`missing_observations` 是有记录或时期但没有可核验数值。缺失不补零；未声明测量字段返回 `observations_unverified`，不能从“有数字”猜成统计数据。`has_data:null` 表示尚不能判断。

`research_verify` 只有实际返回了已声明层级的非空记录/内容/数值才写入验证通过；空结果、缺失或未分类不会仅凭ok标为成功。

批量的 `passed` 仍是完成请求数。另有 `data_summary` 分列非空记录、目录、题录、短片段、正文/数值、零命中和缺失，不再用6个请求完成声称6项都取到数据。数字0有效，null、NaN和布尔值不算数值。表格值仍需核对单位、估计/实绩、版本、年份和质量标记。

## CBS：复现零命中并走到真实数值

`cbs-datasets --query population --top 2` 是荷语Title的子串过滤，实际 `$filter` 为 `contains(Title,'population')`；本次返回空。工具保持原条件，返回语言提示与 `Bevolking` 建议，**不自动替换查询，也不使用 `$search` 兜底**。

以下为实际通过的路径：

```text
cbs-datasets --query Bevolking --top 2
cbs-properties 03743
cbs-dimensions 03743
cbs-codes 03743 --dimension Measure --top 1
cbs-observations 03743 --top 2
```

样例得到真实测量值，测量代码M000352，单位aantal；03743是1995—2023的历史且已停止更新的数据集，不能当作最新人口。实际分析须读取维度代码、时期和单位，不把示例无过滤的前两行当作任意问题的答案。

复测：`python3 -B tools/capability_check.py --suite cbs --output <包外报告路径>`。其中一项预期就是零命中：6/6验收通过不等于6项都得到数值。

## 公开来源本次取到的层级

| 来源 | 已验证样例层级 | 限制 |
|---|---|---|
| 国家统计局 | GDP年度、PMI月度数值；最新发布命令仍仅目录 | CPI总指标未确认；PPI样例有时期无数值；一次社零发现遇TLS失败，不称全覆盖 |
| 世界银行 | 多国/多指标数值 | 保留源站年份、单位、缺失与分页 |
| CBS、Eurostat | 指定历史人口数值 | 先维度/代码/单位；历史人口示例不代表全部欧盟接口 |
| US Census | 2024 vintage人口估计 | 不代表最新版或所有普查产品 |
| US Treasury | 指定日期联邦债务数值 | 原美元字段，不擅改单位 |
| ADB | 指定PRC人口指标两年数值 | 原始UNIT和UNIT_MULT保留，口径须另核 |
| IADB | 目录和指标定义 | 已试pop/BRA/2023为零行；一条目录详情404，未计作数值能力 |
| WHO GHED / TB / 空气质量 | 卫生支出、结核估计、PM2.5样例数值 | 各产品分别验证；空气质量发布版本2026的样例观测年为2016 |
| IARC GLOBOCAN | 2022癌症估计值 | 不是登记病例数；此样例不能验证CI5plus登记命令 |
| FDA | 药品标签检索记录 | 不是临床判断或统计数值 |
| NASA POWER / USGS | 气象格点估计 / 地震事件测量值 | POWER不是当地气象站实测 |
| Crossref / arXiv / DataCite / Europe PMC | 文献题录与摘要等已返回字段 | DOI/链接不是全文权限，预印本不是已同行评议论文 |
| ONS / BIS / FAOSTAT / 最高检 | 所列样例为目录 | 目录成功不能代替后续观测或原文验证 |
| WTO timeseries | 已完成一个有凭据查询，结果为空 | 空结果不算数值通过；接收者须配置自己的密钥 |

公开数值与目录复测：`python3 -B tools/capability_check.py --suite all --output <包外报告路径>`。此脚本不读取个人凭据、不抄录正文，按每项预期分别验收。其他公开回归见 `tools/public_check.py`。

## 馆藏目录之后：真实记录号与原题名

本机校园网络实测，未改变DIRECT设置；每项只取一篇、一页或少量行。公开证据仅保留调用与结果长度/计数，不附正文、会话或用户凭据。

| 库 | 实际取得内容 | 第二步规则与边界 |
|---|---|---|
| 人大复印报刊 | 第1阅读器页正文段落 | 原id、title；每页两段，段数不是印刷页或整篇 |
| 鼎秀 | 第1页原文HTML | guid + **title_traditional**；不做简繁转换，无页面影像 |
| 天禄 | 第1页文字、标注、版面字段 | 原id、title；不含页面图像 |
| 中国资讯行 | 单篇正文段落 | 原record_id/database/partition；建议加 `--expected-title` 逐字核对 |
| 民国风云 | 单篇段落 | 命中片段另行标为snippet；正文用原query/result_offset/title，图片仅占位 |
| 国研网 | 单篇提取文字 | 目录返回detail_reference：doc_id、leaf_id、channel_id、expected_title；多路径按竖线分开解析，不能将完整chnidPath传给数字参数；图片、表格结构不保留 |
| 环球财经 | 单指标历史行、原单位 | dbid + **code**，不是目录UUID；不把未来年份当实绩 |
| 微谱 | 单条13C NMR谱表 | record_id + compound_name；compound_raw保留目录原名，仅分离明确的列表序号，保留化学位次；核对返回UUID和化合物名，不推定谱图、单位或结构 |

目录中的 `followup_template` 给出字段绑定方法。**选择同一条记录、保留原始题名；缺编号、身份不符或题名不符时停止该详情，不能猜号或改名以求通过。** 微谱列表序号分离与民国风云HTML高亮去标签均保留原字段及规则，不改变作品题名或化合物化学名称。

华案此次目录和详情均成功，但详情只是元数据，简介字段也可能为空。目录与详情现在调用同一个严格的 `getByIp` 精确机构检查；本次源码未发现两处检查规则不同，先前失败可能是不同会话响应，不能仅凭检索成功沿用身份。汉达仍无可靠的机构/检索验证，不列为正文可用。

中华经典、文泉、科学文库、掌阅、思想理论资源、边疆史地、东方杂志、古地图、域外汉籍、文心阁、数字方志、爱教材等现有详情多为书目、简介或目录，不能当作正文。公苑图片说明不等于图片文件。Ovid、FirstSearch、IncoPat、CNRDS现有题录入口不附带对应全文接口。法院公开案例通报和国知局公开调查报告不等于全部裁判文书或专利全文。

当前一页/篇可读，只证明本条在本次会话可读；不推出同一本其他页、整库下载、图片或后续会话权限。导出JSON/CSV保存的是工具已经返回的字段，导出目录不是下载原书。
