"""Hunan S&T department's published cross-provincial technology SME statistics."""
import release_runtime
import hashlib, re, subprocess
from bs4 import BeautifulSoup
SOURCES = {'2022H1': 'https://kjt.hunan.gov.cn/kjt/xxgk/kjtj/202207/t20220706_27316400.html', '2023H1': 'https://kjt.hunan.gov.cn/kjt/xxgk/kjtj/202307/t20230703_29391034.html', '2023Q3': 'https://kjt.hunan.gov.cn/kjt/xxgk/kjtj/202310/t20231007_31514836.html', '2023FY': 'https://kjt.hunan.gov.cn/kjt/xxgk/kjtj/202401/t20240105_32619082.html'}

def catalog():
    return [{'period': k, 'url': v} for k, v in SOURCES.items()]

def table(period, region=''):
    if not isinstance(period, str) or period not in SOURCES:
        raise ValueError('period must be 2022H1, 2023H1, 2023Q3 or 2023FY')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    proc = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '3000000', SOURCES[period]], capture_output=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('HTTPS source read failed: curl status ' + str(proc.returncode))
    raw = proc.stdout
    if len(raw) > 3000000:
        raise ValueError('response too large')
    soup = BeautifulSoup(raw, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('unexpected table count')
    trs = tables[0].find_all('tr')
    rows = []
    for tr in trs[1:]:
        cells = [''.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) != 3 or not re.fullmatch('\\d+', cells[1]) or (not re.fullmatch('\\d+|-', cells[2])):
            raise ValueError('unexpected table row')
        rows.append({'region': cells[0], 'count': cells[1], 'rank': cells[2]})
    if len(rows) != 32 or rows[-1]['region'] != '总计' or sum((int(x['count']) for x in rows[:-1])) != int(rows[-1]['count']):
        raise ValueError('unexpected rows or total')
    return {'source': '湖南省科学技术厅公开全国各省份科技型中小企业入库数量及排名', 'period': period, 'source_url': SOURCES[period], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'unit': '个', 'total_rows': len(rows), 'rows': [x for x in rows if region in x['region']], 'note': '据页面注释，湖南科技厅根据全国科技型中小企业信息服务平台各省市入库公告整理，五个计划单列市汇总进所在省份。期次按官方标题：H1为1–6月，2023Q3为1–9月，FY为2023年度；是累计入库数量，不是单季度增量或全体中小企业数。排名及总计保留官方原值，统计资格和变化应核原文。'}
