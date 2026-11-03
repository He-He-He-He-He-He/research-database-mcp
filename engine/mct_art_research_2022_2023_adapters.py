"""国家社科基金艺术学 2022—2023 年年度项目公开表快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2022: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202210/P020221009358354588229.xls', 219), 2023: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202310/P020231009407194634928.xls', 235)}

def mct_art_research_2022_2023(year, keyword=''):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2022、2023 年度')
    source, expected = SOURCES[year]
    rows = json.loads((ROOT / f'{year}.json').read_text(encoding='utf-8'))
    if len(rows) != expected or [r['序号'] for r in rows] != list(range(1, expected + 1)) or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
