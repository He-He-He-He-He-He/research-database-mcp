"""2026 全国教育科学规划拟立项公示名单快照；不是最终立项。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '全国教育科学规划'
ANNOUNCEMENT = 'https://onsgep.moe.edu.cn/post/view/1874'
PDF = 'https://onsgep.moe.edu.cn/storage/onsgep/onsgep/cn/article/2026/10/beda358020e72eb8b8608f91d133727f.pdf'

def education_projects_2026_proposed(keyword='', page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码必须大于零，每页 1—100 条')
    rows = json.loads((ROOT / '2026年度拟立项公示名单.json').read_text(encoding='utf8'))
    if len(rows) != 560 or [r['序号'] for r in rows] != list(range(1, 561)):
        raise ValueError('公示快照数量或序号异常')
    needle = ''.join(keyword.split()).casefold()
    matches = [r for r in rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'status': '拟立项公示，非最终立项；正式结果可能变化', 'notice_date': '2026-10-10', 'source_url': ANNOUNCEMENT, 'pdf_url': PDF, 'source_total': len(rows), 'filtered_total': len(matches), 'page': page, 'page_size': page_size, 'results': matches[(page - 1) * page_size:page * page_size]}
