"""最高人民检察院官网跨栏目公开搜索。"""
import release_runtime
from urllib.parse import urlparse, quote
import requests
from bs4 import BeautifulSoup
URL = 'https://www.spp.gov.cn/guestweb/s'

def spp_site_search(query, page=1, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 100):
        raise ValueError('页码须为 1–100 的整数')
    q = query.strip()
    params = {'searchWord': quote(q, safe=''), 'column': quote('全部', safe=''), 'wordPlace': '0', 'orderBy': '1', 'pageSize': 10, 'pageNum': page - 1, 'timeStamp': 0, 'siteCode': 'N000005434', 'checkHandle': 1, 'countKey': 0, 'areaSearchFlag': 0}
    r = requests.get(URL, params=params, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    total = s.select_one('#totalDataNum')
    current = s.select_one('#allSearchWord')
    if total is None or not total.get('value', '').isdigit() or current is None or (current.get('value') != q):
        raise ValueError('搜索页面格式或查询绑定异常')
    rows = []
    for box in s.select('#showPage .Residence-permit'):
        a = box.select_one('a.titlec')
        date = box.select_one('.quily-con')
        snippet = box.select_one('.p-text-color')
        category = box.select_one('.permit-title .type')
        if not a or not a.get('href'):
            raise ValueError('结果结构异常')
        u = urlparse(a['href'])
        if u.scheme != 'https' or u.hostname != 'www.spp.gov.cn':
            raise ValueError('结果域名异常')
        rows.append({'title': a.get('title') or a.get_text('', strip=True), 'url': a['href'], 'date': date.get_text(' ', strip=True) if date else None, 'category': category.get_text(' ', strip=True) if category else None, 'snippet': snippet.get_text('', strip=True) if snippet else None})
    n = int(total['value'])
    if (page - 1) * 10 < n and (not rows):
        raise ValueError('上游报告有结果，但未解析到首屏')
    return {'source': '最高人民检察院官网跨栏目全文检索', 'source_url': r.url, 'query': q, 'upstream_total': n, 'page': page, 'items': rows, 'note': '官网全文匹配按时间排序，结果含新闻、典型及指导案例等，不等于全部案件文书或指导案例；依官网官方翻页参数每页 10 条；服务端隐藏页码始终回显 0，页码依请求参数而非回显核验，搜索结果可能随更新变化；正文和效力须核对原文。'}
