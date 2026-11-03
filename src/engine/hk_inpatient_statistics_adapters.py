"""香港卫生署 2012–2024 年 ICD 章节住院病人出院及死亡人次原表。"""
import release_runtime
import argparse
import csv
import io
import json
import requests
URL = 'https://www.dh.gov.hk/datagovhk/ncdd/Inpatient%20Discharges%20and%20Deaths%20in%20Hospitals%20by%20ICD%2010th%20Revision%20Chapter,%202012%20to%202024%20(SC).csv'

def inpatient_statistics(keyword=None, timeout=15):
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('筛选词无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    lines = list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
    if len(lines) < 10 or '2012' not in lines[3] or '2024' not in lines[3]:
        raise ValueError('官方原表结构已变化')
    end = next((i for i, x in enumerate(lines) if x and x[0].startswith('注释：')), None)
    if end is None:
        raise ValueError('官方表未找到注释')
    data = [x for x in lines[6:end] if len(x) > 1 and x[1].strip()]
    if keyword is not None:
        data = [x for x in data if keyword in x[0] or keyword in x[1]]
    return {'source': '香港卫生署住院病人出院及死亡统计', 'source_url': URL, 'keyword_filter': keyword, 'title': lines[0][0], 'headers': lines[3:6], 'rows': data, 'notes': [x[0] for x in lines[end + 1:] if x and x[0].strip()], 'note': '出院及死亡为合并人次，包含日间住院，非去重患者人数；请阅读原表注释及各年度口径。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(inpatient_statistics(a.keyword), ensure_ascii=False, indent=2))
