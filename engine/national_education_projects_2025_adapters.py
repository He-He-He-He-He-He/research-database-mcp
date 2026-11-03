"""全国教育科学规划 2025 年正式立项名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '全国教育科学规划'
ANNOUNCEMENT = 'https://onsgep.moe.edu.cn/post/view/1803'
PDF = 'https://onsgep.moe.edu.cn/storage/onsgep/onsgep/cn/article/2025/08/4ad43d128d9e236af5af713f0df00722.pdf'

def education_projects_2025(keyword='', page=1, page_size=20):
    page = int(page)
    page_size = int(page_size)
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码必须大于零，每页 1—100 条')
    rows = json.loads((ROOT / '2025年度正式立项名单.json').read_text(encoding='utf8'))
    if len(rows) != 539 or [r['序号'] for r in rows] != list(range(1, 540)) or len({r['批准号'] for r in rows}) != 539:
        raise ValueError('快照数量、序号或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    matches = [r for r in rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'source_url': ANNOUNCEMENT, 'pdf_url': PDF, 'source_total': len(rows), 'filtered_total': len(matches), 'page': page, 'page_size': page_size, 'results': matches[(page - 1) * page_size:page * page_size]}
