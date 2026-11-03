"""中国记协记者之家数据库公开分类及同站资料页。"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode, urlparse, urljoin
from bs4 import BeautifulSoup
BASE = 'https://jzzjsjk.chinaso.com'
CATEGORIES = {'新闻奖': 'chinaNewsAward', '长江韬奋奖': 'YangRiverTaofen', '好记者讲好故事': 'reportStory', '媒体社会责任报告': 'socialReport', '新媒体研究报告': 'newMediaReport', '新媒体年鉴': 'newMediaYearbook', '新闻援助': 'assistance'}

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'jzzjsjk.chinaso.com':
        raise ValueError('只允许记者之家 HTTPS 页面')
    r = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('记者之家请求失败: ' + r.stderr.decode('utf8', 'replace').strip())
    return r.stdout

def category(kind='新闻奖', page=1, size=10, keyword_on_page=''):
    """分类分页；可选关键词仅筛选当前页字段，不是全库搜索。"""
    page, size = (int(page), int(size))
    if kind not in CATEGORIES or page < 1 or (not 1 <= size <= 100):
        raise ValueError('分类、页码或每页数量无效')
    url = BASE + '/roll/category/' + CATEGORIES[kind] + '?' + urlencode({'pageNo': page, 'pageSize': size})
    try:
        r = json.loads(_get(url))
        d = r['data']
        items = d['results']
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('分类接口返回异常') from exc
    if r.get('status') != 1 or not isinstance(items, list):
        raise RuntimeError('分类接口返回失败')
    filtered = [x for x in items if keyword_on_page in ' '.join((str(v) for v in x.values() if v is not None))]
    return {'source': url, 'kind': kind, 'upstream_total': d.get('totalCount'), 'page': d.get('pageNo'), 'page_size': d.get('pageSize'), 'page_matches': len(filtered), 'results': filtered}

def detail(url):
    """读取同站 HTTPS 原文页；图像或音视频正文只返回资源链接。"""
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'jzzjsjk.chinaso.com' or (not re.fullmatch('/[A-Za-z0-9_-]+/detail/\\d{8}/\\d+_\\d+\\.html', p.path)):
        raise ValueError('只接受同站题录详情链接')
    s = BeautifulSoup(_get(url), 'html.parser')
    title = s.select_one('.section-content-title')
    body = s.select_one('.section-content-detail')
    if title is None or body is None:
        raise RuntimeError('未识别详情正文')
    media = [{'kind': tag.name, 'url': urljoin(url, tag.get('src'))} for tag in body.select('img[src],audio[src],video[src],source[src]')]
    return {'source': url, 'title': title.get_text(' ', strip=True), 'text': body.get_text('\n', strip=True), 'media': media}
