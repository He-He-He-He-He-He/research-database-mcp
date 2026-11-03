"""2010—2012 国家社科基金艺术学项目官方公告原表快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '国家社科基金艺术学'
SOURCES = {2010: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202012/t20201206_918742.html', 113, '文化和旅游部政府信息公开的 2010 公告表'), 2011: ('https://www.nopss.gov.cn/mediafile/201108/16/P201108161612457687189601.xls', 142, '全国哲学社会科学工作办公室 2011 公告附件'), 2012: ('https://zwgk.mct.gov.cn/zfxxgkml/kjjy/202012/t20201206_916743.html', 123, '文化和旅游部政府信息公开的 2012 公告表')}

def mct_art_research_2010_2012(year, keyword=''):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('仅支持 2010—2012 年度')
    source, expected, edition = SOURCES[year]
    rows = json.loads((ROOT / f'{year}.json').read_text(encoding='utf-8'))
    if len(rows) != expected or len({r['批准号'] for r in rows}) != expected:
        raise ValueError('快照行数或批准号异常')
    needle = ''.join(keyword.split()).casefold()
    return [{**r, 'source_url': source, 'source_edition': edition} for r in rows if needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
