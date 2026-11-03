"""2026 年国家网信办生成式 AI 备案公告统计摘要。"""
import release_runtime
from jiangsu_cyberspace_policies_adapters import jiangsu_cyberspace_policy_detail
PERIODS = {'2026_01-02': {'mirror': 'https://www.jswx.gov.cn/fwhd/tzgg/202603/t20260317_1316018.shtml', 'as_of': '2026-02-28', 'new_registered': 48, 'new_filed': 46, 'cumulative_registered': 796, 'cumulative_filed': 481}, '2026_03-04': {'mirror': 'https://www.jswx.gov.cn/fwhd/tzgg/202605/t20260513_1329727.shtml', 'as_of': '2026-04-30', 'new_registered': 72, 'new_filed': 49, 'cumulative_registered': 868, 'cumulative_filed': 530}, '2026_05-06': {'mirror': 'https://www.jswx.gov.cn/fwhd/tzgg/202607/t20260710_1343807.shtml', 'as_of': '2026-06-30', 'new_registered': 120, 'new_filed': 68, 'cumulative_registered': 988, 'cumulative_filed': 598}, '2026_07-08': {'mirror': 'https://www.jswx.gov.cn/fwhd/tzgg/202609/t20260914_1358593.shtml', 'as_of': '2026-08-31', 'new_registered': 124, 'new_filed': 133, 'cumulative_registered': 1112, 'cumulative_filed': 731, 'new_mobile_included': 7}}

def cac_genai_2026_summaries():
    """读取四篇网信公告转载，核对摘要数字并返回不同口径。"""
    rows = []
    for period, data in PERIODS.items():
        detail = jiangsu_cyberspace_policy_detail(data['mirror'])
        text = detail['text']
        expected = [data['new_registered'], data['new_filed'], data['cumulative_registered'], data['cumulative_filed']]
        if any((str(number) + '款' not in text for number in expected)) or (period == '2026_07-08' and '7款提供手机端侧' not in text):
            raise ValueError(f'{period} 公告正文与已核对摘要不一致，停止输出')
        rows.append({'period': period, **data, 'unit': '款', 'source_text': text, 'note': '7—8 月的手机端侧 7 款包含在新增备案 124 款中，不可重复相加；数量是公告时点口径。'})
    return rows
