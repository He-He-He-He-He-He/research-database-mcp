"""教育部 2012 年人文社科一般项目正式立项公告附件快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部人文社科一般项目2012'
ANNOUNCEMENT = 'https://www.sinoss.net/c/2012-03-14/550080.shtml'
COUNTS = {1: 3961, 2: 131, 3: 58, 4: 11, 5: 121, 6: 162, 7: 18, 8: 8, 9: 6}
NAMES = {1: '规划基金、青年基金、自筹经费', 2: '西部和边疆地区', 3: '新疆', 4: '西藏', 5: '马克思主义中国化、时代化、大众化专项', 6: '高校思想政治工作专项', 7: '工程科技人才培养研究专项', 8: '教育廉政理论研究专项', 9: '科研诚信和学风建设专项'}
IDS = ['20120229031516556', '20120229031502516', '20120229031448652', '20120229031427142', '20120229031414133', '20120229031400273', '20120229031346207', '20120229031331214', '20120229031316229']

def moe_humanities_general_projects_2012(keyword='', attachment=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    if attachment is not None:
        attachment = int(attachment)
        if attachment not in COUNTS:
            raise ValueError('附件编号须为 1—9')
    rows = json.loads((ROOT / '2012立项名单.json').read_text(encoding='utf8'))
    if len(rows) != sum(COUNTS.values()):
        raise ValueError('快照总数异常')
    needle = ''.join(keyword.split()).casefold()
    found = [r for r in rows if (attachment is None or r['附件'] == attachment) and needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'status': '2012 年正式立项公告快照，项目当前状态需另核', 'source_url': ANNOUNCEMENT, 'attachment_names': NAMES, 'pdf_urls': {str(i): f'https://www.sinoss.net/uploadfile/2012/0229/{v}.pdf' for i, v in enumerate(IDS, 1)}, 'filtered_total': len(found), 'page': page, 'page_size': page_size, 'results': found[(page - 1) * page_size:page * page_size]}
