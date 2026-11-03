"""2016—2018 国家社科基金艺术学年度项目公开资料快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2016: ('https://www.mct.gov.cn/whzx/bnsj/whkjs/201608/W020160822422820154613.xlsx', 196, '2016 立项公告附件'), 2017: ('https://www.mct.gov.cn/whzx/bnsj/whkjs/201709/t20170922_750910.html', 249, '2017 立项公告正文表'), 2018: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202201/P020220216531003417704.xlsx', 219, '2022 发布历年汇编中的 2018 非重大项目')}

def mct_art_research_2016_2018(year, keyword=''):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2016—2018 年度')
    source, expected, edition = SOURCES[year]
    rows = json.loads((ROOT / f'{year}.json').read_text(encoding='utf-8'))
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source, 'source_edition': edition} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
