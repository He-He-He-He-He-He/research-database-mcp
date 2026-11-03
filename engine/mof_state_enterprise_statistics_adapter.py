"""财政部资产评估中心转载的全国国有企业经济运行历史公报。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://zcpgzx.mof.gov.cn/yjbg/'

def _get(url):
    with requests.get(url, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源重定向')
        b = bytearray()
        for part in r.iter_content(65536):
            b.extend(part)
            if len(b) > 3000000:
                raise ValueError('来源文件过大')
        return bytes(b)

def catalog(page=0):
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 20):
        raise ValueError('page 须为 0–20')
    index = BASE + ('index.htm' if page == 0 else f'index_{page}.htm')
    s = BeautifulSoup(_get(index), 'html.parser')
    out = []
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})年1-(\\d{1,2})月全国国有及国有控股企业经济运行情况', title)
        url = urljoin(index, a['href'])
        p = urlsplit(url)
        if m and 1 <= int(m[2]) <= 12 and (p.scheme == 'https') and (p.hostname == 'zcpgzx.mof.gov.cn') and re.fullmatch('/yjbg/\\d{6}/t\\d{8}_\\d+\\.htm', p.path):
            out.append({'year': int(m[1]), 'through_month': int(m[2]), 'title': title, 'url': url})
    return {'source': '财政部资产评估中心研究报告', 'source_url': index, 'page': page, 'items': out, 'note': '仅筛选当前页全国国有及国有控股企业运行公报；各期为年初至当月累计，资产负债率为期末数。'}

def detail(year, through_month, max_pages=4):
    if isinstance(year, bool) or not isinstance(year, int) or isinstance(through_month, bool) or (not isinstance(through_month, int)) or (not 1 <= through_month <= 12):
        raise ValueError('年份和截至月份须为整数')
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or (not 1 <= max_pages <= 10):
        raise ValueError('max_pages 须为 1–10')
    item = None
    for p in range(max_pages):
        item = next((x for x in catalog(p)['items'] if x['year'] == year and x['through_month'] == through_month), None)
        if item:
            break
    if not item:
        raise ValueError('未在指定页数找到该期')
    s = BeautifulSoup(_get(item['url']), 'html.parser')
    body = s.select_one('.TRS_Editor')
    if not body:
        raise ValueError('未识别正文')
    paras = [' '.join(p.get_text('', strip=True).split()) for p in body.select('p')]
    paras = [x for x in paras if x]
    if len(paras) < 3 or not any(('国有' in x for x in paras)):
        raise ValueError('正文结构无效')
    return {'source': '财政部资产评估中心研究报告（财政部国有企业经济运行公报）', **item, 'paragraphs': paras, 'note': '保留全文段落及脚注，非自动结构化指标；营业收入、利润、应交税费为年初至当月累计，资产负债率是期末值；企业覆盖范围和同口径同比计算须核原文脚注。'}
