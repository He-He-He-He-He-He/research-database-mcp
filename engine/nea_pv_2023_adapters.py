"""国家能源局 2023 年各省光伏并网容量原表。"""
import release_runtime
import argparse
import json
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.nea.gov.cn/2024-02/28/c_1310765696.htm'
COLUMNS = ['地区', '全年新增并网容量', '新增其中集中式光伏电站', '新增其中分布式光伏', '新增其中户用光伏', '年底累计并网容量', '累计其中集中式光伏电站', '累计其中分布式光伏', '累计其中户用光伏']

def pv_statistics_2023(region=None, timeout=15):
    if region is not None and (not isinstance(region, str) or len(region) > 20):
        raise ValueError('地区无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    text = s.get_text(' ', strip=True)
    if '单位：万千瓦' not in text or '2023年光伏发电建设情况' not in text:
        raise ValueError('原表单位或标题已变化')
    tables = s.find_all('table')
    if len(tables) != 2:
        raise ValueError('原表结构已变化')
    rows = []
    for tr in tables[1].find_all('tr')[3:]:
        cells = [td.get_text(' ', strip=True) for td in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) != 9 or not all((not v or re.fullmatch('\\d+(?:\\.\\d+)?', v) for v in cells[1:])):
            raise ValueError('表格数据结构异常')
        rows.append(dict(zip(COLUMNS, cells)))
    if len(rows) != 33 or rows[0]['地区'] != '总计':
        raise ValueError('地区或总计数量异常')
    if region is not None:
        rows = [x for x in rows if x['地区'] == region]
    return {'source': '国家能源局', 'source_url': URL, 'period': '2023年全年及年底', 'unit': '万千瓦', 'columns': COLUMNS, 'rows': rows, 'notes': [], 'note': '新增为全年并网容量，累计为年底存量；分类有包含关系，空白保留，不推定为零。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--region')
    a = p.parse_args()
    print(json.dumps(pv_statistics_2023(a.region), ensure_ascii=False, indent=2))
