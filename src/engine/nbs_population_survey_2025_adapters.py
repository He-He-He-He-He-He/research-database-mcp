"""国家统计局 2025 年全国 1% 人口抽样调查主要数据公报。"""
import release_runtime
import argparse
import json
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/zxfbhjd/202605/t20260522_1963788.html'

def population_survey(keyword=None, timeout=15):
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('关键词无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    body = soup.select_one('.trs_editor_view')
    if body is None:
        raise ValueError('找不到公报正文')
    paras = [p.get_text('', strip=True) for p in body.find_all('p')]
    paras = [p for p in paras if p and (not p.isspace())]
    if not any(('全国人口为140545万人' in p for p in paras)):
        raise ValueError('正文格式或数据已变化，需核验')
    notes = [p for p in paras if re.match('^\\[\\d+\\]', p)]
    items = [p for p in paras if not re.match('^\\[\\d+\\]', p) and (keyword is None or keyword in p)]
    return {'source': '国家统计局', 'source_url': URL, 'keyword_filter': keyword, 'timepoint': '2025-11-01 00:00', 'paragraphs': items, 'notes': notes, 'note': '公报为抽样调查推算数，调查时点是 11 月 1 日零时，并非年末人口；保留原文注释。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(population_survey(a.keyword), ensure_ascii=False, indent=2))
