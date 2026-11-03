# v1.5.1 分发与验收

[返回首页](../README.md) · [验证记录](VALIDATION.md) · [实测能力](CAPABILITIES.md)

发行目录只含通用代码、目录、样例级证据与说明，不附维护者账号、密钥、浏览器会话、正文或研究下载。安装后的环境、客户端备份、连接配置、进度与查询导出都放在接收者自己的包外目录。清单白名单控制导出，ZIP不带缓存、虚拟环境、资源叉或原文件本机位置。

根目录保留install.py；实现、文档、测试与维护工具分别位于src/docs/tests/tools。原有七个MCP工具和三种模式不变；升级保留模式、暂停步骤与已导出结果。

可自行复核：

```sh
python3 -B tools/verify_manifest.py
python3 -B -m unittest discover -s tests -v
python3 -B tools/capability_check.py --suite cbs --output <包外报告路径>
```

严格清单检查用于解压后的干净发行文件夹；Git工作副本含.git等额外文件会被报告为不可直接分享。用python3 -B tools/pack_release.py导出清单白名单ZIP，不要直接压缩已经安装和使用过的目录。

验收区分请求完成、非空目录/题录、单篇/单页文字、数值和文件；期望零命中的回归通过不是取数成功。元数据与目录输出不宣称全文；缺失不补零，未知测量字段不猜数值。全新安装、升级、三系统回归与本版联网结果均另列在验证记录，历史版结果不充作本版结果。
