"""2019—2021 年国家社科基金重大项目名单高校转载表快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金重大项目'
COUNTS = {2019: 364, 2020: 338, 2021: 348}
SOURCE = {2019: 'https://www.shupl.edu.cn/_upload/article/files/dc/1b/4584fbbb4c339c56705aa716de30/185e9689-bb0c-47eb-b16f-b9fb8b90b8f0.xlsx', 2020: 'https://www.shupl.edu.cn/_upload/article/files/dc/1b/4584fbbb4c339c56705aa716de30/8a3c870e-aa4b-4b3b-b772-0eb6cf5f0d49.xlsx', 2021: 'https://www.shupl.edu.cn/_upload/article/files/dc/1b/4584fbbb4c339c56705aa716de30/9d146c7f-0069-4d56-a96f-daa596826509.xls'}

def nopss_major_2019_2021(year, keyword=''):
    year = int(year)
    if year not in COUNTS:
        raise ValueError('仅支持 2019—2021 年')
    rows = json.loads((ROOT / f'{year}正式名单.json').read_text(encoding='utf8'))
    if len(rows) != COUNTS[year] or len({r['批准号'] for r in rows}) != COUNTS[year]:
        raise ValueError('快照记录数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': SOURCE[year], 'source_edition': '上海政法学院科研处转载名单'} for r in rows if needle in ''.join((''.join(str(v or '').split()) for v in r.values())).casefold()]
