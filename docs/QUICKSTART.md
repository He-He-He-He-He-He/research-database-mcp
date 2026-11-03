# 快速开始：从下载到第一次查询

[返回首页](../README.md) · [使用示例](EXAMPLES.md) · [常见问题](TROUBLESHOOTING.md)

## 1. 先判断安装在哪里

MCP 是 AI 调用工具的通道。这个项目提供 **stdio 本机服务**：客户端启动 Python 进程，与它交换工具调用和结果。

| 你的环境 | 是否适合 | 需要注意 |
|---|---|---|
| 支持启动 stdio MCP 的桌面 AI 客户端/代理 | 可以接入 | 安装在客户端能启动进程的电脑上 |
| 支持 stdio 子进程的 Linux 云端代理/容器 | 可以尝试 | 使用持久用户目录；网络、凭据和机构权限属于容器 |
| 仅能上传文件的普通聊天网页 | 不能仅靠上传就接通 | 需要额外的工具执行能力 |
| 只接受远程 HTTP MCP 地址的平台 | 不能直接填本项目文件路径使用 | 本包未提供 HTTP 托管服务；不要把 stdio 文件当 URL |

macOS 为主要验证平台。Windows/Linux 按标准 Python 与 curl 环境设计，但并未对全部扩展逐项验收；少数扩展依赖 macOS 工具或浏览器执行能力。

## 2. 准备运行条件

- Python 3.10 或更新版本。
- `curl` 可用。
- 可安装 Python 依赖的网络。
- 客户端支持添加本机 stdio MCP，并能使用运行环境里的 Python 和文件路径。

让 AI 检查 Python/curl 的版本与可用性即可；无需输出全部环境变量、浏览器资料或已有连接器配置。

## 3. 获取干净发行包

从 [Releases](https://github.com/He-He-He-He-He-He/research-database-mcp/releases/latest) 下载 ZIP 并解压。建议使用 Release 附件；其中不含 Git 元数据或运行环境。

可对解压文件夹进行严格检查：

```sh
python3 -B verify_manifest.py
```

成功时 `ok` 为 `true`、`extra_files` 为 `0`。如果直接克隆仓库，`.git` 会使严格发行检查报告额外文件；安装器和打包器仍只读取许可清单文件。

## 4. 选择安装模式

先由用户选择：

```sh
python3 -B install.py --mode partial
```

或：

```sh
python3 -B install.py --mode full
```

`partial` 开放免登录起步命令；`full` 保留它们并允许逐项配置扩展。选择 full 并不会替你注册账号，也不要求一次完成所有来源。

Windows 上使用自己的 `python` 或 `py` 命令。不要使用其他操作系统复制来的虚拟环境。

可选参数：

| 参数 | 作用 |
|---|---|
| `--install-dir` | 指定包外的用户安装根目录，云端容器应选择持久可写目录 |
| `--extras` | 安装高级文件解析/数据库适配器可能需要的额外依赖 |
| `--config-only` | 使用当前 Python，只复制代码并生成配置，不安装依赖；仅适合已准备好依赖的环境 |

正常安装会创建全新虚拟环境，不修改系统 Python。网络或依赖安装失败时可修复后重试，不要清空已有进度或关闭证书校验。

## 5. 理解安装器输出

安装器会输出一个 JSON 结果，其中包括：

| 字段 | 含义 |
|---|---|
| `installed` / `version` / `mode` | 本轮安装完成状态、版本和所选模式 |
| `mcp_entry` | 当前运行环境的启动命令、参数与本工具的环境设置 |
| `connection_file` | 常见 MCP 客户端的 JSON 配置片段文件 |
| `codex_connection_file` | 安装器生成的另一种客户端配置片段 |
| `runtime_app` | 包外代码副本位置 |
| `progress_location` | 本次安装使用的配置进度目录 |
| `source_unchanged` | 安装器不会把运行环境写回发行文件夹 |

安装器输出的路径属于**接收者自己的机器**，不是包内预装的发送者路径。不要把该输出或生成配置放回发行目录再分享。

默认安装根目录为用户的 `.local/share/research-database-mcp`；Windows 使用 `%LOCALAPPDATA%/research-database-mcp`。目录结构为：

```text
用户安装根目录/
├── apps/<版本>-<清单指纹>/    运行代码副本
├── runtime-venv/             当前系统新建的 Python 环境
├── connection/               当前机器的连接配置
└── state/                    配置进度及隔离运行文件
```

如显式设置了 `RESEARCH_MCP_STATE_DIR`，进度使用该目录；它也必须位于发行文件夹之外。

## 6. 把本服务接到 AI 客户端

让 AI 按客户端实际支持的格式追加 `mcp_entry`。JSON 配置使用 `mcpServers`；生成的 TOML 文件使用对应的配置格式，不能互相错贴。

- 只增加 `research-databases` 服务，不覆盖其他 MCP。
- 保留 `-B` 参数及生成的 `env`，确保进度路径一致且不产生字节码缓存。
- 如果客户端需要重连或重启，明确说明；不要把“写入配置”当成“已连接”。
- 需要查看现有配置时，在内存解析并仅输出服务名和本服务相关字段，不打印其他连接器令牌或授权头。

## 7. 验收第一次查询

AI 应能看到以下五个工具：

`research_setup`、`research_discover`、`research_help`、`research_query`、`research_verify`。

依次执行：

1. `research_setup`，参数 `{"action":"status"}`：确认模式和进度位置。
2. `research_discover`，参数 `{"keyword":"世界银行","starter_only":true,"limit":5}`：确认可发现命令。
3. `research_help`，参数 `{"command":"wb-series"}`：确认参数。
4. `research_query`，参数如下：

```json
{"command":"wb-series","args":["FRA","SP.POP.TOTL","--start","2020","--end","2023"]}
```

这会请求对应国家代码、指标代码及年份范围的实际数据。核对返回的国家、指标、年份、数值及上游信息，不要假定一定有每年的非空值。

看到工具列表、帮助页成功、实际查询返回，是三个不同的验收环节。若最后一步失败，记录具体原因并处理，不宣称接口已通过。

## 8. 接下来怎么用？

- 只需公开查询：留在 partial，查看 [使用示例](EXAMPLES.md)。
- 想配置其他 API 或机构访问：查看 [配置与暂停恢复](CONFIGURATION.md)。
- 遇到问题：查看 [常见问题](TROUBLESHOOTING.md)。
- 想更新或再次分享：重新运行新版安装器会创建新的版本代码副本，同一安装根目录的进度不被清空；分享使用原始发行文件或 `pack_release.py`，不转发运行目录。

旧版升级前可先用 `research_setup(status)` 确认原来的 `state_location`。若旧版使用了与新安装根目录不同的进度目录，应在新安装进程中显式设置相同的 `RESEARCH_MCP_STATE_DIR`，并保留生成连接配置中的该值。这样只切换代码路径，不必复制账号或把本机进度混进发行包。
