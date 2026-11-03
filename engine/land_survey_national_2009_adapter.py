"""Eight published land-use categories of the second national land survey."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCE = 'https://news.12371.cn/2013/12/31/ARTI1388437838282426.shtml'
EXPECTED = ('耕地', '园地', '林地', '草地', '城镇村及工矿用地', '交通运输用地', '水域及水利设施用地')

def categories(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    with requests.get(SOURCE, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        content = bytearray()
        for chunk in r.iter_content(65536):
            content.extend(chunk)
            if len(content) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(content), 'html.parser')
    found = {}
    for p in soup.find_all('p'):
        raw = ' '.join(p.get_text(' ', strip=True).split())
        normal = ''.join(raw.split())
        m = re.match('^([^：]+)：([0-9]+(?:\\.[0-9]+)?)万公顷（([0-9]+(?:\\.[0-9]+)?)万亩）', normal)
        if not m or m.group(1) not in EXPECTED:
            continue
        name = m.group(1)
        entry = {'category': name, 'area_10000_hectares': m.group(2), 'area_10000_mu': m.group(3), 'source_paragraph': raw}
        if name in found and found[name] != entry:
            raise ValueError('conflicting repeated category')
        found[name] = entry
    if set(found) != set(EXPECTED):
        raise ValueError('unexpected source structure; not all seven published categories found')
    return {'title': '第二次全国土地调查主要数据成果公报', 'survey_reference_date': '2009-12-31', 'publication_date': '2013-12-30', 'source_url': SOURCE, 'source_description': '共产党员网转载国土资源部、国家统计局、国务院第二次全国土地调查领导小组办公室联合公报', 'items': [found[n] for n in EXPECTED if keyword in n], 'note': '公报公布的七类主要地类数据，另有其他土地未列数值，并非全部地类或地图。仅提取每类开头总量；单位为万公顷和万亩，地类定义及调查方法随次别变化，不可直接与第三次调查相减作为实际变化；后者新增湿地一级地类。范围及修订以公报为准。'}
