"""中国银行公开的贷款市场报价利率历史表。"""
import release_runtime
import re
import subprocess
from datetime import date
from bs4 import BeautifulSoup
URL = 'https://www.boc.cn/fimarkets/lilv/fd32/201310/t20131031_2591219.html'

def lpr(start='', end=''):
    """查询转载的历史 LPR，start/end 均为 YYYY-MM-DD，区间包含端点。"""
    for v in (start, end):
        if v:
            try:
                if date.fromisoformat(v).isoformat() != v:
                    raise ValueError
            except ValueError:
                raise ValueError('日期须为 YYYY-MM-DD')
    if start and end and (start > end):
        raise ValueError('起始日期晚于结束日期')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--compressed', '--max-time', '25', URL], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('中国银行查询失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    soup = BeautifulSoup(p.stdout, 'html.parser')
    found = []
    for t in soup.find_all('table'):
        rows = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in t.find_all('tr')]
        if rows and rows[0][:3] == ['LPR报价', '1年期', '5年期以上']:
            found.append(rows)
    if len(found) != 1:
        raise RuntimeError('未识别唯一 LPR 历史表')
    out = []
    for row in found[0][1:]:
        if len(row) < 3 or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', row[0]):
            raise RuntimeError('LPR 数据行结构变化')
        if not all((re.fullmatch('\\d+(?:\\.\\d+)?%', x) for x in row[1:3])):
            raise RuntimeError('LPR 值格式变化')
        if start and row[0] < start or (end and row[0] > end):
            continue
        out.append({'date': row[0], 'one_year_percent': float(row[1][:-1]), 'over_five_year_percent': float(row[2][:-1]), 'raw': row[:3]})
    return {'source': URL, 'publisher': '中国银行转载全国银行间同业拆借中心 LPR', 'unit': '百分比（年利率）', 'total': len(out), 'records': out}
