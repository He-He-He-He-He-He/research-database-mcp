"""国家统计局 2019—2022 年农民工监测调查报告原表。"""
import release_runtime
import json, subprocess
from moe_education_statistics_adapters import _LeafTables
from bs4 import BeautifulSoup
URLS = {2019: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1900710.html', 2020: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1901074.html', 2021: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1901452.html', 2022: 'https://www.stats.gov.cn/sj/zxfb/202304/t20230427_1939124.html'}
TITLES = ['外出农民工地区分布及构成', '农民工输出和输入地区分布', '农民工年龄构成', '农民工就业行业分布情况', '分行业农民工月均收入及增速']

def report(year, table=0):
    if int(year) not in URLS:
        raise ValueError('目前仅支持 2019—2022 年')
    if int(table) not in range(6):
        raise ValueError('表号为 0（全部）或 1—5')
    url = URLS[int(year)]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('国家统计局报告请求失败（curl %s）' % p.returncode)
    html = p.stdout.decode('utf8')
    soup = BeautifulSoup(html, 'html.parser')
    if f'{year}年农民工监测调查报告' not in soup.get_text(' ', strip=True):
        raise RuntimeError('报告标题无法核验')
    parser = _LeafTables()
    parser.feed(html)
    tables = parser.tables
    if len(tables) != 10 or not all((tables[i] == tables[i + 5] for i in range(5))):
        raise RuntimeError('未识别预期五张重复表，网站结构可能改变')
    tables = tables[:5]
    html_tables = soup.find_all('table')[:5]
    units = []
    for i, t in enumerate(tables):
        if year <= 2020:
            prior = html_tables[i].find_previous('p')
            value = prior.get_text(' ', strip=True) if prior else ''
        else:
            value = ' '.join((c['text'] for c in t[0]))
        if '单位' not in value:
            raise RuntimeError('第 %d 张表无法识别单位' % (i + 1))
        units.append(value)
    body = soup.select_one('.txt-content')
    return {'source': '国家统计局农民工监测调查报告', 'year': int(year), 'url': url, 'tables': [{'table': i + 1, 'title': TITLES[i], 'unit': units[i], 'rows': t} for i, t in enumerate(tables) if int(table) in (0, i + 1)], 'report_text': body.get_text('\n', strip=True) if body else None, 'note': '保留原表合并单元格；调查样本、统计范围和指标解释见报告附注。年际比较需核对调查口径。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--table', type=int, choices=range(6), default=0)
    a = p.parse_args()
    print(json.dumps(report(a.year, a.table), ensure_ascii=False, indent=2))
