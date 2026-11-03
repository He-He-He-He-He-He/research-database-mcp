"""国家知识产权局集成电路布图设计登记月度及历史累计表。"""
import release_runtime
import ast, re
import requests
BASE = 'https://www.cnipa.gov.cn/index82/'

def _get(path):
    r = requests.get(BASE + path, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 4000000:
        raise ValueError('上游响应跳转或过大')
    r.encoding = 'utf-8'
    return r.text

def report(period):
    if not isinstance(period, str) or not re.fullmatch('20\\d{2}(0[1-9]|1[0-2])', period):
        raise ValueError('期次格式为 YYYYMM')
    y = int(period[:4])
    s = _get('js/common.js')
    m = re.search('var\\s+firstDate\\s*=\\s*[\'\\"](\\d{6})', s)
    if not m or y < 2021 or period > m.group(1):
        raise ValueError('期次不在官网当前公布范围')
    path = 'js/eleven.js' if y <= 2022 else f'js/{y}/eleven.js'
    js = _get(path)
    p = 'var\\s+tempValue_' + period + '\\s*=\\s*(\\[\\s*\\[[^\\[\\]]*\\]\\s*,\\s*\\[[^\\[\\]]*\\]\\s*,?\\s*\\])'
    m = re.search(p, js, re.S)
    if not m:
        raise ValueError('未识别该月登记数据')
    vals = ast.literal_eval(m.group(1))
    if period <= '202501':
        labels = ['总累计', '2001-2010年'] + [f'{i}年' for i in range(2011, y + 1)]
    elif y == 2025:
        labels = ['总累计', '2001-2011年'] + [f'{i}年' for i in range(2012, y + 1)]
    else:
        labels = ['总累计', f'2001-{y - 14}年'] + [f'{i}年' for i in range(y - 13, y + 1)]
    if len(vals) != 2 or any((not isinstance(x, list) or len(x) != len(labels) for x in vals)):
        raise ValueError('官方统计表结构变化')
    if any((isinstance(v, bool) or not isinstance(v, int) or v < 0 for row in vals for v in row)):
        raise ValueError('数据非预期整数')
    return {'source': '国家知识产权局', 'period': period, 'unit': '件', 'columns': labels, 'rows': [{'item': '申请', 'values': vals[0]}, {'item': '发证', 'values': vals[1]}], 'page_url': BASE + 'eleven.html', 'data_url': BASE + path, 'note': '历史各年和当年1月至所选月累计；总累计包含各分项，不应重复相加。分组起点随官网规则变化；申请数与发证数不同。'}
