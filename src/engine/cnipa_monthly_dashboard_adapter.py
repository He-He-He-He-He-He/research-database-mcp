"""国家知识产权局月度仪表板：国内外专利授权与有效量表。"""
import release_runtime
import ast
import html
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.cnipa.gov.cn/index82/'
GROUPS = [('合计', '小计'), ('合计', '职务'), ('合计', '非职务'), ('国内', '小计'), ('国内', '职务'), ('国内', '非职务'), ('国外', '小计'), ('国外', '职务'), ('国外', '非职务')]
COLUMNS = ['发明_数量', '发明_构成', '实用新型_数量', '实用新型_构成', '外观设计_数量', '外观设计_构成']

def _get(path):
    r = requests.get(BASE + path, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 4000000:
        raise ValueError('上游响应重定向或过大')
    r.encoding = 'utf-8'
    return r.text

def latest():
    js = _get('js/common.js')
    m = re.search('var\\s+firstDate\\s*=\\s*[\'\\"](\\d{6})[\'\\"]', js)
    if not m:
        raise ValueError('无法识别官网最新月份')
    return {'latest': m.group(1), 'source': BASE + 'js/common.js', 'note': '最新月份来自官网公共仪表板，实际各表仍需检索核验。'}

def table(period, kind='grants'):
    if kind not in ('grants', 'active', 'pct', 'trademark', 'owner-grants', 'owner-active'):
        raise ValueError('未知统计表类型')
    if not isinstance(period, str) or not re.fullmatch('20\\d{2}(0[1-9]|1[0-2])', period):
        raise ValueError('period 格式应为 YYYYMM')
    year = int(period[:4])
    latest_period = latest()['latest']
    if year < 2021 or year > int(latest_period[:4]) or period > latest_period:
        raise ValueError('此月不在官网当前时间范围')
    name = {'grants': 'one', 'active': 'three', 'pct': 'five', 'trademark': 'seven', 'owner-grants': 'two', 'owner-active': 'four'}[kind]
    path = f'js/{name}.js' if year <= 2022 else f'js/{year}/{name}.js'
    js = _get(path)
    m = re.search('var\\s+tempValue_' + period + '\\s*=\\s*(\\[.*?\\])\\s*;?\\s*(?:\\r?\\n)\\s*var\\s+', js, re.S)
    if not m:
        raise ValueError('官网此月数据不存在或格式变化')
    try:
        vals = ast.literal_eval(m.group(1))
    except (SyntaxError, ValueError):
        raise ValueError('官网数据格式变化') from None
    if kind in ('owner-grants', 'owner-active'):
        if len(vals) != 6 or any((not isinstance(x, list) or len(x) != 5 for x in vals)):
            raise ValueError('权利人分类表结构变化')
        categories = ('高等院校', '科研机构', '企业', '事业单位', '个人')
        rows = []
        for i, typ in enumerate(('发明', '实用新型', '外观设计')):
            for j, category in enumerate(categories):
                num, pct = (vals[i * 2][j], vals[i * 2 + 1][j])
                if any((not isinstance(x, str) or not re.fullmatch('[0-9,.%\\-]+', x) for x in (num, pct))):
                    raise ValueError('表格存在无法识别的值')
                rows.append({'专利类型': typ, '权利人类型': category, '数量': num, '构成': pct})
        return {'source': '国家知识产权局', 'period': period, 'kind': kind, 'scope': '国内专利权人；' + ('本年累计授权' if kind == 'owner-grants' else '截至所选月末有效量'), 'unit': '件（构成列为百分比）', 'rows': rows, 'data_url': BASE + path, 'page_url': BASE + name + '.html', 'note': '官网分别将前四类列为职务、个人列为非职务；累计授权是流量，有效量是存量。请核对官网统计口径。'}
    if kind in ('pct', 'trademark'):
        if len(vals) != 3 or any((not isinstance(x, list) or len(x) != 4 for x in vals)):
            raise ValueError('表格结构与预期不符')
        columns = ('当月受理量', '当月构成', '当年累计受理量', '累计构成') if kind == 'pct' else ('当年累计注册量', '当年累计构成', '有效注册量', '有效注册构成')
        rows = []
        for region, cells in zip(('合计', '国内', '国外'), vals):
            if any((not isinstance(x, str) or not re.fullmatch('[0-9,.%\\-]+', x) for x in cells)):
                raise ValueError('表格存在无法识别的值')
            rows.append({'地区': region, **dict(zip(columns, cells))})
        note = 'PCT 国际专利申请受理量；当月值与当年累计分别列示，跨月差异或修订请核对原始数据。' if kind == 'pct' else '官网注：当年累计统计日期为上年度12月16日至当月15日；有效注册量统计日期至当月15日。数据提取时间为当月月末。累计注册量与有效注册量分别为流量、存量。'
        return {'source': '国家知识产权局', 'period': period, 'kind': kind, 'unit': '件（构成列为百分比）', 'rows': rows, 'data_url': BASE + path, 'page_url': BASE + name + '.html', 'note': note}
    if len(vals) != 9 or any((not isinstance(x, list) or len(x) != 6 for x in vals)):
        raise ValueError('表格结构与预期不符')
    rows = []
    for (region, service), cells in zip(GROUPS, vals):
        if any((not isinstance(x, str) or not re.fullmatch('[0-9,.%\\-]+', x) for x in cells)):
            raise ValueError('表格存在无法识别的值')
        rows.append({'地区': region, '类别': service, **dict(zip(COLUMNS, cells))})
    if kind == 'grants':
        marker = re.search('var\\s+remk_' + period + "\\s*=\\s*'([^']*)'", js)
        note = BeautifulSoup(html.unescape(marker.group(1)), 'html.parser').get_text(' ', strip=True) if marker else '未识别期次注释，请查看原网页。'
    else:
        latestyear = latest_period[:4]
        remarkjs = _get(f'js/{latestyear}/three.js') if int(latestyear) >= 2023 else _get('js/three.js')
        key = 'remark20240701' if period == '202406' else 'remark'
        marker = re.search('var\\s+' + key + '\\s*=\\s*"([^"]*)"', remarkjs)
        note = BeautifulSoup(html.unescape(marker.group(1)), 'html.parser').get_text(' ', strip=True) if marker else '未识别官网注释，请查看原网页。'
    note_scope = '该期脚本的注释' if kind == 'grants' else '从当前最新年份脚本读取的通用注释（2024年6月采用特殊注释），不保证适用于所有历史期次'
    return {'source': '国家知识产权局', 'period': period, 'kind': kind, 'scope': '本年 1 月至所选月累计授权' if kind == 'grants' else '截至所选月末有效量', 'unit': '件（构成列为百分比）', 'rows': rows, 'official_note': note, 'official_note_scope': note_scope, 'data_url': BASE + path, 'page_url': BASE + name + '.html', 'note': '保留官网原始字符串与构成比例；累计授权量不能按月简单相加，有效量是存量而非当月授权。'}
