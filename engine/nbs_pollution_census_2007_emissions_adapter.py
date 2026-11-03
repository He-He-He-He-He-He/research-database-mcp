"""First national pollution census: national pollutant emissions in 2007."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/tjgb/qttjgb/qgqttjgb/202302/t20230218_1913282.html'
SPECS = {'wastewater': ['化学需氧量', '氨氮', '石油类', '重金属', '总磷', '总氮'], 'wastegas': ['二氧化硫', '烟尘', '氮氧化物']}

def emissions(kind='wastewater'):
    if kind not in SPECS:
        raise ValueError('kind must be wastewater or wastegas')
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
    texts = {''.join(p.get_text(' ', strip=True).split()) for p in soup.select('p') if not p.find('p') and '各类源废水排放总量' in p.get_text() and ('主要污染物排放总量' in p.get_text())}
    if len(texts) != 1:
        raise ValueError('expected one unique source paragraph')
    text = texts.pop()
    segment = text.split('主要污染物排放总量：', 1)[1].split('。', 1)[0]
    items = []
    for name in SPECS[kind]:
        matches = re.findall(re.escape(name) + '(?:（[^）]*）)?([0-9]+(?:\\.[0-9]+)?)(万吨|吨)', segment)
        if len(matches) != 1:
            raise ValueError('missing or ambiguous source metric: ' + name)
        items.append({'pollutant': name, 'value': matches[0][0], 'unit': matches[0][1]})
    return {'source': '国家统计局刊载第一次全国污染源普查公报', 'source_url': URL, 'year': 2007, 'kind': kind, 'items': items, 'source_paragraph': text, 'note': '这是公报中各类源主要污染物排放总量，不是单项工业排放；重金属包括镉、铬、砷、汞、铅。与2017年比较须先核调查对象、方法及污染物定义，不能不加核实直接比较。'}
