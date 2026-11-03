"""PBC financial stability report: regional insurance premium tables 2022–2023."""
import release_runtime
import hashlib, re
import fitz, requests
URLS = {2022: 'https://www.pbc.gov.cn/jinrongwendingju/146766/146772/8ea499f9f9604fcfbd25a43b7efa5f01/2024071920310922075.pdf', 2023: 'https://www.pbc.gov.cn/jinrongwendingju/146766/146772/08b4b564775242619f8386232f9f4fae/2025010317243072518.pdf'}
COLUMNS = ['地区', '原保险保费收入', '财产保险', '寿险', '意外险', '健康险']

def catalog():
    return [{'data_year': y, 'source_url': u, 'title': f'{y}年全国各地区保费收入情况表'} for y, u in URLS.items()]

def table(year, region=''):
    if type(year) is not int or year not in URLS:
        raise ValueError('year must be 2022 or 2023')
    if not isinstance(region, str) or len(region) > 30:
        raise ValueError('invalid region')
    with requests.get(URLS[year], stream=True, timeout=(10, 60), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 15000000:
                raise ValueError('PDF too large')
    raw = bytes(data)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    with fitz.open(stream=raw, filetype='pdf') as doc:
        candidates = [(i, p) for i, p in enumerate(doc) if f'{year}年全国各地区保费收入情况表' in re.sub('\\s+', '', p.get_text())]
        if len(candidates) != 1:
            raise ValueError('report table page not uniquely identified')
        index, page = candidates[0]
        groups = {}
        for word in page.get_text('words'):
            groups.setdefault(round(word[1], 1), []).append(word)
        rows = []
        for line in groups.values():
            ws = sorted(line, key=lambda w: w[0])
            nums = [w[4] for w in ws if re.fullmatch('\\d+', w[4])]
            names = [w[4] for w in ws if not re.fullmatch('\\d+', w[4])]
            if len(nums) != 5 or not names:
                continue
            name = re.sub('\\s+', '', ''.join(names))
            if not name or not re.fullmatch('[\\u4e00-\\u9fff、]+', name):
                continue
            rows.append(dict(zip(COLUMNS, [name, *nums])))
        if len(rows) != 38 or rows[0]['地区'] != '全国合计' or rows[-1]['地区'] != '集团、总公司本级':
            raise ValueError('unexpected table layout; no result returned')
        selected = [x for x in rows if region in x['地区']]
        return {'source': '中国人民银行中国金融稳定报告，数据来源国家金融监督管理总局', 'year': year, 'source_url': URLS[year], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'pdf_page': index + 1, 'table_title': f'{year}年全国各地区保费收入情况表', 'unit': '亿元', 'columns': COLUMNS, 'total_rows': len(rows), 'rows': selected, 'note': '原表按地区含计划单列市和集团、总公司本级；地区数据不能简单与所属省份相加或视为省行政区口径。数值保留官方表中整数，舍入可能导致分项合计不等；本表按保险合同相关会计处理规定统计，详见原表下注释。PDF坐标逐行提取，表布局校验失败即报错。'}
