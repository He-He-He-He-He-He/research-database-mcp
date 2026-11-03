"""河北省2024科技经费公报分地区原表。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://tjj.hebei.gov.cn/hbstjj/sj/tjgb/101758793797446.html'
REGIONS = '全省 石家庄市 唐山市 秦皇岛市 邯郸市 邢台市 保定市 张家口市 承德市 沧州市 廊坊市 衡水市 定州市 辛集市'.split()

def data(region=None):
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = s.find_all('table')
    matches = []
    for t in tables:
        h = ''.join(t.get_text(' ', strip=True).split())
        if '2024年R&D经费' in h and '修订后2023年R&D经费投入强度' in h:
            matches.append(t)
    if len(matches) != 1:
        raise ValueError('分地区表格未唯一定位')
    rows = []
    for tr in matches[0].find_all('tr'):
        c = [''.join(x.get_text(' ', strip=True).split()) for x in tr.find_all(['td', 'th'], recursive=False)]
        if len(c) != 4 or c[0] not in REGIONS:
            continue
        if not all((re.fullmatch('\\d+(?:\\.\\d+)?', v) for v in c[1:])):
            raise ValueError('数字内容异常')
        rows.append({'地区': c[0], '2024年R&D经费_亿元': float(c[1]), '2024年R&D投入强度_百分比': float(c[2]), '修订后2023年R&D投入强度_百分比': float(c[3])})
    if [x['地区'] for x in rows] != REGIONS:
        raise ValueError('地区数或次序异常')
    if region:
        rows = [x for x in rows if x['地区'] == region]
    return {'source': '河北省统计局、科技厅和财政厅《2024年河北省科技经费投入统计公报》', 'source_url': URL, 'table': '附表2 2024年及2023年各地区研究与试验发展（R&D）经费情况', 'note': '2024有经费金额（亿元）及强度（%）；2023仅有按照第五次全国经济普查后GDP最终数修订的强度。按原表保留定州、辛集等地区；不要假定与其他行完全互斥或相加等于全省。', 'rows': rows}
