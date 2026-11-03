"""国家邮政局分省快递业务累计原表，保留各年列顺序和单位。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {'2024-10': 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202411/cb8e6841781c41d59bab21365b0ed452.shtml', '2024-11': 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202412/213132b50e1c458284e07bfde40a1d72.shtml', '2025-10': 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202511/5909c14cc22a40bcbc85999d74b41a3d.shtml', '2025-11': 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202512/f41902e3f29a450f9b36fdcb242afcc8.shtml'}

def table(period, region=None):
    if period not in URLS:
        raise ValueError('支持 2024-10、2024-11、2025-10、2025-11')
    if region is not None and (not isinstance(region, str) or len(region) > 30):
        raise ValueError('地区无效')
    url = URLS[period]
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
    return {'source': '国家邮政局', 'source_url': url, 'period': period + '月累计', 'headers': rows[0], 'rows': data, 'note': '原表为当年1月至指定月累计，不是当月；2024和2025列顺序及业务量单位不同，请按各年原表头读取；同比为百分比，非单月。原文说明数据舍入可能导致合计差异。'}
