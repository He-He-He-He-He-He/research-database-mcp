"""MOHRSS minimum wages by province: official China Job website snapshots."""
import release_runtime
import hashlib, re
import requests
from bs4 import BeautifulSoup
SOURCES = {'2022-04-01': 'https://chinajob.mohrss.gov.cn/h5/c/2022-04-08/347439.shtml', '2023-10-01': 'https://chinajob.mohrss.gov.cn/h5/c/2023-10-19/388883.shtml'}
PROVINCES = ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江', '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南', '广东', '其中：深圳', '广西', '海南', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']

def catalog():
    return [{'as_of': date, 'url': url} for date, url in SOURCES.items()]

def table(as_of, region=''):
    if not isinstance(as_of, str) or as_of not in SOURCES:
        raise ValueError('available dates: 2022-04-01, 2023-10-01')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    with requests.get(SOURCES[as_of], stream=True, timeout=(10, 30), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        content = bytearray()
        for chunk in r.iter_content(65536):
            content.extend(chunk)
            if len(content) > 3000000:
                raise ValueError('response too large')
    raw = bytes(content)
    soup = BeautifulSoup(raw, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('unexpected number of tables')
    rows = []
    for tr in tables[0].find_all('tr'):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if len(cells) != 9:
            continue
        raw_cells = [c.get_text(' ', strip=True) for c in cells]
        clean = [''.join(s.split()) for s in raw_cells]
        if clean[0] not in PROVINCES:
            continue
        if any((v and (not re.fullmatch('\\d+(?:\\.\\d+)?', v)) for v in clean[1:])):
            raise ValueError('unrecognized numeric value')
        rows.append({'region': clean[0], 'month_yuan': clean[1:5], 'hour_yuan': clean[5:9], 'raw_cells': raw_cells})
    if [r['region'] for r in rows] != PROVINCES:
        raise ValueError('table missing or rearranged region rows')
    return {'source': '中国就业网转载人力资源和社会保障部最低工资表', 'as_of': as_of, 'source_url': SOURCES[as_of], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'unit': '元', 'total_rows': len(rows), 'rows': [x for x in rows if region in x['region']], 'note': '为截至指定日期的快照，不代表当前标准；省内各档适用地区需查询当地规定。空字符串保留原表空白；数值仅去除单元格内排版空格，原始文本另存 raw_cells。深圳为广东其中项，不可当作单独省份汇总。'}
