"""2024 年国家社科基金重大项目正式名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
SOURCE = 'https://download.people.com.cn/dangwang/one17340010291.pdf'
ANNOUNCEMENT = 'https://www.nopss.gov.cn/n1/2024/1212/c431028-40380981.html'

def nopss_major_2024(keyword=''):
    rows = json.loads((ROOT / '2024正式名单.json').read_text(encoding='utf8'))
    if len(rows) != 326 or len({r['批准号'] for r in rows}) != 326:
        raise ValueError('快照记录数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': SOURCE, 'announcement_url': ANNOUNCEMENT} for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()]
