"""国家统计局 2021–2023 年农业及相关产业增加值公告原表。"""
import release_runtime
import argparse, json, requests
from bs4 import BeautifulSoup
URLS = {2021: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202212/t20221230_1891328.html', 2022: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202312/t20231229_1946073.html', 2023: 'https://www.stats.gov.cn/zwfwck/sjfb/202412/t20241230_1957936.html'}

def agriculture_history(year=2023, keyword=None, timeout=15):
    if year not in URLS:
        raise ValueError('只支持 2021–2023 年')
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('关键词无效')
    url = URLS[year]
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.trs_editor_view') or s.select_one('.TRS_Editor')
    if body is None:
        raise ValueError('未识别正文')
    t = body.find('table')
    if not t:
        raise ValueError('原表缺失')
    raw = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in t.find_all('tr')]
    if len(raw) != 18 or raw[1][0] != '农业及相关产业':
        raise ValueError('原表结构已变化')
    rows = raw[1:17]
    if keyword is not None:
        rows = [row for row in rows if keyword in row[0]]
    return {'source': '国家统计局', 'source_url': url, 'year': year, 'keyword_filter': keyword, 'headers': raw[0], 'rows': rows, 'full_official_text': body.get_text(' ', strip=True), 'note': '原表两种分类互有重叠，不能跨组相加；2023 年依第五次经济普查核算，与旧年公告比较应核对修订。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=URLS)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(agriculture_history(a.year, a.keyword), ensure_ascii=False, indent=2))
