"""全国住房公积金2024年年度报告表1：地区缴存情况。"""
import release_runtime
import argparse, hashlib, io, json, re, subprocess, sys
try:
    import pdfplumber
except ImportError:
    raise SystemExit('需要 Python pdfplumber；可使用本机 Codex bundled Python 运行')
URL = 'https://www.gov.cn/zhengce/zhengceku/202506/P020250601601759182303.pdf'
PAT = re.compile('^([\\u4e00-\\u9fff]+)\\s+(\\d+\\.\\d{2})\\s+(\\d+\\.\\d{2})\\s+(\\d+\\.\\d{2})\\s+(\\d+\\.\\d{2})\\s+(\\d+\\.\\d{2})$')
REGIONS = '全国 北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆 新疆兵团'.split()

def get_table(region=''):
    data = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '5242880', URL], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    if not data.startswith(b'%PDF-') or len(data) > 5242880:
        raise ValueError('上游不是受支持 PDF')
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        if len(pdf.pages) < 3:
            raise ValueError('PDF 页数异常')
        text = (pdf.pages[1].extract_text() or '') + '\n' + (pdf.pages[2].extract_text() or '')
    if '2024 年分地区住房公积金缴存情况' not in text:
        raise ValueError('未发现目标表标题')
    text = text.split('2024 年分地区住房公积金缴存情况', 1)[1].split('2024 年分类型单位住房公积金缴存情况', 1)[0]
    rows = []
    for line in text.splitlines():
        m = PAT.fullmatch(line.strip())
        if m:
            x = m.groups()
            rows.append(dict(zip(['region', 'paid_units_10k', 'paid_people_10k', 'annual_deposits_100m_yuan', 'cumulative_deposits_100m_yuan', 'deposit_balance_100m_yuan'], x)))
    if [x['region'] for x in rows] != REGIONS:
        raise ValueError('地区顺序或表格行数变化，请核验原始PDF')
    return {'year': 2024, 'source': URL, 'sha256': hashlib.sha256(data).hexdigest(), 'table': '表1 分地区住房公积金缴存情况', 'scope': '全国、31个省级地区和新疆兵团；单位分别为万个、万人、亿元', 'items': [x for x in rows if region in x['region']]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--region', default='')
    a = p.parse_args()
    print(json.dumps(get_table(a.region), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
