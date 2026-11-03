"""在京中央单位及直属机构广播电视节目制作经营许可名单快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '广电节目制作许可'
SOURCE = 'https://www.nrta.gov.cn/art/2026/1/5/art_113_72262.html'

def nrta_production_license_2025(keyword='', page=1, page_size=20):
    page = int(page)
    page_size = int(page_size)
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码必须大于零，每页 1—100 条')
    rows = json.loads((ROOT / '在京中央单位2025年末.json').read_text(encoding='utf8'))
    if len(rows) != 97 or [r['序号'] for r in rows] != list(range(1, 98)):
        raise ValueError('快照数量或序号异常')
    needle = ''.join(keyword.split()).casefold()
    matching = [r for r in rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'source_url': SOURCE, 'cutoff': '2025-12-31', 'source_total': len(rows), 'filtered_total': len(matching), 'page': page, 'page_size': page_size, 'results': matching[(page - 1) * page_size:page * page_size]}
