"""Unified access to verified national R&D expenditure bulletin tables."""
import release_runtime
import nbs_research_funding_1999_2008_adapter as early
import nbs_research_funding_2010_2017_adapter as middle
import nbs_research_funding_2018_2022_adapter as later
import nbs_research_funding_adapters as recent

def available_years():
    return sorted(set(early.SOURCES) | set(middle.SOURCES) | set(later.SOURCES) | set(recent.URLS))

def query(year, keyword='', limit=100, offset=0):
    if type(year) is not int or year not in available_years():
        raise ValueError('该年尚无已接入的年度公报；可查询 available_years，缺年不代表未发布')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    if year in early.SOURCES:
        result = early.table(year, keyword, limit, offset)
        branch = '1999–2008'
    elif year in middle.SOURCES:
        result = middle.table(year, keyword, limit, offset)
        branch = '2010–2017'
    elif year in later.SOURCES:
        result = later.table(year, keyword, limit, offset)
        branch = '2018–2022'
    else:
        result = recent.report(year, keyword)
        branch = '2023–2025'
        for t in result['tables']:
            rows = t['rows']
            t['matched_rows'] = len(rows)
            t['offset'] = offset
            t['rows'] = rows[offset:offset + limit]
            t['truncated'] = offset + limit < len(rows)
    return {'year': year, 'keyword': keyword, 'limit': limit, 'offset': offset, 'adapter_range': branch, 'result': result, 'scope': '按已接入的年度官方公报路由；筛选和分页按各表进行，原文可能有后续修订；2000、2009 尚未接入年度公报，不代表没有发布。'}
