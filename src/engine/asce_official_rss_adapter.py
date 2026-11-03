"""Read verified official ASCE Library article headline RSS feeds."""
import release_runtime
import xml.etree.ElementTree as ET
import requests
FEEDS = {'construction': 'jcemd4', 'structural': 'jsendh', 'planning': 'jupddm', 'environment': 'joeedu', 'geotechnical': 'jggefk', 'water-resources': 'jwrmd5', 'transport': 'jtepbs', 'bridge': 'jbenf2', 'aerospace': 'jaeeez'}
EXPECTED = {'construction': 'Journal of Construction Engineering and Management', 'structural': 'Journal of Structural Engineering', 'planning': 'Journal of Urban Planning and Development', 'environment': 'Journal of Environmental Engineering', 'geotechnical': 'Journal of Geotechnical and Geoenvironmental Engineering', 'water-resources': 'Journal of Water Resources Planning and Management', 'transport': 'Journal of Transportation Engineering, Part A: Systems', 'bridge': 'Journal of Bridge Engineering', 'aerospace': 'Journal of Aerospace Engineering'}
EXTRA_FEEDS = {'ajrua6': 'ASCE-ASME Journal of Risk and Uncertainty in Engineering Systems, Part A: Civil Engineering', 'ijgnai': 'International Journal of Geomechanics', 'jaeied': 'Journal of Architectural Engineering', 'jceecd': 'Journal of Civil Engineering Education', 'jcrgei': 'Journal of Cold Regions Engineering', 'jccof2': 'Journal of Composites for Construction', 'jccee5': 'Journal of Computing in Civil Engineering', 'jleed9': 'Journal of Energy Engineering', 'jenmdt': 'Journal of Engineering Mechanics', 'jhtrbp': 'Journal of Hazardous, Toxic, and Radioactive Waste', 'jhtrcq': 'Journal of Highway and Transportation Research and Development (English Edition)', 'jhend8': 'Journal of Hydraulic Engineering', 'jhyeff': 'Journal of Hydrologic Engineering', 'jitse4': 'Journal of Infrastructure Systems', 'jidedh': 'Journal of Irrigation and Drainage Engineering', 'jladah': 'Journal of Legal Affairs and Dispute Resolution in Engineering and Construction', 'jmenea': 'Journal of Management in Engineering', 'jmcee7': 'Journal of Materials in Civil Engineering', 'jpcfev': 'Journal of Performance of Constructed Facilities', 'jpsea2': 'Journal of Pipeline Systems Engineering and Practice', 'jsued2': 'Journal of Surveying Engineering', 'jswbay': 'Journal of Sustainable Water in the Built Environment', 'jpeodx': 'Journal of Transportation Engineering, Part B: Pavements', 'jwped5': 'Journal of Waterway, Port, Coastal, and Ocean Engineering', 'nhrefo': 'Natural Hazards Review', 'ppscfx': 'Practice Periodical on Structural Design and Construction'}
FEEDS.update({code: code for code in EXTRA_FEEDS})
EXPECTED.update(EXTRA_FEEDS)
URL = 'https://ascelibrary.org/action/showFeed'
RSS = '{http://purl.org/rss/1.0/}'
DC = '{http://purl.org/dc/elements/1.1/}'

def read(feed='construction', keyword='', limit=10, timeout=20):
    if feed not in FEEDS:
        raise ValueError('unsupported ASCE feed')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword must be at most 100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    r = requests.get(URL, params={'type': 'etoc', 'feed': 'rss', 'jc': FEEDS[feed]}, timeout=timeout)
    r.raise_for_status()
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as exc:
        raise ValueError('response is not RSS XML') from exc
    channel = root.find(RSS + 'channel')
    items = root.findall(RSS + 'item')
    if channel is None or channel.findtext(RSS + 'title') is None:
        raise ValueError('RSS channel not recognized')
    if EXPECTED[feed].casefold() not in channel.findtext(RSS + 'title').casefold():
        raise ValueError('RSS channel does not match the requested journal')
    rows = [{'title': i.findtext(RSS + 'title'), 'url': i.findtext(RSS + 'link'), 'date': i.findtext(DC + 'date')} for i in items]
    matches = [i for i in rows if keyword.casefold() in (i['title'] or '').casefold()]
    return {'source': 'ASCE Library official RSS', 'feed_name': channel.findtext(RSS + 'title'), 'keyword': keyword, 'total_in_feed': len(rows), 'matches_in_feed': len(matches), 'items': matches[:limit], 'note': '仅当前订阅源本地筛选，非期刊全库或历史检索；不证明全文或 AI 用途许可。'}
