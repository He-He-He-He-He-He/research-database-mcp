"""北京市公共数据开放平台字段检索目录。"""
import release_runtime
import json
import subprocess
from urllib.parse import urlsplit, urlunsplit
URL = 'https://data.beijing.gov.cn/cms/web/search'

def search(keyword='', page=1, size=10):
    if not isinstance(keyword, str) or len(keyword) > 38:
        raise ValueError('字段关键词须不超过38字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 50):
        raise ValueError('每页须为1至50项')
    cmd = ['/usr/bin/curl', '-fsS', '--max-time', '25', '--max-filesize', '5000000', '-G', URL]
    for param in ('orderFiled=publishDate', 'orderMethod=desc', f'pageSize={size}', f'curPage={page}', 'subject=', 'typeName=', f'columns={keyword}'):
        cmd.extend(['--data-urlencode', param])
    try:
        raw = release_runtime.run(cmd, check=True, capture_output=True, timeout=30).stdout
        data = json.loads(raw)
    except (subprocess.SubprocessError, ValueError) as exc:
        raise RuntimeError('北京公共数据目录请求失败或响应非 JSON') from exc
    if not isinstance(data, dict) or data.get('status') != 200 or (not isinstance(data.get('page'), dict)) or (not isinstance(data.get('object'), dict)):
        raise RuntimeError('目录响应异常')
    info = data['page']
    docs = data['object'].get('docs')
    total = info.get('count')
    if isinstance(total, bool) or not isinstance(total, int) or total < 0 or (info.get('currentPage') != page) or (info.get('pageSize') != size) or (not isinstance(docs, list)) or (len(docs) > size) or (len(docs) > total) or (not docs and (page - 1) * size < total):
        raise RuntimeError('目录总数、页码或条目异常')
    out = []
    for d in docs:
        if not isinstance(d, dict) or not isinstance(d.get('name'), str):
            raise RuntimeError('目录条目结构异常')
        raw_url = d.get('url') or ''
        u = urlsplit(raw_url)
        if u.scheme not in ('http', 'https') or u.hostname != 'data.beijing.gov.cn' or u.username or u.password or (u.port not in (None, 80, 443)):
            raise RuntimeError('目录链接不属于官方站点')
        url = urlunsplit(('https', 'data.beijing.gov.cn', u.path, u.query, ''))
        out.append({'title': d['name'], 'url': url, 'id': d.get('id'), 'department': d.get('department'), 'source': d.get('source'), 'subject': d.get('subject'), 'columns': d.get('columns'), 'publishDate': d.get('publishDate'), 'modifyDate': d.get('modifyDate')})
    return {'source': '北京市公共数据开放平台', 'source_url': 'https://data.beijing.gov.cn/zyml/kfml/index.htm', 'keyword': keyword, 'page': page, 'size': size, 'total': total, 'items': out, 'note': '官网字段搜索：关键词匹配数据字段而非完整文件内容；目录含往年资源。时间字段保留官网原始值；详情、开放状态、更新情况和下载权限以官网为准，目录不等于取得数据文件。'}
