"""教育部 2022—2025 年人文社科一般项目正式立项公告附件快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部人文社科一般项目'
SOURCES = {2022: ('2022-09-26', '626211', '2022/09/26', 31003, (2616, 165, 19, 1, 30, 208)), 2023: ('2023-10-19', '635529', '2023/10/19', 34763, (3028, 200, 20, 3, 27, 202)), 2024: ('2024-09-14', '642760', '2024/09/14', 37629, (3378, 234, 13, 2, 31, 202)), 2025: ('2025-12-03', '661263', '2025/12/03', 46574, (2817, 188, 13, 1, 36, 212))}
GROUPS = {1: '规划基金、青年基金、自筹经费', 2: '西部和边疆地区', 3: '新疆', 4: '西藏', 5: '中国特色社会主义理论体系研究专项', 6: '高校辅导员研究专项'}

def moe_humanities_general_projects(keyword='', year=None, attachment=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    if year is not None:
        year = int(year)
        if year not in SOURCES:
            raise ValueError('快照仅覆盖 2022—2025 年')
    if attachment is not None:
        attachment = int(attachment)
        if attachment not in GROUPS:
            raise ValueError('附件编号须为 1—6')
    rows = json.loads((ROOT / '2022-2025立项名单.json').read_text(encoding='utf8'))
    if len(rows) != sum((sum(x[4]) for x in SOURCES.values())):
        raise ValueError('快照总数异常')
    needle = ''.join(keyword.split()).casefold()
    found = [r for r in rows if (year is None or r['年度'] == year) and (attachment is None or r['附件'] == attachment) and (needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold())]
    return {'status': '正式立项公告快照，项目当前状态须另核', 'coverage': '2022—2025 年各年度一般项目通知的六份附件', 'groups': GROUPS, 'filtered_total': len(found), 'page': page, 'page_size': page_size, 'results': found[(page - 1) * page_size:page * page_size], 'sources': {str(y): {'announcement': f'https://www.sinoss.net/c/{date}/{article}.shtml', 'pdfs': [f'https://www.sinoss.net/upload/resources/file/{folder}/{first + i - 1}.pdf' for i in range(1, 7)], 'counts': counts} for y, (date, article, folder, first, counts) in SOURCES.items() if year is None or year == y}}
