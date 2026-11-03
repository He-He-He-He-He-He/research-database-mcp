"""台湾地区都市及区域发展统计汇编：官方 CSV 查询。"""
import release_runtime
import csv, html, io, re
from urllib.parse import urlsplit
import requests
TABLES = {'population': ('6326', '土地面积、户数、人口及年龄结构'), 'urban_area': ('6489', '都市计划区面积与人口'), 'sewage': ('6513', '污水处理率'), 'water': ('6497', '自来水普及率及用水量'), 'revenue': ('6518', '各县市政府岁入决算数'), 'expenditure': ('6519', '各县市政府岁出决算数'), 'income': ('6520', '平均每户全年经常性收入及支出'), 'housing': ('6507', '住宅支出'), 'construction': ('6699', '房屋营建工程面积'), 'school': ('6516', '各级学校数'), 'waste': ('6511', '垃圾清运处理状况'), 'park': ('95319', '每万人享有公园绿地面积'), 'transport': ('6500', '交通费用汽车及机车数'), 'cultural_events': ('6517', '艺文展演活动统计'), 'heritage': ('95321', '文化资产统计'), 'elderly_care': ('6505', '老人长期照护机构'), 'roads': ('6499', '公路长度与面积'), 'population_change': ('6328', '人口成长')}

def catalog():
    return [{'table': k, 'name': name, 'metadata_url': 'https://data.gov.tw/dataset/' + id} for k, (id, name) in TABLES.items()]

def _read(url, cap):
    with requests.get(url, timeout=(12, 30), allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise RuntimeError('官方页面或资源发生重定向')
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > cap:
                raise RuntimeError('官方响应超过大小上限')
            chunks.append(chunk)
        return b''.join(chunks)

def query(table, region='', limit=100):
    if table not in TABLES:
        raise ValueError('未知统计表')
    if not isinstance(region, str) or len(region) > 100:
        raise ValueError('地区须为不超过100字的字符串')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit 须为1至500')
    id, name = TABLES[table]
    page = 'https://data.gov.tw/dataset/' + id
    body = _read(page, 3000000).decode('utf-8')
    m = re.search('https://ws\\.ndc\\.gov\\.tw/Download\\.ashx\\?[^"<>\\s]+', body)
    if not m:
        raise RuntimeError('政府目录未显示 NDC CSV 地址')
    url = html.unescape(m.group())
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'ws.ndc.gov.tw' or p.path != '/Download.ashx' or ('icon=.csv' not in url.lower()):
        raise RuntimeError('未识别官方 CSV 地址')
    raw = _read(url, 8000000)
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
    if not rows or '年' not in rows[0] or '地區' not in rows[0] or (len(set(rows[0])) != len(rows[0])) or any((len(x) != len(rows[0]) for x in rows)):
        raise RuntimeError('CSV 表头或行列数异常')
    allrows = [dict(zip(rows[0], row)) for row in rows[1:]]
    matched = [row for row in allrows if not region or region in row['地區']]
    return {'source': '台湾地区都市及区域发展统计汇编', 'title': name, 'table': table, 'metadata_url': page, 'csv_url': url, 'fields': rows[0], 'total_rows': len(allrows), 'matched_rows': len(matched), 'items': matched[:limit], 'note': '每次获取官网当前 CSV 后本地地区包含匹配；地区含合计与下级地区，勿重复加总。各表当前年度和字段口径可能不同，原值字符串未转换；CSV 未提供单位时需查原始统计汇编。' + (' 自来水表的供水人口自来水普及率字段名称与数据疑似不一致，须核对原汇编。' if table == 'water' else '') + (' 收入表与住宅表同地区住宅支出占比略有差异，须核对统计口径。' if table in ('income', 'housing') else '') + (' 期中人口的单位未核清，须查原汇编。' if table == 'waste' else '')}
