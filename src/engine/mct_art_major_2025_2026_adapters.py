"""国家社科基金艺术学 2025—2026 重大项目官方名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2025: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202506/P020250623375215403026.xls', 17), 2026: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202607/P020260720533313137855.pdf', 24)}

def mct_art_major_2025_2026(year, keyword=''):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2025、2026 年度')
    source, expected = SOURCES[year]
    rows = json.loads((ROOT / f'{year}重大.json').read_text(encoding='utf-8'))
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
