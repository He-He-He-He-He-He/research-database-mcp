"""宁夏统计局科技统计公报正文：五市R&D经费。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URLS = {2021: 'https://tj.nx.gov.cn/tjsj_htr/tjgb_htr/202209/t20220908_3750227.html', 2022: 'https://tj.nx.gov.cn/zzb/tjgb/202309/t20230920_4276634.html', 2023: 'https://tj.nx.gov.cn/zzb/tjgb/202410/t20241030_4712850.html', 2024: 'https://tj.nx.gov.cn/zzb/tjgb/202510/t20251009_5047369.html'}
CITIES = '银川市 石嘴山市 吴忠市 固原市 中卫市'.split()

def data(year, city=None):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('仅支持2021—2024')
    if city is not None and city not in CITIES:
        raise ValueError('城市名称不存在')
    r = requests.get(URLS[year], timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    t = ''.join(s.stripped_strings)
    t = ''.join(t.split())
    if f'{year}年宁夏科技统计公报' not in t:
        raise ValueError('公报标题异常')
    if '分地区看' not in t:
        raise ValueError('找不到分地区段落')
    section = t.split('分地区看', 1)[1].split('附表', 1)[0]
    out = []
    for c in CITIES:
        m = re.search(re.escape(c) + '[^；。\\d]{0,50}(\\d+(?:\\.\\d+)?)亿元', section)
        if not m:
            raise ValueError(f'{c}经费文字不完整')
        out.append({'地区': c, '年份': year, '研发经费_亿元': float(m.group(1))})
    if city:
        out = [r for r in out if r['地区'] == city]
    return {'source': f'宁夏统计局和科技厅《{year}年宁夏科技统计公报》', 'url': URLS[year], 'note': '提取公报正文分地区研发经费，单位亿元；2024正文仅保留一位小数，其他年份保留两位。地区数与年度口径、历史修订请核对原公报；不含附表图片中的区县指标。', 'rows': out}
