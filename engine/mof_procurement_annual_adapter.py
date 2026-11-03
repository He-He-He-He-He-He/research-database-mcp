"""财政部全国政府采购简要情况：历史分页、年度正文和总规模提取。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://gks.mof.gov.cn/tongjishuju/'

def _get(url):
    with requests.get(url, timeout=(10, 20), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('上游重定向')
        out = bytearray()
        for chunk in r.iter_content(65536):
            out.extend(chunk)
            if len(out) > 3000000:
                raise ValueError('正文超出大小上限')
        return bytes(out)

def catalog(page=0):
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 30):
        raise ValueError('page 须为 0–30')
    index = BASE + ('index.htm' if not page else f'index_{page}.htm')
    s = BeautifulSoup(_get(index), 'html.parser')
    items = []
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})年全国政府采购简要情况', title)
        url = urljoin(index, a['href'])
        p = urlsplit(url)
        if m and p.scheme == 'https' and (p.hostname == 'gks.mof.gov.cn') and re.fullmatch('/tongjishuju/\\d{6}/t\\d{8}_\\d+\\.htm', p.path):
            items.append({'year': int(m[1]), 'title': title, 'url': url})
    return {'source': '财政部国库司全国政府采购简要情况', 'source_url': index, 'page': page, 'items': items, 'note': '仅筛选当前历史分页；空页不代表对应年度不存在。'}

def detail(year, max_pages=8):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year 须为整数')
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or (not 1 <= max_pages <= 30):
        raise ValueError('max_pages 须为 1–30')
    item = None
    for i in range(max_pages):
        item = next((x for x in catalog(i)['items'] if x['year'] == year), None)
        if item:
            break
    if not item:
        raise ValueError('未在扫描页数找到指定年')
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    body = soup.select_one('.TRS_Editor')
    if not body:
        raise ValueError('未识别正文')
    paras = [re.sub('\\s+', '', p.get_text('', strip=True)) for p in body.select('p')]
    paras = [p for p in paras if p]
    text = '\n'.join(paras)
    m = re.search(str(year) + '年全国政府采购规模为([\\d,.]+)亿元', text)
    if not m:
        raise ValueError('未识别同年度采购规模，停止解析')
    return {'source': '财政部国库司全国政府采购简要情况', **item, 'total_procurement_yi_yuan': m[1].replace(',', ''), 'paragraphs': paras, 'note': '采购总规模为原文提取的十进制字符串，单位亿元；全文去除空白以处理跨标签排版，分类、占比及统计口径请核原文，不等于全部政府支出或招标公告。'}
