"""2012 年国家社科基金重大项目第一、第四批名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
COUNTS = {1: 35, 4: 41}

def nopss_major_2012(batch, keyword=''):
    batch = int(batch)
    if batch not in COUNTS:
        raise ValueError('仅支持第一批及第四批；第二、三批未接入')
    rows = json.loads((ROOT / f'2012第{batch}批正式名单.json').read_text(encoding='utf8'))
    if len(rows) != COUNTS[batch] or [r['序号'] for r in rows] != list(range(1, COUNTS[batch] + 1)):
        raise ValueError('快照数量或序号异常')
    needle = ''.join(keyword.split()).casefold()
    return [r for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()]
