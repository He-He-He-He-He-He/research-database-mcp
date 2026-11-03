# 批量查询、结果导出、Python SDK与安装接入

[返回首页](../README.md) · [配置与模式](CONFIGURATION.md)

## 1. 世界银行优先使用原生批量

先help确认参数，一次查询多个国家、多个同源指标：

```json
{"command":"wb-series","args":["CHN,USA,DEU","NY.GDP.MKTP.KD.ZG,FP.CPI.TOTL.ZG","--start","2020","--end","2023"]}
```

逗号或分号分隔，最多20国、10指标。多指标默认source=2（WDI），其他同源数据可用 `--source` 指定官方源编号。内部请求使用世界银行支持的分号格式，不把每个国家拆成一次工具调用。[官方接口结构](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures)

结果继续为 `[metadata, rows]`，保留官方字段和更新日期。单页最多1000行，默认最多4页，`--max-pages`可设1—10。可用 `--page` 从指定页继续；从后续页开始时会记录先前页未取，不冒充全集。检查 `complete`、`pages_fetched`、`next_page` 和 `failed_pages`；上游缺失不补零。`complete`表示本次分页是否取完，不表示每个时期都有非空观测。大范围应缩小查询，不以截取的行数当源站全部记录。

## 2. 不同来源一次提交

以下参数传给 `research_batch`：

```json
{"queries":[{"id":"papers","command":"crossref","args":["renewable energy","--rows","2"]},{"id":"preprints","command":"arxiv","args":["renewable energy","--size","2"]}],"max_workers":2,"output":"compact"}
```

最多12项，1—4路并发；同命令名前缀的命令串行，避免同一来源突发请求。默认批次时间预算110秒，可设5—120秒；未开始且预算耗尽的项明确标记跳过。仍需遵守各源站额度/限流，不以并发绕开限制，也不保证固定倍数提速。

结果保留原顺序、id和各项错误。`ok=false`可能同时有成功项，检查 `partial`、`passed`、`failed`，不要丢掉失败项或将其当作零结果。每项仍通过原有模式和凭据检查。

## 3. 控制回传长度和导出

`research_query` 和 `research_batch` 支持：

| output | 行为 |
|---|---|
| auto（默认） | 小结果完整返回；超过24,000字符时保存完整JSON，返回有标记的预览及文件引用 |
| compact | 保存完整JSON，只返回摘要/预览与引用 |
| file | 保存完整文件，只回传状态和引用 |
| full | 请求完整内联；超过150万字符仍改为文件，避免超大消息 |

底层单次响应处理上限12MB；超限应缩小请求。`export_format="csv"`会同时保存完整JSON作为原始记录，CSV不替代来源、单位、分页和错误元数据。嵌套字段在CSV中编码为JSON；空值在CSV可能显示为空，请以JSON区分null、空串和零。以公式字符开头的文本会做电子表格安全转义，JSON保留原值。

```json
{"command":"wb-series","args":["CHN,USA","SP.POP.TOTL","--start","2020","--end","2023"],"output":"file","export_format":"csv"}
```

返回 `result_id`、文件路径、资源URI、大小和SHA-256。文件仅在**运行MCP的机器**上；云端容器文件不会自动出现在用户电脑，需让所在平台按其文件交付方式提供。支持MCP资源的客户端可读取URI；大资源则用下面的分页工具。

传给 `research_result`：

```json
{"result_id":"实际返回的32位编号","offset":0,"limit":20}
```

用 `next_offset` 继续；或提供JSON指针（如 `/result/1/0/value`）只读某个字段。只能读本工具生成的结果，不接受任意文件路径。如果单行过大，会明确提示继续选择行内字段，不能把空预览当无数据。

结果存放在包外状态目录的 `results` 中，不上传维护者、不自动共享或删除。包含自己的研究内容，需自行保管；不应直接压缩整个运行目录发给别人。原始发布包和pack_release仍不带结果。

## 4. Python调用

正常安装后，使用安装器返回的**独立虚拟环境Python**，可以在其他工作目录中导入SDK。`--config-only`不修改当前/系统Python导入路径，需要自行把运行副本放入Python导入路径。

```python
from research_sdk import ResearchClient, WorldBank, Crossref

client = ResearchClient()  # 安装环境读取自己保存的状态目录
# 尚未安装/使用另一个状态目录时，可显式传state_dir并client.setup("general")
result = WorldBank.get_series(
    ["CHN", "USA", "DEU"],
    ["NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG"],
    start=2020, end=2023, client=client, output="full"
)
if result["ok"]:
    metadata, rows = result["result"]
    # 继续用自己的分析/绘图库处理rows，先核对缺失值、单位和metadata。
```

SDK返回与MCP相同的字典/原始结构，不强制安装pandas或绘图库。`client.query`、`client.batch`、`client.result`使用相同的模式、状态和凭据路径；不会绕过登录要求或从其他应用导入账户。每个client的状态目录独立，不改全局环境；batch工作线程也保留该client的状态。

## 5. 指定客户端合并

默认只生成本服务的JSON/TOML片段，不修改任何客户端。可显式选择：

```sh
python3 -B install.py --client cursor
```

支持cursor、copilot、claude-desktop的明确默认位置；不扫描所有应用。VS Code旧格式或其他严格JSON客户端需提供实际配置文件：

```sh
python3 -B install.py --client vscode --client-config /path/to/mcp.json
```

VS Code `servers` 与其他客户端 `mcpServers` 分别处理。当前Copilot全局入口与旧VS Code配置有迁移差异，应以实际客户端为准。[VS Code官方迁移说明](https://code.visualstudio.com/docs/agent-customization/migrate-customizations)、[Cursor官方说明](https://docs.cursor.com/context/model-context-protocol)

已有配置先备份到本工具包外的私有状态目录，仅添加/更新research-databases，保留其他服务及本服务的额外环境配置。不同来源的同名服务拒绝自动覆盖；核对后才可用 `--replace-client-entry`。含注释的JSONC、异常格式和符号链接不会盲目改写；用客户端界面或AI按实际格式合并生成片段。Codex继续使用安装器生成的TOML片段，由接收者AI按现有配置合并，不用JSON替换整份TOML。

写好配置不代表客户端已连接：重连并看到7个工具，再做真实查询。客户端备份含自己的配置，不能发到聊天或发行包。

## 6. 软件源及失败重试

默认尊重当前pip、代理和CA配置。可显式指定HTTPS软件源；也可仅在真实连接超时/网络失败时，重试用户指定的备用源：

```sh
python3 -B install.py --fallback-index-url https://your-trusted-mirror.example/simple/
```

示例地址是占位符，须替换为你信任的实际源。`--index-url`指定主源，`--fallback-index-url`指定备用；不自动增加第三方源，不混用extra-index，不使用trusted-host，也不关闭证书验证。依赖不兼容/编译错误不会伪装成网络问题；证书错误需检查CA/代理。不打印私有源URL、凭据或完整pip日志。
