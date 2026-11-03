"""国家统计局 2024 年专利密集型产业增加值公告原表。"""
import release_runtime
import argparse, json, requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/zxfbhjd/202512/t20251231_1962229.html'

def patent_intensive(keyword=None, timeout=15):
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('关键词无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.trs_editor_view')
    if body is None:
        raise ValueError('正文缺失')
    table = body.find('table')
    if not table:
        raise ValueError('原表缺失')
    raw = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in table.find_all('tr')]
    if len(raw) != 10 or raw[1][0] != '专利密集型产业':
        raise ValueError('原表结构已变化')
    rows = raw[1:9]
    if keyword is not None:
        rows = [x for x in rows if keyword in x[0]]
    text = body.get_text(' ', strip=True)
    return {'source': '国家统计局、国家知识产权局', 'source_url': URL, 'year': 2024, 'keyword_filter': keyword, 'headers': raw[0], 'rows': rows, 'full_official_text': text, 'note': '分行业增加值和其构成占比；总计与分项存在包含关系，不应重复相加，数值舍入差异见原文。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(patent_intensive(a.keyword), ensure_ascii=False, indent=2))
