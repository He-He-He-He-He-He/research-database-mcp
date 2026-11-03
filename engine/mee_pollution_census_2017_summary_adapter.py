"""Selected national pollutant emissions from the second pollution source census."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.mee.gov.cn/home/ztbd/rdzl/wrypc/zlxz/202006/t20200616_784745.html'
SPECS = {'water': ['化学需氧量', '氨氮', '总氮', '总磷', '动植物油', '石油类', '挥发酚', '氰化物', '重金属'], 'air': ['二氧化硫', '氮氧化物', '颗粒物']}

def emissions(kind='water'):
    if kind not in SPECS:
        raise ValueError('kind must be water or air')
    with requests.get(URL, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    content = soup.select_one('.TRS_Editor')
    if not content:
        raise ValueError('official bulletin content unavailable')
    prefix = {'water': '2017年，全国水污染物排放量：', 'air': '2017年，全国大气污染物排放量：'}[kind]
    matching = [''.join(p.get_text(' ', strip=True).split()) for p in content.select('p') if ''.join(p.get_text(' ', strip=True).split()).startswith(prefix)]
    if len(matching) != 1:
        raise ValueError('expected one matching source paragraph')
    text = matching[0]
    segment = text.split('。', 1)[0]
    items = []
    for name in SPECS[kind]:
        pattern = re.escape(name) + '(?:（[^）]*）)?([0-9]+(?:\\.[0-9]+)?)(万吨|吨)'
        matches = re.findall(pattern, segment)
        if len(matches) != 1:
            raise ValueError('source metric missing or ambiguous: ' + name)
        items.append({'pollutant': name, 'value': matches[0][0], 'unit': matches[0][1]})
    return {'source': '生态环境部 第二次全国污染源普查公报', 'source_url': URL, 'year': 2017, 'kind': kind, 'items': items, 'source_paragraph': text, 'note': '年度排放量；水与大气、吨与万吨不可混同。重金属含铅、汞、镉、铬及类金属砷；挥发性有机物属部分行业试验性调查，未列入本接口指标。与其他年份比较需核查调查范围与方法。'}
