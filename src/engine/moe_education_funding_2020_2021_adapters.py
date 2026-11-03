"""2020、2021 年全国教育经费统计表，保留原版分表差异。"""
import release_runtime
from pathlib import Path
import re
ROOT = Path(__file__).parent
SOURCES = {2020: ('https://www.moe.gov.cn/srcsite/A05/s3040/202111/t20211130_583343.html', 'https://www.moe.gov.cn/srcsite/A05/s3040/202111/W020211130306990511931.doc'), 2021: ('https://www.moe.gov.cn/srcsite/A05/s3040/202212/t20221230_1037263.html', 'https://www.moe.gov.cn/srcsite/A05/s3040/202212/W020221230530014152191.doc')}
KINDS = {'表二': '生均一般公共预算教育经费', '表三': '生均一般公共预算教育事业费支出', '表四': '生均一般公共预算公用经费支出'}
LEVELS = (('幼儿园', '普通小学', '普通初中'), ('普通高中', '中等职业学校', '普通高等学校'))

def education_funding_2020_2021(year, table=2, region='', level=''):
    """返回表 1 地区预算或表 2—4 各教育阶段生均金额与增幅。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2020 或 2021')
    if table not in (1, 2, 3, 4):
        raise ValueError('table 应为 1 至 4')
    lines = [x.strip() for x in (ROOT / f'{year}年全国教育经费执行情况统计表_提取文本.txt').read_text(encoding='utf-8').replace('\x07', '\n').splitlines() if x.strip()]
    section = None
    counts = {}
    rows = []
    num = re.compile('^-?\\d+(?:\\.\\d+)?$')
    for i, line in enumerate(lines):
        if line.startswith(('表一', '表二', '表三', '表四')):
            section = line
            counts[section] = 0
            continue
        name = re.sub('\\s+', '', line)
        if not section or not (name == '全国' or name.endswith(('省', '市', '自治区'))):
            continue
        first = section.startswith('表一')
        n = 5 if first else 9 if year == 2020 else 6
        vals = lines[i + 1:i + 1 + n]
        if len(vals) != n or not all((num.fullmatch(v) for v in vals)):
            raise ValueError(f'表格行解析异常: {section} {name}')
        counts[section] += 1
        base = {'year': year, 'region': name, 'source_url': SOURCES[year][0], 'doc_url': SOURCES[year][1]}
        if first:
            d = {'budget_yi_yuan': vals[0]}
            d.update(share_public_budget_percent=vals[1], budget_growth_percent=vals[2], fiscal_recurrent_income_growth_percent=vals[3], growth_gap_percentage_points=vals[4])
            rows.append({**base, 'table': 1, **d})
        else:
            t = {'表二': 2, '表三': 3, '表四': 4}[section[:2]]
            for j, name_level in enumerate(LEVELS[1 if '（续）' in section else 0]):
                stride = 3 if year == 2020 else 2
                record = {**base, 'table': t, 'indicator': KINDS[section[:2]], 'level': name_level, 'value_yuan': vals[j * stride + (1 if year == 2020 else 0)], 'growth_percent': vals[j * stride + stride - 1]}
                if year == 2020:
                    record['previous_year_value_yuan'] = vals[j * stride]
                rows.append(record)
    if len(counts) != 7 or any((count != (31 if name.startswith('表一') else 32) for name, count in counts.items())):
        raise ValueError(f'地区行数异常: {counts}')
    region, level = (region.strip(), level.strip())
    return [r for r in rows if r['table'] == table and (not region or region in r['region']) and (not level or level in r.get('level', ''))]
