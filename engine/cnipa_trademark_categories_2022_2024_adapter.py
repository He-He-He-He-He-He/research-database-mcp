"""CNIPA trademark quarterly regional Nice-class PDFs; original text coordinates."""
import release_runtime
import hashlib, re
import fitz, requests
SOURCES = {'2022Q4': 'https://sbj.cnipa.gov.cn/sbj/sbsj/202301/W020230119542417395809.pdf', '2023Q1': 'https://sbj.cnipa.gov.cn/sbj/sbsj/202304/W020230412530501981696.pdf', '2023Q2': 'https://sbj.cnipa.gov.cn/sbj/sbsj/202307/W020230705353683450217.pdf', '2024Q3': 'https://sbj.cnipa.gov.cn/sbj/sbsj/202410/W020241014382030664202.pdf', '2024Q4': 'https://sbj.cnipa.gov.cn/sbj/sbsj/202501/W020250103577772112913.pdf'}
REGIONS = ['北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省', '黑龙江省', '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省', '广东省', '广西壮族自治区', '海南省', '重庆市', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区', '台湾省', '香港特别行政区', '澳门特别行政区', '合计']
TYPES = ['注册申请量', '注册量', '有效注册量']

def catalog():
    return [{'period': k, 'url': u} for k, u in SOURCES.items()]

def table(period, metric, region=''):
    if not isinstance(period, str) or period not in SOURCES:
        raise ValueError('period not available; consult catalog')
    if metric not in TYPES:
        raise ValueError('metric must be 注册申请量, 注册量, or 有效注册量')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    with requests.get(SOURCES[period], stream=True, timeout=(10, 40), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 10000000:
                raise ValueError('PDF too large')
    raw = bytes(raw)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    with fitz.open(stream=raw, filetype='pdf') as d:
        if len(d) != 1 or d[0].rotation != 90:
            raise ValueError('unexpected PDF layout')
        p = d[0]
        words = p.get_text('words')
        paragraphs = p.get_text()
        snippets = re.findall('说明：统计数据为[^。]+。', paragraphs)
        if len(snippets) != 3:
            raise ValueError('statistical period descriptions missing')
        rows = []
        idx = TYPES.index(metric)
        for name in REGIONS:
            anchors = sorted([w for w in words if w[4] == name and w[1] > 3300], key=lambda x: x[0])
            if len(anchors) != 3:
                raise ValueError('region anchors missing or ambiguous: ' + name)
            anchor = anchors[idx]
            center = (anchor[0] + anchor[2]) / 2
            line = sorted([w for w in words if abs((w[0] + w[2]) / 2 - center) < 3 and re.fullmatch('\\d+', w[4])], key=lambda w: -w[1])
            if len(line) != 46:
                raise ValueError('table row has unexpected number of columns: ' + name)
            numbers = [w[4] for w in line]
            if sum(map(int, numbers[:-1])) != int(numbers[-1]):
                raise ValueError('class totals do not match: ' + name)
            if region in name:
                rows.append({'region': name, 'nice_class_counts': {str(i): numbers[i - 1] for i in range(1, 46)}, 'total': numbers[-1]})
        return {'source': '国家知识产权局商标局', 'period': period, 'metric': metric, 'source_url': SOURCES[period], 'sha256': hashlib.sha256(raw).hexdigest(), 'source_period_note': snippets[idx], 'unit': '件', 'total_rows': len(REGIONS), 'rows': rows, 'note': '根据原生PDF旋转版面坐标读取尼斯45类；逐行核验分类总和。申请量和注册量为报告所注明的累计期间，不能按季度名称误认为单季度值；有效注册量为指定时点存量，统计范围和比较应看原表。'}
