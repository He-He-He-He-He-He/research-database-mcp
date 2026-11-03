"""湖南省政府门户文件库标题检索与省政府站正文。"""
import release_runtime
import re, subprocess
from urllib.parse import urlsplit, urljoin
import requests
from bs4 import BeautifulSoup
SEARCH = 'https://searching.hunan.gov.cn/hunan/001000000/file'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 70):
        raise ValueError('页码须为 1–70 的整数')
    r = requests.get(SEARCH, params={'searchfields': 'title', 'q': keyword.strip(), 'p': page - 1}, timeout=25)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    match = re.search('var\\s+total\\s*=\\s*parseInt\\(\\s*[\\\'\\"](\\d+)[\\\'\\"]\\s*\\)', r.text)
    if not match:
        raise RuntimeError('无法识别原站总数')
    total = int(match.group(1))
    items = []
    for node in s.select('.resultbox'):
        a = node.select_one('.list-name a')
        if not a or not a.get('href'):
            raise RuntimeError('结果缺少标题或链接')
        fields = {}
        for li in node.select('li'):
            k, v = (li.select_one('span'), li.select_one('p'))
            if k and v:
                fields[k.get_text(strip=True)] = v.get_text('', strip=True)
        items.append({'title': a.get('title') or a.get_text('', strip=True), 'url': a['href'], 'fields': fields})
    if not items and (page - 1) * 10 < total:
        raise RuntimeError('原站返回的总数与页内结果不一致')
    return {'source': '湖南省政府门户文件库', 'keyword': keyword.strip(), 'page': page, 'total_approx': total, 'items': items, 'notice': '文件标题搜索，原站总数为约数；含部门及其他文件，效力与全文须回查原始发布页面。'}

def detail(url):
    if not isinstance(url, str):
        raise ValueError('需要正文链接')
    p = urlsplit(url)
    if p.scheme not in ('https', 'http') or p.hostname != 'www.hunan.gov.cn' or p.username or p.password or (p.port not in (None, 80, 443)) or (not p.path.startswith('/hnszf/xxgk/wjk/')):
        raise ValueError('仅支持湖南省政府文件库本站链接')
    safe = 'https://www.hunan.gov.cn' + p.path + ('?' + p.query if p.query else '')
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--noproxy', 'www.hunan.gov.cn', '--max-time', '25', '--max-filesize', '5000000', '--write-out', '\n%{http_code}', safe], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('湖南官网正文请求失败')
    raw, status = result.stdout.rsplit(b'\n', 1)
    if status != b'200' or len(raw) > 5000000:
        raise RuntimeError('原站重定向、状态异常或页面过大')
    s = BeautifulSoup(raw, 'html.parser')
    node = s.select_one('#zoom')
    if not node:
        raise RuntimeError('正文容器未识别')
    text = node.get_text('\n', strip=True)
    if len(text) < 100 or text.startswith('请点击下面链接'):
        raise RuntimeError('该条仅为外部链接或正文过短，请查看原站')
    return {'url': safe, 'title': s.title.get_text(' ', strip=True) if s.title else None, 'text': text, 'notice': '原始发布页面；附件及文件当前效力需另行核对。'}
