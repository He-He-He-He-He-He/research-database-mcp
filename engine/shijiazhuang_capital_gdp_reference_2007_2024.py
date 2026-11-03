"""Shijiazhuang science information institute reference compilation of capital GDP."""
import release_runtime
import hashlib, re
import fitz, requests
URL = 'https://kjj.sjz.gov.cn/attachments/1/202510/16/统计信息专递--2025年第6期20251016161920994.pdf'
CITIES = ['石家庄', '太原', '呼和浩特', '沈阳', '长春', '哈尔滨', '南京', '杭州', '合肥', '福州', '南昌', '济南', '郑州', '武汉', '长沙', '广州', '南宁', '海口', '成都', '贵阳', '昆明', '拉萨', '西安', '兰州', '西宁', '银川', '乌鲁木齐']

def catalog():
    return {'source': '石家庄市科技信息研究所《统计信息专递》2025年第6期', 'source_url': URL, 'years': list(range(2007, 2025)), 'cities': CITIES, 'unit': '亿元', 'note': '该资料是研究所整理的参考表，未逐格标注原始统计公报或修订版本，不能当成各市统计局已验证原始数据；重要引用应逐市逐年复核。'}

def table(city='', year=None):
    if not isinstance(city, str) or len(city) > 30:
        raise ValueError('invalid city')
    if year is not None and (type(year) is not int or year not in range(2007, 2025)):
        raise ValueError('year must be 2007–2024')
    with requests.get(URL, stream=True, timeout=(10, 30), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 3000000:
                raise ValueError('PDF too large')
    raw = bytes(data)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    records = []
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if len(doc) != 2:
            raise ValueError('unexpected PDF page count')
        for index, page in enumerate(doc):
            words = page.get_text('words')
            if '全国各省会GDP年度变化情况' not in ''.join(page.get_text().split()):
                raise ValueError('table title missing')
            for name in CITIES:
                anchors = [w for w in words if w[4] == name and 100 < w[0] < 160]
                if len(anchors) != 1:
                    raise ValueError('ambiguous city ' + name)
                anchor = anchors[0]
                line = sorted([w for w in words if w[0] > 170 and abs(w[1] - anchor[1]) < 4], key=lambda w: w[0])
                if len(line) != 18:
                    raise ValueError('unexpected city row ' + name)
                for i in range(9):
                    y = 2007 + 9 * index + i
                    value = line[2 * i][4]
                    rank = line[2 * i + 1][4]
                    if not re.fullmatch('\\d+|[-—－]+', value) or not re.fullmatch('\\d+|[-—－]+', rank):
                        raise ValueError('unexpected cell')
                    if city in name and (year is None or y == year):
                        records.append({'city': name, 'year': y, 'gdp_100m_yuan': value, 'published_rank': rank})
    return {'source': '石家庄市科技信息研究所《统计信息专递》2025年第6期', 'source_url': URL, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'unit': '亿元', 'rows': records, 'note': '资料为政府科研机构根据2007–2024年省会GDP整理的参考表，未逐格标明原始数据与修订版本；可能存在历史修订或可比性差异，引用前核各地统计局原文。原表--表示缺失，排名为原作者表中排位。只读取PDF文字，并非OCR。'}
