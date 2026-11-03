"""Official China 2024 ODI bulletin: provincial non-financial flow and stock."""
import release_runtime
import hashlib, re, unicodedata
import fitz, requests
URL = 'https://www.gov.cn/lianbo/bumen/202509/P020250908508134967854.pdf'
REGIONS = ['北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省', '黑龙江省', '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省', '广东省', '广西壮族自治区', '海南省', '重庆市', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区', '新疆生产建设兵团']
METRICS = {'flow': {'page': 64, 'name': '对外非金融类直接投资流量', 'title': '2016—2024年中国对外非金融类直接投资流量情况'}, 'stock': {'page': 65, 'name': '年末对外非金融类直接投资存量', 'title': '2016—2024年末中国对外非金融类直接投资存量情况'}}

def catalog():
    return [{'metric': k, 'name': v['name'], 'pdf_page': v['page'], 'years': list(range(2016, 2025)), 'unit': '万美元'} for k, v in METRICS.items()]

def table(metric, region='', year=None):
    if not isinstance(metric, str) or metric not in METRICS:
        raise ValueError('metric must be flow or stock')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    if year is not None and (type(year) is not int or year not in range(2016, 2025)):
        raise ValueError('year must be 2016–2024')
    with requests.get(URL, stream=True, timeout=(15, 90), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 18000000:
                raise ValueError('PDF too large')
    raw = bytes(data)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    cfg = METRICS[metric]
    rows = []
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if len(doc) != 68:
            raise ValueError('unexpected PDF version')
        page = doc[cfg['page'] - 1]
        text = unicodedata.normalize('NFKC', ''.join(page.get_text().split()))
        if cfg['title'] not in text or '单位:万美元' not in text:
            raise ValueError('table title or unit mismatch')
        words = page.get_text('words')
        chars = [c for b in page.get_text('rawdict')['blocks'] for line in b.get('lines', []) for span in line['spans'] for c in span['chars']]
        chars.sort(key=lambda c: c['bbox'][0])
        for name in REGIONS:
            anchors = [w for w in words if unicodedata.normalize('NFKC', w[4]) == name]
            if len(anchors) != 1:
                raise ValueError('ambiguous region anchor ' + name)
            anchor = anchors[0]
            for i in range(9):
                y = 2016 + i
                lo = 140 + i * 45.1
                hi = lo + 45.1
                value = ''.join((unicodedata.normalize('NFKC', c['c']) for c in chars if lo <= c['bbox'][0] < hi and abs(c['bbox'][1] - (anchor[1] - 4.1)) < 2)).strip()
                if not re.fullmatch('-?\\d+', value):
                    raise ValueError(f'cannot uniquely parse {name} {y}')
                if region in name and (year is None or year == y):
                    rows.append({'region': name, 'year': y, 'value': value})
    return {'source': '商务部、国家统计局、国家外汇管理局《2024年度中国对外直接投资统计公报》', 'source_url': URL, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'metric': metric, 'name': cfg['name'], 'unit': '万美元', 'pdf_page': cfg['page'], 'rows': rows, 'note': '省级口径为境内投资者所在地区、非金融类；另列新疆生产建设兵团，不包含中央合计及计划单列市细项。流量为年度发生额，存量为年末余额，不可混淆或跨地区随意叠加。原报告历史数可能修订。PDF原生文字按坐标解析，非OCR。'}
