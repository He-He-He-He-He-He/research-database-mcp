"""国家统计局规模以上文化及相关产业企业营业收入原表。"""
import release_runtime
import argparse, json, subprocess
PERIODS = {'2024年度': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250127_1958489.html', '2025一季度': 'https://www.stats.gov.cn/sj/zxfb/202504/t20250429_1959509.html', '2025上半年': 'https://www.stats.gov.cn/zwfwck/sjfb/202507/t20250730_1960526.html', '2025前三季度': 'https://www.stats.gov.cn/sj/zxfb/202510/t20251030_1961731.html', '2025年度': 'https://www.stats.gov.cn/sj/zxfbhjd/202601/t20260130_1962411.html', '2026一季度': 'https://www.stats.gov.cn/sj/zxfb/202604/t20260429_1963439.html', '2026上半年': 'https://www.stats.gov.cn/sj/zxfb/202607/t20260730_1964244.html'}

def data(period, keyword=''):
    if period not in PERIODS:
        raise ValueError('不支持该期次；请查 periods')
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError('需要 Beautiful Soup 4') from e
    url = PERIODS[period]
    raw = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], capture_output=True, check=True).stdout
    s = BeautifulSoup(raw, 'html.parser')
    found = []
    for table in s.find_all('table'):
        rows = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in table.find_all('tr')]
        if rows and any(('营业收入' in cell for row in rows for cell in row)) and (rows not in found):
            found.append(rows)
    if len(found) != 1:
        raise ValueError('上游统计表结构变化，请核对原文')
    rows = found[0]
    selected = [{'source_row': i + 1, 'cells': row} for i, row in enumerate(rows) if not keyword or any((keyword in c for c in row))]
    return {'period': period, 'source': url, 'header': rows[:2], 'rows': selected, 'note': '原表文字保留；部分期次有多行表头，空字符串不得视作零。上半年、前三季度为年初至报告期累计，具体指标单位、同比口径及统计范围以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('periods')
    d = s.add_parser('data')
    d.add_argument('period', choices=PERIODS)
    d.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(PERIODS if a.cmd == 'periods' else data(a.period, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
