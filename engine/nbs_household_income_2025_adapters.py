"""国家统计局 2025 年全国及分城乡居民收支原表。"""
import release_runtime
import argparse, json, requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/zxfb/202601/t20260119_1962321.html'

def household_income(table=1, keyword=None, timeout=15):
    if table not in (1, 2):
        raise ValueError('表号必须为 1 或 2')
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('关键词无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    b = s.select_one('.trs_editor_view') or s.select_one('.TRS_Editor')
    if b is None:
        raise ValueError('正文缺失')
    tables = b.find_all('table')
    if len(tables) != 2:
        raise ValueError('报告表格数量变化')
    raw = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in tables[table - 1].find_all('tr')]
    if not raw or raw[0][0] != '指标':
        raise ValueError('原表表头变化')
    notes = [row[0] for row in raw if len(row) == 1 and row[0].startswith('注：')]
    rows = [row for row in raw[1:] if len(row) == 3]
    if keyword is not None:
        rows = [x for x in rows if keyword in x[0]]
    return {'source': '国家统计局 2025 年居民收入和消费支出情况', 'source_url': URL, 'year': 2025, 'table': table, 'keyword_filter': keyword, 'headers': raw[0], 'rows': rows, 'table_notes': notes, 'full_official_text': b.get_text(' ', strip=True), 'note': '表 1 含全国与分城乡，括号内为实际增速、其他为名义增速；表 2 为分城乡名义增速。保留单位、原文和调查口径。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--table', type=int, choices=[1, 2], default=1)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(household_income(a.table, a.keyword), ensure_ascii=False, indent=2))
