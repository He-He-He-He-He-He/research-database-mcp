"""教育部 2010 年人文社科一般项目正式立项公告附件快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部人文社科一般项目2010'
ANNOUNCEMENT = 'https://www.sinoss.net/c/2010-11-23/550056.shtml'
COUNTS = {1: 4611, 2: 207, 3: 48, 4: 7}
NAMES = {1: '规划基金、青年基金、自筹经费', 2: '西部和边疆地区', 3: '新疆', 4: '西藏'}
IDS = ['20101116045741753', '20101116045807270', '20101116045818124', '20101116045830161']

def moe_humanities_general_projects_2010(keyword='', attachment=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    if attachment is not None:
        attachment = int(attachment)
        if attachment not in COUNTS:
            raise ValueError('附件编号须为 1—4')
    rows = json.loads((ROOT / '2010立项名单.json').read_text(encoding='utf8'))
    if len(rows) != sum(COUNTS.values()):
        raise ValueError('快照总数异常')
    needle = ''.join(keyword.split()).casefold()
    found = [r for r in rows if (attachment is None or r['附件'] == attachment) and needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'status': '2010 年正式立项公告快照，项目当前状态需另核', 'source_url': ANNOUNCEMENT, 'attachment_names': NAMES, 'pdf_urls': {str(i): f'https://www.sinoss.net/uploadfile/2010/1116/{v}.pdf' for i, v in enumerate(IDS, 1)}, 'filtered_total': len(found), 'page': page, 'page_size': page_size, 'results': found[(page - 1) * page_size:page * page_size]}
