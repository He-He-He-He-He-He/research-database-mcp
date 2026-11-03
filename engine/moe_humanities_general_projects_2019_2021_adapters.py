"""教育部人文社科一般项目 2019—2021 部分年度官方公告附件快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '教育部人文社科一般项目2019-2021'
SOURCES = {2019: {'announcement': 'https://www.sinoss.net/c/2019-05-17/550005.shtml', 'counts': {1: 3095, 2: 186, 3: 15, 4: 6, 5: 100, 6: 70, 7: 11, 8: 5, 9: 187}, 'pdfs': {str(i): f'https://www.sinoss.net/uploadfile/2019/0315/2019{i:02}.pdf' for i in range(1, 10)}}, 2020: {'announcement': 'https://www.sinoss.net/c/2020-05-09/550040.shtml', 'counts': {1: 2620, 2: 173, 3: 12, 4: 6}, 'pdfs': {str(i): f'https://www.sinoss.net/uploadfile/2020/0320/{v}.pdf' for i, v in enumerate(['20200320043648943', '20200320043709361', '20200320043730153', '20200320043759932'], 1)}}, 2021: {'announcement': 'https://www.moe.gov.cn/s78/A13/tongzhi/202108/t20210820_552619.html', 'counts': {1: 2362, 3: 15, 4: 1, 6: 209}, 'pdfs': {'1': 'https://www.sinoss.net/uploadfile/2021/0820/20210820024641764.pdf', '3': 'https://www.sinoss.net/uploadfile/2021/0820/20210820024706542.pdf', '4': 'https://www.sinoss.net/uploadfile/2021/0820/20210820024720946.pdf', '6': 'https://www.sinoss.net/uploadfile/2021/0820/20210820024748190.pdf'}}}

def moe_humanities_general_projects_2019_2021(keyword='', year=None, attachment=None, page=1, page_size=20):
    page, page_size = (int(page), int(page_size))
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    if year is not None:
        year = int(year)
        if year not in SOURCES:
            raise ValueError('仅覆盖 2019—2021 年')
    if attachment is not None:
        attachment = int(attachment)
        if not 1 <= attachment <= 9:
            raise ValueError('附件编号须为 1—9')
        if year is not None and attachment not in SOURCES[year]['counts']:
            raise ValueError('该年度附件未收录，不能视为零项')
    rows = json.loads((ROOT / '2019-2021立项名单.json').read_text(encoding='utf8'))
    if len(rows) != 9073:
        raise ValueError('快照总数异常')
    needle = ''.join(keyword.split()).casefold()
    found = [r for r in rows if (year is None or r['年度'] == year) and (attachment is None or r['附件'] == attachment) and (needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold())]
    return {'status': '正式立项公告附件快照，当前项目状态需另核', 'coverage': '2019 公告九附件、2020 公告四附件、2021 附件 1、3、4、6；2021 附件 2、5 未收录', 'filtered_total': len(found), 'page': page, 'page_size': page_size, 'results': found[(page - 1) * page_size:page * page_size], 'sources': {str(y): v for y, v in SOURCES.items() if year is None or y == year}}
