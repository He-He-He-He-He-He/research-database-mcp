"""信用中国知识产权质押信息平台金融产品公开目录。"""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
URL = 'https://zscq.creditchina.gov.cn/zscq/wz/searchZrcp'

def products(keyword='', page=1, size=5, area='', bank=''):
    """查询产品公开目录；保留原始字段、缺失值及详情链接。"""
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页数量须为 1—100')
    query = urlencode({'keyword': keyword, 'area': area, 'bank': bank, 'page': page, 'pageSize': size})
    proc = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', URL + '?' + query], capture_output=True, text=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('平台请求失败: ' + proc.stderr.strip())
    try:
        response = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError('平台返回非 JSON 内容，可能是访问限制或接口变更') from exc
    if response.get('status') != 1:
        raise RuntimeError('平台返回错误: ' + str(response.get('message')))
    return response
