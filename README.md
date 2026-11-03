# 研究数据库 MCP

**让你的 AI 按问题查询统计数据、学术文献与法律资料，并保留来源。**

[下载最新版](https://github.com/He-He-He-He-He-He/research-database-mcp/releases/latest) · [安装教程](docs/QUICKSTART.md) · [数据源清单](docs/DATA_SOURCES.md) · [使用示例](docs/EXAMPLES.md) · [更新记录](docs/CHANGELOG.md)

## 能做什么

| 需求 | 提供的能力 |
|---|---|
| 跨国统计与中国公开指标 | 世界银行及各类官方统计来源，先查定义和代码，再取数值 |
| 学术文献与法律资料 | 检索题录、DOI、预印本和公开法律资料，保留原始出处 |
| 多项研究任务 | 世界银行多国/多指标查询、跨来源批量任务，分别记录失败 |
| 后续分析 | 完整JSON/CSV导出、按页读取结果、Python SDK |

这是可重复调用的查询工具。你需要什么，AI再去查；目录和帮助页不代表已经取得数据。详细范围见[数据源清单](docs/DATA_SOURCES.md)。

## 怎么安装

1. 从 [Releases](https://github.com/He-He-He-He-He-He/research-database-mcp/releases/latest) 下载ZIP并解压。
2. 把**整个文件夹**交给支持运行本地MCP的AI，并发给它这句话：

> 请阅读 docs/INSTALL.md，帮我安装并连接研究数据库MCP。先使用一般模式；只追加本服务，保留其他连接器。连接后做一次真实查询，确认能够使用。

也可在解压目录运行：

```sh
python3 -B install.py
```

需要Python 3.10+、curl、网络及支持stdio MCP的客户端。安装环境和进度放在包外；仅上传文件到普通聊天网页不会自动接通。完整步骤见[快速开始](docs/QUICKSTART.md)；给AI的操作规则见[安装指南](docs/INSTALL.md)。

## 三种模式

| 模式 | 开放范围 |
|---|---|
| **一般** `general`（默认） | 全部无需个人凭据、无需机构网络的命令 |
| **浙大内网** `zju` | 再开放依赖机构IP/内网的命令，仍需真实校园网络及订阅 |
| **登录** `login` | 再按需配置自己的账号、API密钥等；可暂停，下次继续 |

不用为公开功能注册。选择模式不会授予源站权限；云端AI也不会自动继承电脑的校园IP。网络连接失败会短暂跳过相应命令，保留配置。详见[配置与恢复](docs/CONFIGURATION.md)。

## 可以直接这样问AI

- “比较中国、美国、德国2020—2023年的GDP增长率和通胀率，给官方指标代码、原始值和来源。”
- “用Crossref和arXiv找多智能体研究的候选论文，只列真实返回的DOI或编号，区分预印本。”
- “批量查询这些来源，结果较大就导出JSON和CSV，聊天里只给摘要及分页读取入口。”

[更多例子](docs/EXAMPLES.md) · [批量、导出与SDK](docs/PRODUCTIVITY.md)

## 使用前了解

- 保留时间、单位、地区、口径和缺失值；目录、题录与数值不是同一层结果，预览也不是全量。
- 3,753个命令入口不等于3,753个已接通数据库；42条starter仅为起步样例，不限制一般模式。
- 公开包不含维护者账号、密钥、浏览器会话或研究资料；接收者使用自己的网络和凭据。
- 检查记录和已知限制见[实测能力与内容层级](docs/CAPABILITIES.md)、[验证范围](docs/VALIDATION.md)，常见问题见[故障排查](docs/TROUBLESHOOTING.md)。

## 进一步了解

[隐私与边界](docs/PRIVACY.md) · [架构与开发](docs/ARCHITECTURE.md) · [验收说明](docs/ACCEPTANCE.md)

仓库按用途分组：`src/` 放运行代码与适配器，`docs/` 放说明，`tests/` 放测试，`tools/` 放维护脚本。再分享请使用发布ZIP或白名单打包工具，避免夹带自己的运行数据。
