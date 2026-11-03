"""国家能源局 2025 年前三季度各省光伏并网容量原表。"""
import release_runtime
import argparse
import json
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.nea.gov.cn/20251112/35126d06a151461882b61d0a2e5706a6/c.html'
COLUMNS = ['地区', '前三季度新增并网容量', '新增其中集中式光伏电站', '新增其中分布式光伏', '新增其中户用光伏', '9月底累计并网容量', '累计其中集中式光伏电站', '累计其中分布式光伏', '累计其中户用光伏']

def pv_statistics(region=None, timeout=15):
    if region is not None and (not isinstance(region, str) or len(region) > 20):
        raise ValueError('地区无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    text = s.get_text(' ', strip=True)
    if '单位：万千瓦' not in text or '户用光伏包括自然人户用和非自然人户用' not in text:
        raise ValueError('原表单位或注释已变化')
    tables = s.find_all('table')
    if len(tables) != 1:
        raise ValueError('原表结构已变化')
    rows = []
    for tr in tables[0].find_all('tr')[3:]:
        cells = [td.get_text(' ', strip=True) for td in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) != 9 or not all((re.fullmatch('\\d+(?:\\.\\d+)?', v) for v in cells[1:])):
            raise ValueError('表格数据结构异常')
        rows.append(dict(zip(COLUMNS, cells)))
    if len(rows) != 32 or rows[0]['地区'] != '总计':
        raise ValueError('地区或总计数量异常')
    if region is not None:
        rows = [x for x in rows if x['地区'] == region]
    return {'source': '国家能源局', 'source_url': URL, 'period': '2025年前三季度及9月底', 'unit': '万千瓦', 'columns': COLUMNS, 'rows': rows, 'notes': ['数据来源：国家可再生能源中心、中国电力企业联合会。', '户用光伏包括自然人户用和非自然人户用。'], 'note': '新增为前三季度并网容量，累计为9月底存量；分类有包含关系，不能重复相加。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--region')
    a = p.parse_args()
    print(json.dumps(pv_statistics(a.region), ensure_ascii=False, indent=2))
