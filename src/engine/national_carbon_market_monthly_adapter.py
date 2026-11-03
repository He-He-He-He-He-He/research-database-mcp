"""上海环境能源交易所全国碳市场月度交易信息（个人查询）。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://overview.cneeex.com/'

def _get(url):
    with requests.get(url, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源发生重定向')
        out = bytearray()
        for part in r.iter_content(65536):
            out.extend(part)
            if len(out) > 2000000:
                raise ValueError('来源文件过大')
        return bytes(out)

def catalog(year):
    if isinstance(year, bool) or not isinstance(year, int) or (not 2021 <= year <= 2100):
        raise ValueError('年份须为 2021 及以后整数')
    index = BASE + f'qgtpfqjy/jysj/ydgk/{year}n/'
    s = BeautifulSoup(_get(index), 'html.parser')
    out = {}
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.search('全国碳市场每月综合价格行情及成交信息(20\\d{6})-(20\\d{6})', title)
        u = urljoin(index, a['href'])
        p = urlsplit(u)
        if m and m[1][:4] == str(year) and (p.scheme == 'https') and (p.hostname == 'overview.cneeex.com') and re.fullmatch('/c/20\\d\\d-\\d\\d-\\d\\d/\\d+\\.shtml', p.path):
            out[u] = {'title': title, 'start': m[1], 'end': m[2], 'url': u}
    return {'source': '上海环境能源交易所全国碳市场月度概况', 'source_url': index, 'year': year, 'items': list(out.values()), 'note': '仅当年度栏目当前页面；历史年份未必都有月报或同一命名。价格和成交量仅限个人查询；发布与使用应遵守交易机构声明。'}

def detail(year, end_date):
    if not isinstance(end_date, str) or not re.fullmatch('20\\d{6}', end_date):
        raise ValueError('结束日期须为 YYYYMMDD')
    item = next((x for x in catalog(year)['items'] if x['end'] == end_date), None)
    if not item:
        raise ValueError('未在该年栏目当前页找到结束日期')
    s = BeautifulSoup(_get(item['url']), 'html.parser')
    body = s.select_one('.article-con')
    if not body:
        raise ValueError('未识别正文')
    for x in body.select('script,style'):
        x.decompose()
    paras = [' '.join(p.get_text('', strip=True).split()) for p in body.select('p')]
    paras = [p for p in paras if p]
    if not paras or not any(('成交' in p for p in paras)):
        raise ValueError('未识别交易信息正文')
    return {'source': '上海环境能源交易所全国碳市场月度概况', **item, 'paragraphs': paras, 'note': '保留原文和交易机构声明，未自动计算或结构化；月度、年度累计和市场启动以来累计不能混同。价格单位元/吨，成交额单位元，具体以原文为准。仅供个人查询；交易信息发布须遵守机构声明。'}
