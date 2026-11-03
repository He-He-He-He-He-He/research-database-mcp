"""江西省政府文件栏目标题查询和正文；仅省政府文件栏目。"""
import release_runtime
import json, subprocess
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
CHANNEL = '1750738299950129152'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    args = ['curl', '-fsS', '--max-time', '20', 'https://www.jiangxi.gov.cn/searchManuscript']
    for k, v in [('current', str(page)), ('pageSize', '15'), ('channelTreeIds[]', CHANNEL), ('title', keyword.strip()), ('Contenthtml', ''), ('isSearchHighlight', 'false')]:
        args += ['--data-urlencode', k + '=' + v]
    try:
        raw = release_runtime.run(args, capture_output=True, check=True, timeout=25).stdout
        data = json.loads(raw)['data']
    except (subprocess.SubprocessError, ValueError, KeyError) as e:
        raise RuntimeError('江西官方搜索不可用') from e
    rows = data.get('results')
    total = data.get('total')
    if data.get('page') != page or not isinstance(rows, list) or (not isinstance(total, int)) or isinstance(total, bool) or (total < 0):
        raise RuntimeError('搜索响应结构或页码异常')
    if len(rows) > total or (not rows and total > 0 and ((page - 1) * 15 < total)):
        raise RuntimeError('搜索总数与页内条目不一致，无法判断实际结果')
    if not rows and page > 1:
        raise RuntimeError('官方空页无法判断是否超出范围或服务故障，请先查询首页总数')
    items = []
    for row in rows:
        try:
            path = json.loads(row['urls'])['pc']
            meta = json.loads(row.get('metadata') or '{}') if isinstance(row.get('metadata'), str) else row.get('metadata', {})
        except (ValueError, KeyError, TypeError) as e:
            raise RuntimeError('官方结果结构异常') from e
        if not path.startswith('/jxsrmzf/szfwj/pc/content/'):
            raise RuntimeError('结果不属于省政府文件栏目')
        items.append({'title': row.get('title'), 'url': 'https://www.jiangxi.gov.cn' + path, 'published': row.get('pubDate'), 'metadata': meta, 'summary': row.get('summary')})
    return {'source': '江西省人民政府：省政府文件栏目', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': items, 'notice': '标题检索，仅省政府文件栏目；效力和附件以原站为准。'}

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要原文链接')
    p = urlsplit(url)
    try:
        port = p.port in (None, 80, 443)
    except ValueError:
        port = False
    if p.scheme not in ('http', 'https') or p.hostname != 'www.jiangxi.gov.cn' or p.username or p.password or (not port) or (not p.path.startswith('/jxsrmzf/szfwj/pc/content/')) or (not p.path.endswith('.html')):
        raise ValueError('仅支持江西省政府文件栏目正文链接')
    safe = 'https://www.jiangxi.gov.cn' + p.path
    try:
        r = release_runtime.run(['curl', '-fsS', '--max-time', '20', '--max-filesize', '5000000', '-w', '\n%{http_code} %{content_type}', safe], capture_output=True, check=True, timeout=25).stdout
        content, info = r.rsplit(b'\n', 1)
    except (subprocess.SubprocessError, ValueError) as e:
        raise RuntimeError('江西官方正文不可用') from e
    if not info.startswith(b'200 text/html') or len(content) > 5000000:
        raise RuntimeError('页面跳转、非 HTML 或过大')
    s = BeautifulSoup(content, 'html.parser')
    node = s.select_one('#zoomcon.article-content')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100:
        raise RuntimeError('正文过短')
    return {'url': safe, 'title': s.title.get_text(' ', strip=True) if s.title else None, 'text': text, 'notice': '附件与现行效力须另核。'}
