"""教育部高校思政课教师研究专项一般项目 2022—2025 年正式名单。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部思政课教师研究专项'
SOURCES = {2022: ('https://www.sinoss.net/c/2022-08-18/625522.shtml', 'https://www.sinoss.net/upload/resources/file/2022/08/18/30916.pdf', 198), 2023: ('https://www.sinoss.net/c/2023-10-19/635504.shtml', 'https://www.sinoss.net/upload/resources/file/2023/10/19/34755.pdf', 206), 2024: ('https://www.sinoss.net/c/2024-09-14/642779.shtml', 'https://www.sinoss.net/upload/resources/file/2024/09/14/37635.pdf', 200), 2025: ('https://www.sinoss.net/c/2025-12-03/661261.shtml', 'https://www.sinoss.net/upload/resources/file/2025/12/03/46573.pdf', 198)}

def moe_ideological_teaching_projects(keyword='', year=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码应大于零，每页 1—100 条')
    if year is not None:
        year = int(year)
        if year not in SOURCES:
            raise ValueError('快照仅覆盖 2022—2025 年')
    rows = json.loads((ROOT / '2022-2025立项名单.json').read_text(encoding='utf8'))
    if len(rows) != sum((v[2] for v in SOURCES.values())):
        raise ValueError('快照总行数异常')
    needle = ''.join(keyword.split()).casefold()
    matches = [r for r in rows if (year is None or r['年度'] == year) and needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'status': '当年公告的正式立项名单快照，项目后续状态请另行核实', 'source_years': list(SOURCES), 'sources': {str(y): {'announcement': v[0], 'pdf': v[1], 'count': v[2]} for y, v in SOURCES.items() if year is None or year == y}, 'filtered_total': len(matches), 'page': page, 'page_size': page_size, 'results': matches[(page - 1) * page_size:page * page_size]}
