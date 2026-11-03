# 配置更多来源、暂停和恢复

[返回首页](../README.md) · [快速开始](QUICKSTART.md) · [常见问题](TROUBLESHOOTING.md)

## full 模式实际意味着什么

`partial` 只开放 42 个免登录起步命令。`full` 保留这些能力，并允许尝试其余目录命令、逐项配置可选来源。**切换 full 只是本工具的模式选择，不会自动给你数据库账号、API 审批或学校订阅。**

有些扩展本身是公开来源，切换模式后可能直接可用；其他扩展需要凭据、机构会话、官方文件、额外依赖或代码适配。没有必要为不使用的来源逐一注册。

## 1. 读取状态与选择下一步

以下均为 `research_setup` 的参数：

```json
{"action":"status"}
```

```json
{"action":"select","mode":"full"}
```

```json
{"action":"next"}
```

也可指定某个来源：

```json
{"action":"next","source":"eia"}
```

`status` 返回模式、是否暂停、各来源记录和进度位置。`next` 返回当前来源的官方入口、下一步骤和指导。不要把“已记录某步骤”当作网站实时状态。

## 2. 理解配置阶段

| 阶段 | 应完成的事情 | 不等同于 |
|---|---|---|
| `read_terms` | 查看官方用途、条款与申请说明，需要用户决定的由用户处理 | AI 替用户声明已经阅读所有协议 |
| `account_ready` | 接收者用自己的邮箱完成账号注册/验证或登录 | API 已获批 |
| `credential_issued` | 申请并获得对应 API 产品的有效凭据 | 网页上的机构订阅覆盖所有 API |
| `credential_saved` | 将凭据保存到本机安全存储或显式设置专用环境变量 | 密钥已经测试通过 |
| `tested` | 工具实际执行对应来源的示例查询并记录返回状态 | 全部数据、全部参数、全文权限永久可用 |

完成前四项后，可用：

```json
{"action":"mark","source":"eia","step":"account_ready"}
```

`tested` 不能通过 `mark` 手工冒充通过，应执行 `research_verify`。站点验证、密码输入、费用和身份声明由用户按自己的实际情况完成。

## 3. 可选 API 引导标识

这 13 项是代码中提供逐步引导与测试入口的来源/产品，不是 13 个“已替用户开好”的账户。入口及测试条件见 [数据源清单](DATA_SOURCES.md)。

| `source` | 来源/产品 | 专用环境变量 |
|---|---|---|
| `eia` | 美国能源信息署 EIA | `RESEARCH_MCP_EIA_KEY` |
| `cinii` | CiNii Research | `RESEARCH_MCP_CINII_KEY` |
| `asean` | ASEANstats | `RESEARCH_MCP_ASEAN_KEY` |
| `undp` | UNDP DataPrism | `RESEARCH_MCP_UNDP_KEY` |
| `elsevier` | Elsevier Scopus / ScienceDirect | `RESEARCH_MCP_ELSEVIER_KEY` |
| `wto` | WTO | `RESEARCH_MCP_WTO_KEY` |
| `springer` | Springer Nature Meta | `RESEARCH_MCP_SPRINGER_KEY` |
| `wos` | Web of Science Starter | `RESEARCH_MCP_WOS_KEY` |
| `iom-baseline` | IOM DTM Baseline | `RESEARCH_MCP_IOM_BASELINE_KEY` |
| `iom-hna` | IOM HNA | `RESEARCH_MCP_IOM_HNA_KEY` |
| `iati` | IATI Datastore | `RESEARCH_MCP_IATI_KEY` |
| `un-population` | 联合国人口数据 | `RESEARCH_MCP_UN_POPULATION_KEY` |
| `cas` | CAS Common Chemistry | `RESEARCH_MCP_CAS_KEY` |

环境变量方式需要由接收者明确提供给服务进程；不会自动从其他应用导入。不要把值写进聊天、源代码、发行包或公开仓库。注册界面、审批和额度可能变化，以实际官网为准。

## 4. 保存自己的凭据

建议使用安装后的 `onboarding.py credential SOURCE`，通过本机终端隐藏输入。必须：

- 使用安装器返回的 Python 与运行副本路径。
- 使用连接配置里相同的 `RESEARCH_MCP_STATE_DIR`，并处于 full 模式。
- 在接收者自己的电脑操作；不要让 AI 把密钥作为 MCP 参数传入。

POSIX 终端的示意写法如下；所有路径都要替换为**本次安装的真实输出**：

```sh
RESEARCH_MCP_STATE_DIR="/path/to/installed/state" "/path/to/runtime/python" -B "/path/to/installed/app/onboarding.py" credential eia
```

Windows 应使用对应的进程环境设置方式和自己的 Python 路径，不直接照抄 POSIX 命令。

macOS 使用本工具独立的钥匙串命名空间；其他系统需要可用的系统安全存储后端。若云端容器没有安全存储，可由用户在该平台的安全环境设置中显式提供专用变量，避免把密钥写回发行文件夹。

随后调用 `research_verify`，参数 `{"source":"eia"}`。失败时保留现有记录，检查错误及源站状态；不要无意义地重复注册或创建多个令牌。

## 5. 暂停、跳过、恢复

| 用户意图 | `research_setup` 参数 | 结果 |
|---|---|---|
| 暂停配置 | `{"action":"pause"}` | 保存暂停标记；不再推进下一配置步骤，已可用查询仍可使用 |
| 下次继续 | `{"action":"resume"}` | 清除暂停标记并给出下一未完成步骤 |
| 先做其他来源 | `{"action":"skip","source":"eia"}` | 默认推进时跳过该项，原记录保留 |
| 返回跳过项 | `{"action":"next","source":"eia"}` | 指定查看该来源的未完成步骤 |
| 回到公开起步功能 | `{"action":"select","mode":"partial"}` | 不删除以前的配置进度 |

进度保存的是步骤和测试状态，不是网站登录状态备份。重新登录、令牌续期和机构授权过期仍需按实际情况处理。

## 6. 机构访问、公开文件与其他凭据

向导还提供三个需要按具体情况处理的项目：

- `institution`：用用户自己的学校/机构目录核验 IP 或机构登录。有些辅助代码带有特定学校断言，必须按实际机构适配。网页能登录仍不等于 API 或全文可用。
- `public-files`：扩展命令若依赖 PDF、Excel 或其他公开文件，应从官方获取或由用户提供正确路径。历史下载材料不随包分发；缺文件不是零结果。
- `other-keys`：其他适配器的旧环境变量只有显式加上 `RESEARCH_MCP_EXTERNAL_` 前缀才会读取，具体变量名查看相应模块。不要导入发送者或其他应用的配置。

这些项需要人工核验；单纯确认 `manual_validation` 只记为用户/AI 确认，不能当作自动查询成功。

## 7. 更新与卸载范围

新版安装器在同一安装根目录建立新的版本代码副本，生成新连接配置，保留既有进度。应再次把新的服务路径接入客户端；已经运行的旧进程不会因为解压新版而自动切换。

若要卸载，先从客户端移除本服务并停止进程，再按用户意愿处理独立运行目录、进度和本工具命名空间的凭据。不要删除其他应用的账户或整个系统安全存储。发行 ZIP 本身不含这些运行状态。

v1.2.0 会保存正在配置的 `active_source`。指定某个来源后暂停，恢复时优先回到它的未完成步骤；更新安装也保留暂停标记。若该项已完成或被跳过，再推进到其他来源。客户端连接更新为新版路径后才能使用这一行为。
