"""Selected national public-library measures in official MCT annual bulletins."""
import release_runtime
import re
from mct_statistics_adapters import mct_statistics_detail
PAGES = {2024: '/zfxxgkml/tjxx/202505/t20250530_960335.html', 2025: '/zfxxgkml/tjxx/202606/t20260602_966073.html'}
PATTERNS = {'libraries': ('全国共有公共图书馆([0-9.]+)个', '个'), 'employees': ('全国共有公共图书馆[0-9.]+个，从业人员([0-9.]+)万人', '万人'), 'floor_area': ('全国公共图书馆实际使用房屋建筑面积([0-9.]+)万平方米', '万平方米'), 'collection': ('全国图书总藏量([0-9.]+)亿册', '亿册'), 'seats': ('阅览室座席数([0-9.]+)万个', '万个'), 'floor_area_per_10000_people': ('全国平均每万人公共图书馆建筑面积([0-9.]+)平方米', '平方米/万人'), 'books_per_person': ('全国人均图书藏量([0-9.]+)册', '册/人'), 'book_acquisition_per_person': ('全年全国人均购书费([0-9.]+)元', '元/人'), 'total_visits': ('全年公共图书馆总流通人次([0-9.]+)亿(?:人次)?', '亿人次'), 'events': ('全年共为读者举办各种活动([0-9.]+)万次', '万次')}

def catalog():
    return [{'year': y, 'path': path} for y, path in sorted(PAGES.items(), reverse=True)]

def report(year):
    if type(year) is not int or year not in PAGES:
        raise ValueError('supported years: 2024, 2025')
    doc = mct_statistics_detail(PAGES[year])
    text = doc['text']
    section = text.split('公共图书馆方面', 1)
    if len(section) != 2 or '群众文化机构方面' not in section[1]:
        raise ValueError('library section not found')
    section = section[1].split('群众文化机构方面', 1)[0]
    results = {}
    for key, (pat, unit) in PATTERNS.items():
        matches = list(re.finditer(pat, section))
        if len(matches) == 1:
            m = matches[0]
            results[key] = {'value': m.group(1), 'unit': unit, 'source_excerpt': m.group(0)}
    if not results:
        raise ValueError('no unambiguous metrics')
    return {'source': '文化和旅游部文化和旅游发展统计公报', 'year': year, 'url': doc['url'], 'published': doc['published'], 'metrics': results, 'source_section': section, 'note': '年末资源和全年活动为不同统计期间；缺失字段不当作零，口径以原文为准。'}
