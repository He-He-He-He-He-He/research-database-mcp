"""读取最高检门户公开文章正文；仅接受固定形态的本站文章链接。"""
import release_runtime
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

def spp_site_detail(url, timeout=25):
    if not isinstance(url, str):
        raise ValueError('需要最高检公开文章链接')
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'www.spp.gov.cn' or u.query or u.fragment or (not re.fullmatch('/+(?:[a-zA-Z0-9_-]+/)+\\d{6}/t\\d{8}_\\d+\\.shtml', u.path)):
        raise ValueError('仅支持最高检门户规范文章链接')
    r = requests.get(url, timeout=timeout, allow_redirects=False)
    r.raise_for_status()
    if r.status_code != 200:
        raise ValueError('文章返回重定向或异常状态')
    s = BeautifulSoup(r.content, 'html.parser')
    x = s.select_one('#fontzoom')
    if x is None:
        raise ValueError('未识别文章正文，页面可能改版或为不支持的栏目')
    for br in x.select('br'):
        br.replace_with('\n')
    for p in x.select('p'):
        p.insert_before('\n')
        p.insert_after('\n')
    text = '\n'.join((z.strip() for z in x.get_text().splitlines() if z.strip()))
    if not text:
        raise ValueError('文章正文为空')
    title = s.title.get_text(' ', strip=True) if s.title else ''
    return {'source': '最高人民检察院官网公开文章', 'source_url': url, 'title': title, 'text': text, 'note': '正文为网页文字，可能不含图片、附件及表格原格式；案例通报并不等于原始裁判文书，适用情况须核对后续状态。'}
