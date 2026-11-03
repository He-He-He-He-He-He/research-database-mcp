"""国家社科基金艺术学 2019—2021 年年度项目公开原表快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2019: ('https://www.mct.gov.cn/whzx/bnsj/whkjs/201909/W020191009614942055042.xls', 214), 2020: ('https://www.mct.gov.cn/whzx/bnsj/whkjs/202010/W020201010566038340508.xls', 214), 2021: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202108/P020210820404196513293.xls', 221)}

def mct_art_research_2019_2021(year, keyword=''):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2019—2021 年度')
    source, expected = SOURCES[year]
    rows = json.loads((ROOT / f'{year}.json').read_text(encoding='utf-8'))
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
