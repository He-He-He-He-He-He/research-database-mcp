"""Selected annual Chinese cultural heritage service measures from MCT."""
import release_runtime
import re
from mct_statistics_adapters import mct_statistics_detail
PAGES = {2024: '/zfxxgkml/tjxx/202505/t20250530_960335.html', 2025: '/zfxxgkml/tjxx/202606/t20260602_966073.html'}
PATTERNS = {'heritage_institutions': ('全国共有[^。]{0,100}?各类文物机构([0-9.]+)个', '个'), 'heritage_collection': ('全国文物机构藏品([0-9.]+)万件/套', '万件/套'), 'heritage_exhibitions': ('全国(?:各类)?文物机构共举办陈列展览([0-9.]+)万个', '万个'), 'heritage_visits': ('(?<!博物馆)接待观众([0-9.]+)亿人次', '亿人次'), 'minor_visits': ('其中未成年人([0-9.]+)亿人次', '亿人次'), 'registered_museums_memorials': ('全国登记备案博物馆、纪念馆达到([0-9.]+)个', '个')}

def catalog():
    return [{'year': y, 'path': p} for y, p in sorted(PAGES.items(), reverse=True)]

def report(year):
    if type(year) is not int or year not in PAGES:
        raise ValueError('supported years: 2024, 2025')
    doc = mct_statistics_detail(PAGES[year])
    split = doc['text'].split('文物保护利用方面', 1)
    if len(split) != 2 or '非物质文化遗产保护传承方面' not in split[1]:
        raise ValueError('heritage section missing')
    section = split[1].split('非物质文化遗产保护传承方面', 1)[0]
    metrics = {}
    for k, (pattern, unit) in PATTERNS.items():
        match = list(re.finditer(pattern, section))
        if len(match) == 1:
            m = match[0]
            metrics[k] = {'value': m.group(1), 'unit': unit, 'source_excerpt': m.group(0)}
    if not metrics:
        raise ValueError('no unambiguous metrics')
    return {'source': '文化和旅游部文化和旅游发展统计公报', 'year': year, 'url': doc['url'], 'published': doc['published'], 'metrics': metrics, 'source_section': section, 'note': '年末机构藏品与全年展览参观统计期不同；未识别项不视为零。'}
