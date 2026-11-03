"""香港环境保护署公开空气质量健康指数：当前 RSS 和过去 24 小时 XML。"""
import release_runtime
import argparse
import json
import xml.etree.ElementTree as ET
import requests
URLS = {'current': 'https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_ChS.xml', 'past24h': 'https://www.aqhi.gov.hk/epd/ddata/html/out/24aqhi_ChS.xml'}

def air_quality(period='current', timeout=15):
    if period not in URLS:
        raise ValueError('period 必须为 current 或 past24h')
    url = URLS[period]
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    if period == 'current':
        channel = root.find('channel')
        if root.tag != 'rss' or channel is None:
            raise ValueError('当前指数响应结构异常')
        entries = [{'station': x.findtext('title'), 'description': x.findtext('description'), 'published': x.findtext('pubDate'), 'url': x.findtext('link')} for x in channel.findall('item')]
        updated = channel.findtext('lastBuildDate')
    else:
        if root.tag != 'AQHI24HrReport':
            raise ValueError('24 小时指数响应结构异常')
        entries = [{'station': x.findtext('StationName'), 'station_type': x.findtext('type'), 'datetime': x.findtext('DateTime'), 'aqhi': x.findtext('aqhi')} for x in root.findall('item')]
        updated = root.findtext('lastBuildDate')
    return {'source': '香港环境保护署空气质量健康指数', 'source_url': url, 'period': period, 'updated': updated, 'items': entries}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('period', nargs='?', choices=URLS, default='current')
    args = parser.parse_args()
    print(json.dumps(air_quality(args.period), ensure_ascii=False, indent=2))
