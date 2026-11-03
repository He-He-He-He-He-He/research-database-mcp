"""重庆市卫生健康委年鉴转引全国分省卫生资源表（2021–2023）。"""
import release_runtime
import argparse
import hashlib
import json
import re
import requests
SOURCES = {2021: (2023, 'https://wsjkw.cq.gov.cn/zwgk_242/fdzdgknr/tjxx/sjzl/ndzl/202506/W020251231360427587692.pdf'), 2022: (2024, 'https://wsjkw.cq.gov.cn/zwgk_242/fdzdgknr/tjxx/sjzl/ndzl/202503/W020250327356379362444.pdf'), 2023: (2025, 'https://wsjkw.cq.gov.cn/zwgk_242/fdzdgknr/tjxx/sjzl/ndzl/202602/W020260213388117019353.pdf')}
REGIONS = '全国 重庆 北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆'.split()
FIELDS = ['机构数', '实有床位数_张', '每千人口医疗卫生机构床位数', '每千人口卫生技术人员数', '每千人口执业（助理）医师数', '每千人口注册护士数']

def get_data(year, region=None):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('需要安装 PyMuPDF 才能读取官方 PDF') from exc
    if year not in SOURCES:
        raise ValueError('仅支持 2021、2022、2023 数据年份')
    edition, url = SOURCES[year]
    with requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=45, stream=True) as response:
        response.raise_for_status()
        chunks, size = ([], 0)
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 20000000:
                raise ValueError('PDF 超过大小限制')
            chunks.append(chunk)
        data = b''.join(chunks)
    if len(data) > 20000000 or not data.startswith(b'%PDF-'):
        raise ValueError('来源未返回预期大小的 PDF')
    doc = fitz.open(stream=data, filetype='pdf')
    title = f'表12.8{year}年全国各地区主要指标'
    matches = [(i, p.get_text()) for i, p in enumerate(doc) if title in ''.join(p.get_text().split()) and '实有床位数' in p.get_text() and (len(p.get_text()) > 500)]
    if len(matches) != 1:
        raise ValueError('无法唯一定位表格，请检查官方文件是否变更')
    index, page = matches[0]
    lines = [re.sub('\\s+', '', x) for x in page.splitlines()]
    rows = []
    for i, line in enumerate(lines):
        if line not in REGIONS:
            continue
        values = lines[i + 1:i + 7]
        if len(values) != 6 or not all((re.fullmatch('\\d+(?:\\.\\d+)?', v) for v in values)):
            raise ValueError(f'{line} 数据列不完整，停止解析')
        rows.append({'地区': line, **{field: int(value) if j < 2 else float(value) for j, (field, value) in enumerate(zip(FIELDS, values))}})
    if len(rows) != len(REGIONS) or [r['地区'] for r in rows] != REGIONS:
        raise ValueError('地区数或顺序与预期不符，停止解析')
    if region:
        rows = [row for row in rows if row['地区'] == region]
        if not rows:
            raise ValueError('地区名称不在全国或31个省级地区中')
    note = next((line for line in page.splitlines() if line.strip().startswith('注：')), '')
    return {'数据年份': year, '年鉴版次': edition, '表名': title, 'PDF页码': index + 1, '来源': url, '文件SHA256': hashlib.sha256(data).hexdigest(), '原表注释': note, '范围与限制': '重庆市卫生健康委年鉴转引全国卫生健康统计年鉴；仅提取原表左半部分六项，不包含续页诊疗指标。2021数据表注称引自2021版年鉴，表题与来源版次存在疑点，尚未核对原年鉴；使用2021数据前请核实。', '数据': rows}
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('year', type=int, choices=SOURCES)
    parser.add_argument('--region')
    args = parser.parse_args()
    print(json.dumps(get_data(args.year, args.region), ensure_ascii=False, indent=2))
