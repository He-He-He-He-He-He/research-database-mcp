"""教育部 2013 年人文社科一般项目正式立项公告附件快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部人文社科一般项目2013'
ANNOUNCEMENT = 'https://www.sinoss.net/c/2014-10-30/550087.shtml'
COUNTS = {1: 3232, 2: 105, 3: 20, 4: 4, 5: 64, 6: 177, 7: 7, 8: 8}
NAMES = {1: '规划基金、青年基金、自筹经费', 2: '西部和边疆地区', 3: '新疆', 4: '西藏', 5: '马克思主义中国化、时代化、大众化专项', 6: '高校思想政治工作专项', 7: '教育廉政理论研究专项', 8: '科研诚信和学风建设专项'}
PDFS = ['2013/0522/20130522083632380', '2013/0522/20130522082656583', '2013/0522/20130522082809130', '2013/0522/20130522082901439', '2013/0522/20130522083041375', '2014/1030/20141030021945692', '2013/0522/20130522083249132', '2013/0522/20130522112827321']

def moe_humanities_general_projects_2013(keyword='', attachment=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    if attachment is not None:
        attachment = int(attachment)
        if attachment not in COUNTS:
            raise ValueError('附件编号须为 1—8')
    rows = json.loads((ROOT / '2013立项名单.json').read_text(encoding='utf8'))
    if len(rows) != sum(COUNTS.values()):
        raise ValueError('快照总数异常')
    needle = ''.join(keyword.split()).casefold()
    found = [r for r in rows if (attachment is None or r['附件'] == attachment) and needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'status': '2013 年正式立项公告快照，项目当前状态需另核', 'source_url': ANNOUNCEMENT, 'discrepancy': '附件6原表177项，公告称178项；差异原因未核实', 'attachment_names': NAMES, 'pdf_urls': {str(i): f'https://www.sinoss.net/uploadfile/{v}.pdf' for i, v in enumerate(PDFS, 1)}, 'filtered_total': len(found), 'page': page, 'page_size': page_size, 'results': found[(page - 1) * page_size:page * page_size]}
