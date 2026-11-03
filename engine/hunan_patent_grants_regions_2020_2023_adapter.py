"""Hunan annual prefecture patent grants, official 2020–2023 tables."""
import release_runtime
import hashlib, re, subprocess
from bs4 import BeautifulSoup
BASE = 'https://amr.hunan.gov.cn/amr/ztx/zscqqsx/zstjfx/zsnb/'
SOURCES = {2020: '202104/t20210406_16266273.html', 2021: '202204/t20220406_22730258.html', 2022: '202301/t20230116_29184729.html', 2023: '202401/t20240119_32629377.html'}
CITIES = ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西州', '其他', '全省']
COLUMNS = ['地区', '授权量', '发明', '实用新型', '外观设计', '大专院校', '科研单位', '工矿企业', '机关团体', '职务总计', '个人']

def catalog():
    return [{'year': y, 'url': BASE + p} for y, p in SOURCES.items()]

def table(year, region=''):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2020–2023')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    url = BASE + SOURCES[year]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '3000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('HTTPS source read failed: curl status ' + str(p.returncode))
    raw = p.stdout
    if len(raw) > 3000000:
        raise ValueError('response too large')
    soup = BeautifulSoup(raw, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('unexpected table count')
    rows = []
    for tr in tables[0].find_all('tr'):
        cells = [''.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)]
        if not cells or cells[0] not in CITIES:
            continue
        if len(cells) != 11 or any((not re.fullmatch('\\d+', v) for v in cells[1:])):
            raise ValueError('unexpected numeric row')
        nums = list(map(int, cells[1:]))
        if nums[0] != sum(nums[1:4]) or nums[8] != sum(nums[4:8]) or nums[0] != nums[8] + nums[9]:
            raise ValueError('inconsistent classification total')
        rows.append(dict(zip(COLUMNS, cells)))
    if [x['地区'] for x in rows] != CITIES:
        raise ValueError('missing or reordered regions')
    for key in COLUMNS[1:]:
        if sum((int(x[key]) for x in rows[:-1])) != int(rows[-1][key]):
            raise ValueError('regional and province totals differ')
    return {'source': '湖南省市场监督管理局（知识产权局）', 'year': year, 'source_url': url, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'unit': '件', 'columns': COLUMNS, 'rows': [x for x in rows if region in x['地区']], 'note': '各市州及其他类别的年度专利授权量，分发明、实用新型、外观设计和职务/个人；申请人分类沿用原表名称。授权量不是PCT申请受理量，统计范围及口径以原网页为准。'}
