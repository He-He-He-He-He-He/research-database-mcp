"""国家统计局2023–2025年分省早稻播种面积、产量和单产原表。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2023: 'https://www.stats.gov.cn/sj/zxfb/202308/t20230823_1942209.html', 2024: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202408/t20240823_1956083.html', 2025: 'https://www.stats.gov.cn/sj/zxfbhjd/202508/t20250822_1960862.html'}

def table(year, region=None):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('支持2023–2025年')
    if region is not None and (not isinstance(region, str) or not 1 <= len(region) <= 30):
        raise ValueError('地区无效')
    url = URLS[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    candidates = []
    for t in s.find_all('table'):
        rows = [[''.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in t.find_all('tr')]
        if len(rows) >= 32 and len(rows[0]) == 4 and (rows[1][0] == '全国总计') and ('播种面积' in ''.join(rows[0])):
            candidates.append(rows)
    if not candidates:
        raise ValueError('未找到分省早稻数据表，可能遇到站点验证或结构变化')
    if any((x != candidates[0] for x in candidates[1:])):
        raise ValueError('重复表格不一致')
    rows = [x for x in candidates[0][1:] if len(x) == 4 and x[0]]
    if region is not None:
        rows = [x for x in rows if x[0] == ''.join(region.split())]
    return {'source': '国家统计局', 'source_url': url, 'year': year, 'headers': candidates[0][0], 'rows': rows, 'source_notes': [x[0] for x in candidates[0] if len(x) == 1 and x[0].startswith('注')], 'note': '数据由以省为总体的抽样调查推算；未种植或未列值为空，不等于零。2025年产量与单位面积产量列顺序不同，使用原表头，不应按固定列推断。'}
