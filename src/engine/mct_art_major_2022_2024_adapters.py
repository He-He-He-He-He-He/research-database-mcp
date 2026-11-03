"""2022—2024 国家社科基金艺术学重大项目官方公开资料快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
COUNTS = {2022: 18, 2023: 16, 2024: 17}
SOURCE = {2022: 'https://yskx.mct.gov.cn/file/downloadFile/FL_da5TyJoX7UEhYsmvv.xls', 2023: 'https://yskx.mct.gov.cn/file/downloadFile/FL_dbufyZfCqDshfh8nq.xlsx', 2024: 'https://yskx.mct.gov.cn/file/downloadFile/FL_dbufyZfCqDshfh8nq.xlsx'}
ANNOUNCEMENT = {2022: 'https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202206/t20220629_934381.html', 2023: 'https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202311/t20231122_949865.html', 2024: 'https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202407/t20240708_953927.html'}

def mct_art_major_2022_2024(year, keyword=''):
    year = int(year)
    if year not in COUNTS:
        raise ValueError('仅支持 2022—2024 年')
    rows = json.loads((ROOT / f'{year}重大.json').read_text(encoding='utf-8'))
    if len(rows) != COUNTS[year] or len({row['批准号'] for row in rows}) != COUNTS[year]:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**row, 'source_url': SOURCE[year], 'announcement_url': ANNOUNCEMENT[year], 'source_edition': '2022 年正式名单原表' if year == 2022 else '2026 年发布的 2021—2025 年官方立项汇编'} for row in rows if needle in ''.join((''.join(str(v or '').split()) for v in row.values())).casefold()]
