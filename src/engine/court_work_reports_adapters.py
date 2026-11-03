"""最高人民法院公开工作报告原文（指定会议年份）。"""
import release_runtime
from legal_adapters import CaseDetail
from court_judicial_statistics_adapters import _get
REPORTS = {2023: ('2018—2022 年五年工作及 2023 年建议', 'https://www.court.gov.cn/zixun/xiangqing/393751.html'), 2025: ('2024 年工作回顾及 2025 年安排', 'https://www.court.gov.cn/zixun/xiangqing/457991.html'), 2026: ('2025 年工作及 2026 年安排', 'https://www.court.gov.cn/zixun/xiangqing/494821.html')}

def court_work_reports_list():
    return [{'meeting_year': y, 'coverage': r[0], 'url': r[1]} for y, r in REPORTS.items()]

def court_work_report(year):
    year = int(year)
    if year not in REPORTS:
        raise ValueError('仅支持会议年份 2023、2025、2026')
    scope, url = REPORTS[year]
    parser = CaseDetail()
    parser.feed(_get(url))
    text = '\n'.join((line.strip() for line in ''.join(parser.text).splitlines() if line.strip()))
    if not parser.found or len(text) < 1000 or '最高人民法院工作报告' not in text:
        raise ValueError('未识别工作报告正文，网站可能改版')
    return {'meeting_year': year, 'coverage': scope, 'source_url': url, 'text': text, 'note': '会议年份与回顾年份不同；2018—2022 为五年累计，报告中的案件数、人数、金额等应依原文口径解释。'}
