"""澳门统计暨普查局公开 Web Service：人口估计及总面积。"""
import release_runtime
import argparse
import json
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
import requests
API = 'https://www.dsec.gov.mo/macaudata.asmx/getMacauData'
DOC = 'https://www.dsec.gov.mo/macaudata.asmx?op=getMacauData'
SERVICE = 'https://www.dsec.gov.mo/zh-CN/Service/WebService'
TYPES = {'population': 'LatestPopulationEstimation', 'area': 'AreaInKM2'}

class _Text(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

def get_latest(indicator='population'):
    if indicator not in TYPES:
        raise ValueError('indicator 须为 population 或 area')
    response = requests.get(API, params={'vMacauDataType': TYPES[indicator], 'vLanguageType': 'SChinese'}, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    ns = {'d': 'http://www.dsec.gov.mo/'}
    if root.tag != '{http://www.dsec.gov.mo/}DSECData':
        raise ValueError('统计局响应结构不符')
    raw = root.findtext('d:Text', namespaces=ns)
    year = root.findtext('d:ReferenceYear', namespaces=ns)
    month = root.findtext('d:ReferenceMonth', namespaces=ns)
    day = root.findtext('d:ReferenceDay', namespaces=ns)
    if not raw or not all((v and v.isdigit() for v in (year, month, day))):
        raise ValueError('数据或参考日期缺失')
    parser = _Text()
    parser.feed(raw)
    value = ''.join(parser.parts).strip().replace('\xa0', '')
    if not value:
        raise ValueError('显示值为空')
    return {'source': '澳门特别行政区政府统计暨普查局', 'indicator': indicator, 'display_value': value, 'reference_date': f'{int(year):04}-{int(month):02}-{int(day):02}', 'api': API, 'documentation': DOC, 'service': SERVICE, 'unit': '人' if indicator == 'population' else '平方公里', 'note': '官方公布的最新估计/面积及其参考日期；服务可能更新。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('indicator', choices=TYPES)
    a = p.parse_args()
    print(json.dumps(get_latest(a.indicator), ensure_ascii=False, indent=2))
