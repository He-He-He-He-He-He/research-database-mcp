"""2013—2015 国家社科基金艺术学年度项目公开资料快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2013: ('https://www.mct.gov.cn/whzx/bnsj/whkjs/201311/t20131105_750587.html', 145, '2013 立项公告正文表'), 2014: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202201/P020220216531003417704.xlsx', 159, '2022 历年汇编中的 2014 非重大项目'), 2015: ('https://www.mct.gov.cn/whzx/bnsj/whkjs/201509/W020150907623815313151.xls', 184, '2015 立项公告附件')}

def mct_art_research_2013_2015(year, keyword=''):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2013—2015 年度')
    source, expected, edition = SOURCES[year]
    rows = json.loads((ROOT / f'{year}.json').read_text(encoding='utf-8'))
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source, 'source_edition': edition} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
