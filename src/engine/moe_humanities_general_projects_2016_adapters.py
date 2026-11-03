"""教育部 2016 年人文社科一般项目正式立项公告附件快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部人文社科一般项目2016'
ANNOUNCEMENT = 'https://www.sinoss.net/c/2016-09-30/550113.shtml'
COUNTS = {1: 1958, 2: 118, 3: 28, 4: 6, 5: 92, 6: 150, 7: 16, 8: 4, 9: 120}
NAMES = {1: '规划基金、青年基金、自筹经费', 2: '西部和边疆地区', 3: '新疆', 4: '西藏', 5: '中国特色社会主义理论体系研究专项', 6: '高校思想政治工作专项', 7: '工程科技人才培养研究专项', 8: '教育廉政理论研究专项', 9: '高校示范马克思主义学院和优秀教学科研团队建设'}
IDS = ['20160715032217952', '20160715032318912', '20160715034659187', '20160715045015654', '20160715044126349', '20160715044144488', '20160715044159849', '20160715045743251', '20160715045523418']

def moe_humanities_general_projects_2016(keyword='', attachment=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    if attachment is not None:
        attachment = int(attachment)
        if attachment not in COUNTS:
            raise ValueError('附件编号须为 1—9')
    rows = json.loads((ROOT / '2016立项名单.json').read_text(encoding='utf8'))
    if len(rows) != sum(COUNTS.values()):
        raise ValueError('快照总数异常')
    needle = ''.join(keyword.split()).casefold()
    found = [r for r in rows if (attachment is None or r['附件'] == attachment) and needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    for r in found:
        r['项目名称可能截断'] = r['项目名称'].endswith('研')
    return {'status': '2016 年正式立项公告快照，项目当前状态需另核', 'source_url': ANNOUNCEMENT, 'attachment_names': NAMES, 'pdf_urls': {str(i): f'https://www.sinoss.net/uploadfile/2016/0715/{v}.pdf' for i, v in enumerate(IDS, 1)}, 'filtered_total': len(found), 'page': page, 'page_size': page_size, 'results': found[(page - 1) * page_size:page * page_size]}
