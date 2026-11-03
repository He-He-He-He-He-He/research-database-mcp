"""Eight published land-use categories of the third national land survey."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCE = 'https://zrzyt.xinjiang.gov.cn/xjgtzy/gzdt/202108/b01337d6498e4cc7b6f242b07e5d5767.shtml'
EXPECTED = ('耕地', '园地', '林地', '草地', '湿地', '城镇村及工矿用地', '交通运输用地', '水域及水利设施用地')

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
        m = re.match('^（[一二三四五六七八]+）([^0-9]+)([0-9]+(?:\\.[0-9]+)?)万公顷（([0-9]+(?:\\.[0-9]+)?)万亩）', normal)
        if not m or m.group(1) not in EXPECTED:
            continue
        name = m.group(1)
        entry = {'category': name, 'area_10000_hectares': m.group(2), 'area_10000_mu': m.group(3), 'source_paragraph': raw}
        if name in found and found[name] != entry:
            raise ValueError('conflicting repeated category')
        found[name] = entry
    if set(found) != set(EXPECTED):
        raise ValueError('unexpected source structure; not all eight published categories found')
    return {'title': '第三次全国国土调查主要数据公报', 'survey_reference_date': '2019-12-31', 'publication_date': '2021-08-25', 'source_url': SOURCE, 'source_description': '新疆维吾尔自治区自然资源厅转载全国联合公报', 'items': [found[n] for n in EXPECTED if keyword in n], 'note': '公报公布的八类国土数据，并非全部地类或地图。仅提取每类开头总量；单位为万公顷和万亩，地类定义、范围及后续修订以公报为准。'}
