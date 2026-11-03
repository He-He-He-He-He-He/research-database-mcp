"""Selected structured domestic tourism figures from current MCT releases."""
import release_runtime
import re
from mct_statistics_adapters import mct_statistics, mct_statistics_detail
PATTERNS = {'total_trips': '(?<!居民)(?:国内居民|国内)出游人次\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(亿|万)', 'urban_trips': '城镇居民(?:国内)?出游人次\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(亿|万)', 'rural_trips': '农村居民(?:国内)?出游(?:人次)?\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(亿|万)', 'total_spending': '(?<!居民)(?:国内居民|国内)出游(?:总)?花费\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(万亿元|亿元)', 'urban_spending': '城镇居民(?:国内)?出游(?:总)?花费\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(万亿元|亿元)', 'rural_spending': '农村居民(?:国内)?出游(?:总)?花费\\s*([0-9]+(?:\\.[0-9]+)?)\\s*(万亿元|亿元)'}

def catalog():
    entries = mct_statistics()['items']
    return [x for x in entries if re.search('国内(?:居民)?出游(?:市场)?数据情况|国内旅游市场数据情况|国内旅游数据情况', x['title'])]

def detail(path):
    found = [x for x in catalog() if x['path'] == path]
    if len(found) != 1:
        raise ValueError('path is not a current catalog domestic travel release')
    doc = mct_statistics_detail(path)
    metrics = {}
    for key, pattern in PATTERNS.items():
        text = doc['text']
        if key.startswith('total_'):
            text = '\n'.join((line.split('其中', 1)[0] for line in text.splitlines()))
        matches = list(re.finditer(pattern, text))
        if len(matches) == 1:
            m = matches[0]
            metrics[key] = {'value': m.group(1), 'unit': m.group(2) + ('人次' if key.endswith('trips') else ''), 'source_excerpt': m.group(0)}
    if not metrics:
        raise ValueError('no supported unambiguous data found; inspect original')
    return {'source': '文化和旅游部国内居民出游抽样调查发布', 'url': doc['url'], 'title': doc['title'], 'published': doc['published'], 'metrics': metrics, 'source_text': doc['text'], 'note': '按公布期累计值；单位和抽样口径依原文。未识别项省略，不作为零。'}
