"""NASA GIBS 全球卫星影像 WMS 图层发现与影像浏览。"""
import release_runtime
import base64, math, re, xml.etree.ElementTree as ET
import requests
URL = 'https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi'

def layers(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 120:
        raise ValueError('关键词无效')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit须为1–500')
    r = requests.get(URL, params={'service': 'WMS', 'request': 'GetCapabilities', 'version': '1.1.1'}, timeout=30)
    r.raise_for_status()
    if len(r.content) > 10000000:
        raise ValueError('能力文档过大')
    root = ET.fromstring(r.content)
    matches = []
    for e in root.findall('.//Layer'):
        name = e.findtext('Name')
        title = e.findtext('Title', '')
        if name and keyword.casefold() in (name + ' ' + title).casefold():
            matches.append({'name': name, 'title': title, 'time_extent': next((x.text for x in e.findall('Extent') if x.get('name') == 'time'), None)})
    return {'source': 'NASA Global Imagery Browse Services', 'source_url': r.url, 'matched': len(matches), 'layers': matches[:limit]}

def map_image(layer, bbox, date, width=256, height=256):
    if not isinstance(layer, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,160}', layer):
        raise ValueError('图层名无效')
    if not isinstance(date, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', date):
        raise ValueError('日期须为YYYY-MM-DD')
    if not isinstance(bbox, (tuple, list)) or len(bbox) != 4 or any((isinstance(v, bool) or not isinstance(v, (int, float)) or (not math.isfinite(v)) for v in bbox)):
        raise ValueError('bbox无效')
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ValueError('bbox须是西南东北经纬度，不能跨反经线')
    if any((isinstance(v, bool) or not isinstance(v, int) or (not 1 <= v <= 1024) for v in (width, height))):
        raise ValueError('宽高须为1–1024')
    p = {'service': 'WMS', 'version': '1.1.1', 'request': 'GetMap', 'format': 'image/png', 'transparent': 'true', 'layers': layer, 'srs': 'EPSG:4326', 'styles': '', 'width': width, 'height': height, 'bbox': ','.join(map(str, bbox)), 'time': date}
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    if len(r.content) > 10000000 or not r.content.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('WMS未返回PNG，图层或日期可能不可用')
    return {'source': 'NASA Global Imagery Browse Services', 'source_url': r.url, 'mime_type': 'image/png', 'image_base64': base64.b64encode(r.content).decode('ascii'), 'note': 'WMS可视化影像，不是原始定量卫星测量；透明或无数据像素不代表零。'}
