"""2022—2023 年国家社科基金重大项目正式名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
SOURCE = {2022: 'https://download.people.com.cn/dangwang/one16704862821.pdf', 2023: 'https://download.people.com.cn/yunying2/twentyfive17037243791.pdf'}
COUNTS = {2022: 338, 2023: 333}

def nopss_major_2022_2023(year, keyword=''):
    year = int(year)
    if year not in COUNTS:
        raise ValueError('仅支持 2022、2023 年')
    rows = json.loads((ROOT / f'{year}正式名单.json').read_text(encoding='utf8'))
    if len(rows) != COUNTS[year] or len({r['批准号'] for r in rows}) != COUNTS[year]:
        raise ValueError('快照记录数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': SOURCE[year]} for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()]
