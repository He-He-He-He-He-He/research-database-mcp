"""新疆统计局2024科技经费公报：各地区修订后2023及2024强度。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://tjj.xinjiang.gov.cn/tjj/xxfb/202510/3587f95694474a0a94c8729800d5fb57.shtml'
REGIONS = '乌鲁木齐市 克拉玛依市 吐鲁番市 哈密市 昌吉州 博州 巴州 阿克苏地区 克州 喀什地区 和田地区 伊犁州直属县（市） 塔城地区 阿勒泰地区'.split()

def data(region=None):
    if region is not None and region not in REGIONS:
        raise ValueError('地区名称不在原表中')
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = s.find_all('table')
    if len(tables) != 2:
        raise ValueError('公报表格数发生变化')
    rows = []
    for tr in tables[1].find_all('tr'):
        cells = [''.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) == 4 and cells[0] in REGIONS:
            if not all((re.fullmatch('\\d+(?:\\.\\d+)?', v) for v in cells[1:])):
                raise ValueError('原表数值异常')
            rows.append({'地区': cells[0], '2024年R&D经费_万元': float(cells[1]), '2024年R&D经费投入强度_百分比': float(cells[2]), '2023年修订后R&D经费投入强度_百分比': float(cells[3])})
    if [x['地区'] for x in rows] != REGIONS:
        raise ValueError('地区数量或顺序异常')
    if region:
        rows = [row for row in rows if row['地区'] == region]
    return {'source': '新疆维吾尔自治区统计局、科技厅、教育厅《2024年新疆科技经费投入统计公报》', 'source_url': URL, 'table': '附表2：2024年及2023年各地区研究与试验发展（R&D）经费情况', 'note': '2023年仅含按第五次经济普查GDP最终数修订后的投入强度，2024年含经费金额及投入强度；经费为万元，强度为与地区生产总值之比的百分数。伊犁州行仅直属县（市），不含其他辖区。地区简称保留原表；数据口径与范围见公报。', 'rows': rows}
