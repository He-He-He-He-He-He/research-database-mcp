"""2013—2021 国家社科基金艺术学重大项目公开资料快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
ARCHIVE = 'https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202201/P020220216531003417704.xlsx'
ANNOUNCEMENT_2021 = 'https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202107/t20210705_926208.html'
COUNTS = {2013: 5, 2014: 6, 2015: 4, 2016: 10, 2017: 9, 2018: 24, 2019: 27, 2020: 28, 2021: 27}

def mct_art_major_2013_2021(year, keyword=''):
    year = int(year)
    if year not in COUNTS:
        raise ValueError('仅支持 2013—2021 年')
    rows = json.loads((ROOT / f'{year}重大.json').read_text(encoding='utf-8'))
    expected = COUNTS[year]
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    source = ANNOUNCEMENT_2021 if year == 2021 else ARCHIVE
    edition = '2021 年立项公告正文表' if year == 2021 else '2022 年发布的历年项目汇编'
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source, 'source_edition': edition} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
