"""Hunan official prefecture effective invention patents, December 2023–2025."""
import release_runtime
import hashlib, re, subprocess
from bs4 import BeautifulSoup
SOURCES = {2023: 'https://amr.hunan.gov.cn/amr/sjx/tjfxx/202401/t20240118_32629157.html', 2024: 'https://amr.hunan.gov.cn/amr/sjx/tjfxx/202501/t20250120_33569785.html', 2025: 'https://amr.hunan.gov.cn/amr/ztx/zscqqsx/zstjfx/zsyb/202601/t20260126_33900880.html'}
CITIES = ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西州', '其他', '全省']

def catalog():
    return [{'year': y, 'url': u, 'population_reference_year': y - 1} for y, u in SOURCES.items()]

def table(year, region=''):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2023–2025')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '3000000', SOURCES[year]], capture_output=True, timeout=35)
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
    cols = ['地区', '有效发明专利量', '高校', '科研', '企业', '机构', '职务总计', '个人', '常住人口_万人', '专利密度_每万人', '排名']
    for tr in tables[0].find_all('tr'):
        cells = [''.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)]
        if not cells or cells[0] not in CITIES:
            continue
        if len(cells) != 11 or any((not re.fullmatch('\\d+', v) for v in cells[1:8])):
            raise ValueError('unexpected numeric row')
        if int(cells[1]) != int(cells[6]) + int(cells[7]) or int(cells[6]) != sum((int(v) for v in cells[2:6])):
            raise ValueError('inconsistent classification total')
        rows.append(dict(zip(cols, cells)))
    if [x['地区'] for x in rows] != CITIES:
        raise ValueError('missing or reordered regions')
    for key in cols[1:8]:
        if sum((int(x[key]) for x in rows[:-1])) != int(rows[-1][key]):
            raise ValueError('regional and province totals differ')
    descriptions = {'高校': '高等院校' if year == 2025 else '大专院校', '科研': '科研机构' if year == 2025 else '科研单位', '企业': '企业' if year == 2025 else '工矿企业', '机构': '事业单位' if year == 2025 else '机关团体'}
    return {'source': '湖南省市场监督管理局（知识产权局）', 'year': year, 'source_url': SOURCES[year], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'unit': '件', 'category_original_names': descriptions, 'population_reference_year': year - 1, 'rows': [x for x in rows if region in x['地区']], 'note': '12月末有效发明专利存量，不是当年申请或授权量。人口分母来自湖南省统计局上一年度统计公报；各年申请人类别名称有变化，原名见category_original_names，跨年可比性须核原表。'}
