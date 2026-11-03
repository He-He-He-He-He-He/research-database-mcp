"""2013、2014 年国家社科基金重大项目两批正式公布名单。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
COUNTS = {(2013, 1): 55, (2013, 2): 137, (2014, 1): 90, (2014, 2): 171}

def nopss_major_2013_2014(year, batch=None, keyword=''):
    year = int(year)
    if year not in (2013, 2014):
        raise ValueError('仅支持 2013、2014 年')
    if batch is not None:
        batch = int(batch)
        if batch not in (1, 2):
            raise ValueError('批次必须为 1 或 2')
    needle = ''.join(keyword.split()).casefold()
    result = []
    for b in (batch,) if batch else (1, 2):
        rows = json.loads((ROOT / f'{year}第{b}批正式名单.json').read_text(encoding='utf8'))
        if len(rows) != COUNTS[year, b] or [x['序号'] for x in rows] != list(range(1, COUNTS[year, b] + 1)):
            raise ValueError('快照数量或序号异常')
        result.extend((r for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()))
    return result
