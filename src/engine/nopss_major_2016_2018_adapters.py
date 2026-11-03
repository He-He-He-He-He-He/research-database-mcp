"""2016—2018 国家社科基金重大项目高校转载表快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
COUNTS = {2016: 239, 2017: 331, 2018: 339}
SOURCES = {2016: 'https://www.fafu.edu.cn/_upload/article/files/7c/c1/16c25ea441f3a7462f5ed014a7d6/2445f7fc-dddf-4dd3-87a7-75716d28afd7.xls', 2017: 'https://skc.seu.edu.cn/_upload/article/files/26/b3/04f82bd94de298f778ab6b2d3431/641109be-e382-4fd8-9ceb-dfe8ab37d828.xls', 2018: 'https://www.shupl.edu.cn/_upload/article/files/dc/1b/4584fbbb4c339c56705aa716de30/73aeb297-b23c-4f67-9f7d-76089ffaf1f5.xlsx'}

def nopss_major_2016_2018(year, keyword=''):
    year = int(year)
    if year not in COUNTS:
        raise ValueError('仅支持 2016—2018 年')
    rows = json.loads((ROOT / f'{year}正式名单.json').read_text(encoding='utf8'))
    if len(rows) != COUNTS[year] or [r['序号'] for r in rows] != list(range(1, COUNTS[year] + 1)):
        raise ValueError('快照序号或数量异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': SOURCES[year], 'source_edition': '高校转载表或汇编'} for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()]
