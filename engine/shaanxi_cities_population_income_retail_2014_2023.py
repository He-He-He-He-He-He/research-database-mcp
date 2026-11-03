"""Shaanxi 11 cities/regions population, income and retail, 2014–2023."""
import release_runtime
import hashlib, re
import fitz, requests
URL = 'https://tjj.baoji.gov.cn/zzzb/tjnj/202506/P020250928637183356569.pdf'
CITIES = ['西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市', '杨凌示范区']
METRICS = {'retail': {'page': 42, 'name': '社会消费品零售总额', 'unit': '亿元', 'city_y': (145, 440), 'year_y': (110, 150), 'note': '各年为该年鉴版本；使用前核查统计调整。'}, 'urban_income': {'page': 42, 'name': '城镇居民人均可支配收入', 'unit': '元', 'city_y': (500, 750), 'year_y': (460, 500), 'note': '原表注明2014年为老口径，2015年起调整为新口径。'}, 'rural_income': {'page': 43, 'name': '农民人均收入', 'unit': '元', 'city_y': (145, 430), 'year_y': (110, 150), 'note': '原表注明2014年为农民人均纯收入，2015年起为农民人均可支配收入，跨年指标口径不同。'}, 'population': {'page': 43, 'name': '年末常住人口', 'unit': '万人', 'city_y': (500, 760), 'year_y': (460, 500), 'note': '原表标题为年末常住人口；该年鉴历史数可能与后续普查修订版不同。'}}

def catalog():
    return [{'metric': k, 'name': v['name'], 'unit': v['unit'], 'pdf_page': v['page'], 'years': list(range(2014, 2024)), 'note': v['note']} for k, v in METRICS.items()]

def table(metric, city='', year=None):
    if not isinstance(metric, str) or metric not in METRICS:
        raise ValueError('invalid metric')
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
    config = METRICS[metric]
    records = []
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if len(doc) != 285:
            raise ValueError('unexpected PDF version')
        p = doc[config['page'] - 1]
        words = p.get_text('words')
        for name in CITIES:
            lo, hi = config['city_y']
            cs = {(round(w[0], 2), round(w[1], 2)) for w in words if w[4] == name and lo < w[1] < hi}
            if len(cs) != 1:
                raise ValueError('ambiguous city anchor ' + name)
            _, cy = next(iter(cs))
            for y in range(2014, 2024):
                lo, hi = config['year_y']
                ys = {(round(w[0], 2), round(w[1], 2)) for w in words if w[4] == str(y) and lo < w[1] < hi}
                if len(ys) != 1:
                    raise ValueError('ambiguous year anchor')
                xx, _ = next(iter(ys))
                values = [w[4] for w in words if abs(w[2] - (xx + 30)) < 4 and abs(w[1] - cy) < 6 and re.fullmatch('\\d+(?:\\.\\d+)?', w[4])]
                if len(values) != 1:
                    raise ValueError(f'could not uniquely verify value: {name} {y}')
                if city in name and (year is None or year == y):
                    records.append({'city': name, 'year': y, 'value': values[0]})
    return {'source': '宝鸡统计年鉴2023年资料', 'source_url': URL, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'metric': metric, 'name': config['name'], 'unit': config['unit'], 'pdf_page': config['page'], 'rows': records, 'note': config['note'] + ' 按原生PDF坐标读取，逐值唯一校验；该年鉴版本不代表最新修订。'}
