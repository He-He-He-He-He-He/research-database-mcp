"""国家统计局 2024 年农业及相关产业增加值公告原表。"""
import release_runtime
import argparse, json, requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/zxfbhjd/202512/t20251230_1962181.html'

def agriculture_added_value(keyword=None, timeout=15):
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
    if len(raw) != 18 or raw[1][0] != '农业及相关产业':
        raise ValueError('原表结构已变化')
    rows = raw[1:17]
    if keyword is not None:
        rows = [x for x in rows if keyword in x[0]]
    text = body.get_text(' ', strip=True)
    return {'source': '国家统计局', 'source_url': URL, 'year': 2024, 'keyword_filter': keyword, 'headers': raw[0], 'rows': rows, 'full_official_text': text, 'note': '原表含三次产业和农业大类两种重叠分组，不能跨组相加；保留空白和舍入注释。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(agriculture_added_value(a.keyword), ensure_ascii=False, indent=2))
