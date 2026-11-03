"""2025 年国家社科基金重大项目正式名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
SOURCE = 'https://download.people.com.cn/yunying4/sixteen17661409841.pdf'
ANNOUNCEMENT = 'https://www.nopss.gov.cn/n1/2025/1219/c431028-40628359.html'

def nopss_major_2025(keyword=''):
    rows = json.loads((ROOT / '2025正式名单.json').read_text(encoding='utf8'))
    if len(rows) != 300 or len({r['批准号'] for r in rows}) != 300:
        raise ValueError('快照记录数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': SOURCE, 'announcement_url': ANNOUNCEMENT} for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()]
