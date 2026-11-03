"""国家邮政局 2023–2024 年分省快递业务量与收入原表。"""
import release_runtime
import argparse, json, requests
from bs4 import BeautifulSoup
URLS = {2023: 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202401/59eeb6e8b0e7404f8127aa2c7aebded6.shtml', 2024: 'https://www.spb.gov.cn/gjyzj/c100276/202501/460d02f2e54c4d0ebbba3a4f431d0042.shtml'}

def express_provinces(year=2024, region=None, timeout=15):
    if year not in URLS:
        raise ValueError('只支持 2023、2024')
    if region is not None and (not isinstance(region, str) or len(region) > 20):
        raise ValueError('地区无效')
    url = URLS[year]
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = s.find_all('table')
    if len(tables) != 4:
        raise ValueError('表格数量已变化')
    raw = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in tables[1].find_all('tr')]
    if len(raw) != 33 or len(raw[0]) != 5 or raw[1][0] != '全国':
        raise ValueError('分省表结构已变化')
    rows = raw[1:]
    if region is not None:
        rows = [x for x in rows if x[0] == region]
    return {'source': '国家邮政局', 'source_url': url, 'year': year, 'headers': raw[0], 'rows': rows, 'note': '年度累计，原表单位逐年不同：2023 为万件、万元，2024 为亿件、亿元；同比增速为百分比。统计口径和舍入须查原文。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=URLS)
    p.add_argument('--region')
    a = p.parse_args()
    print(json.dumps(express_provinces(a.year, a.region), ensure_ascii=False, indent=2))
