"""保山市统计局各县市区人口主要数据：已验证可读取的年份。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2017: 'https://www.baoshan.gov.cn/info/4224/4117404.htm', 2019: 'https://www.baoshan.gov.cn/info/4224/4117444.htm', 2021: 'https://www.baoshan.gov.cn/info/4224/4117464.htm', 2022: 'https://www.baoshan.gov.cn/info/4224/9444824.htm', 2023: 'https://www.baoshan.gov.cn/info/4224/9979944.htm', 2024: 'https://www.baoshan.gov.cn/info/4224/10180634.htm', 2025: 'https://www.baoshan.gov.cn/info/4224/10361514.htm'}
INDEX = 'https://www.baoshan.gov.cn/bmym/bsstjj/zfxxgkpt/fdzdgknr/tjsj/rkzysj.htm'

def table(year, keyword=''):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('支持 2017、2019、2021—2025；其他年份未接入')
    if not isinstance(keyword, str) or len(keyword) > 80:
        raise ValueError('筛选词无效')
    r = requests.get(URLS[year], timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    found = []
    for t in s.find_all('table'):
        content = ''.join(t.get_text(' ', strip=True).split())
        if '常住人口' in content and '城镇' in content and ('保山市' in content or '保山' in content):
            found.append(t)
    if len(found) != 1:
        raise ValueError('未找到唯一人口数据表')
    rows = []
    for tr in found[0].find_all('tr'):
        cells = [{'text': ' '.join(c.get_text(' ', strip=True).split()), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    q = ''.join(keyword.split())
    filtered = [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if q and q in ''.join((''.join(c['text'].split()) for c in row))]
    return {'source': '保山市统计局各县（市、区）主要人口数据', 'year': year, 'source_url': URLS[year], 'index_url': INDEX, 'headers': rows[:3], 'rows': filtered if keyword else [{'row': i, 'cells': row} for i, row in enumerate(rows, 1)], 'note': '保留原表文本和合并表头。各年指标、人口单位和统计口径可能不同；2017/2019表包含常住人口人、2021—2025表以万人为主，须核实原表和人口普查修订，不将缺项当零。'}
