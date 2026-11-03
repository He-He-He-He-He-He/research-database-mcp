"""国家邮政局上半年分省快递业务原表，保留各年列顺序和单位。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2024: 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202407/c21604618b0342efa51e6b7c5c95d358.shtml', 2025: 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202507/433736ca3a9043b5a8b5e8bef1d9c4ed.shtml'}

def table(year, region=None):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('支持2024和2025年上半年')
    if region is not None and (not isinstance(region, str) or len(region) > 30):
        raise ValueError('地区无效')
    url = URLS[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    hits = []
    for t in s.find_all('table'):
        rows = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in t.find_all('tr')]
        if len(rows) == 33 and len(rows[0]) == 5 and (rows[1][0] == '全国') and (rows[0][0] == '单位') and ('快递业务' in ''.join(rows[0])):
            hits.append(rows)
    if len(hits) != 1:
        raise ValueError('未找到唯一预期分省表')
    rows = hits[0]
    data = rows[1:] if region is None else [x for x in rows[1:] if x[0] == region]
    return {'source': '国家邮政局', 'source_url': url, 'period': str(year) + '年上半年', 'headers': rows[0], 'rows': data, 'note': '原表为上半年累计；2024和2025列顺序及收入单位不同，请按各年原表头读取；同比为百分比，非年度全年。原文说明数据舍入可能导致合计差异。'}
