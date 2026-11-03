"""Official Hunan prefecture PCT patent applications accepted, 2020–2025."""
import release_runtime
import hashlib, re, subprocess
from bs4 import BeautifulSoup
BASE = 'https://amr.hunan.gov.cn/amr/ztx/zscqqsx/zstjfx/zsnb/'
SOURCES = {2020: '202104/t20210406_16266092.html', 2021: '202204/t20220406_22730263.html', 2022: '202301/t20230116_29184732.html', 2023: '202401/t20240119_32629382.html', 2024: '202501/t20250120_33569779.html', 2025: '202601/t20260126_33900882.html'}
CITIES = ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西州', '全省']

def catalog():
    return [{'year': y, 'url': BASE + p} for y, p in SOURCES.items()]

def table(year, region=''):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2020–2025')
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
        if len(cells) < 2 or not re.fullmatch('\\d+', cells[1]) or (len(cells) > 2 and cells[2] and (not re.fullmatch('\\d+', cells[2]))):
            raise ValueError('unexpected numeric row')
        rows.append({'region': cells[0], 'accepted': cells[1], 'rank': cells[2] if len(cells) > 2 else ''})
    if [x['region'] for x in rows] != CITIES or sum((int(x['accepted']) for x in rows[:-1])) != int(rows[-1]['accepted']):
        raise ValueError('missing rows or total mismatch')
    return {'source': '湖南省市场监督管理局（知识产权局）', 'year': year, 'source_url': url, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'unit': '件', 'total_rows': len(rows), 'rows': [x for x in rows if region in x['region']], 'note': '原表说明国家知识产权局规划发展司数据包含已缴费和未缴费PCT申请且为动态数据；2020原表特别说明以往统计只包括已缴费数据。排名及并列按原表，统计的是申请受理量，不是授权量。'}
