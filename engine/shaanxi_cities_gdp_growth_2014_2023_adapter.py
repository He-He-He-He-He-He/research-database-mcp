"""Shaanxi city GDP growth 2014–2023, Baoji statistical yearbook 2024."""
import release_runtime
import hashlib, re
import fitz, requests
URL = 'https://tjj.baoji.gov.cn/zzzb/tjnj/202506/P020250928637183356569.pdf'
CITIES = ['西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市', '杨凌示范区']

def catalog():
    return {'source': '宝鸡市统计局《宝鸡统计年鉴》2023年资料', 'url': URL, 'pdf_page': 39, 'years': list(range(2014, 2024)), 'cities': CITIES, 'unit': '%', 'note': '按可比价格计算的地区生产总值同比增速；历史数为该年鉴发布版本，不代表最新修订。'}

def table(city='', year=None):
    if not isinstance(city, str) or len(city) > 30:
        raise ValueError('invalid city')
    if year is not None and (type(year) is not int or year not in range(2014, 2024)):
        raise ValueError('year must be 2014–2023')
    with requests.get(URL, stream=True, timeout=(10, 50), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 15000000:
                raise ValueError('PDF too large')
    raw = bytes(data)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if len(doc) != 285:
            raise ValueError('unexpected PDF version')
        p = doc[38]
        words = p.get_text('words')
        text = ''.join(p.get_text().split())
        if '全省各市（区）生产总值比上年增长速度' not in text:
            raise ValueError('expected table title missing')
        records = []
        for name in CITIES:
            anchors = {(round(w[0], 2), round(w[1], 2)) for w in words if w[4] == name and w[1] > 500}
            if len(anchors) != 1:
                raise ValueError('ambiguous city anchor: ' + name)
            _, cy = next(iter(anchors))
            for y in range(2014, 2024):
                years = {(round(w[0], 2), round(w[1], 2)) for w in words if w[4] == str(y) and 480 < w[1] < 510}
                if len(years) != 1:
                    raise ValueError('ambiguous year anchor')
                xx, _ = next(iter(years))
                values = [w[4] for w in words if abs(w[2] - (xx + 30.2)) < 2 and abs(w[1] - cy) < 6 and re.fullmatch('[﹣−-]?\\d+\\.\\d+', w[4])]
                if len(values) != 1:
                    raise ValueError(f'could not verify value: {name} {y}')
                if city in name and (year is None or year == y):
                    records.append({'city': name, 'year': y, 'growth_percent': values[0].replace('﹣', '-').replace('−', '-')})
    return {'source': '宝鸡市统计局《宝鸡统计年鉴》2023年资料', 'source_url': URL, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'pdf_page': 39, 'unit': '%', 'rows': records, 'note': '陕西各市及杨凌示范区地区生产总值同比增长率，按可比价格计算；保留2023年资料原始历史数，并非最新修订版。原PDF原生文本坐标提取、逐值唯一性校验。'}
