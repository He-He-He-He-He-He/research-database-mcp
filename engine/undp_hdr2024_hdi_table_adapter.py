"""UNDP HDR 2023/2024 statistical annex table 1, raw cells and footnotes."""
import release_runtime
import io, re, subprocess
import openpyxl
URL = 'https://hdr.undp.org/sites/default/files/2023-24_HDR/HDR23-24_Statistical_Annex_HDI_Table.xlsx'

def search(keyword, version='2024'):
    if version not in ('2025', '2024', '2022'):
        raise ValueError('版本须为 2025、2024 或 2022')
    url = {'2025': 'https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Statistical_Annex_HDI_Table.xlsx', '2024': URL, '2022': 'https://hdr.undp.org/sites/default/files/2021-22_HDR/HDR21-22_Statistical_Annex_HDI_Table.xlsx'}[version]
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入不超过150字符的关键词')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '1000000', url], capture_output=True, timeout=35)
    if p.returncode or len(p.stdout) > 1000000:
        raise RuntimeError('UNDP 附表下载失败')
    book = openpyxl.load_workbook(io.BytesIO(p.stdout), data_only=False)
    try:
        s = book[{'2025': 'Table 1. HDI', '2024': 'HDI', '2022': 'Table 1'}[version]]

        def cells(row):
            return [{'cell': c.coordinate, 'value': c.value, 'number_format': c.number_format} for c in row if c.value is not None]
        hits = [cells(row) for row in s.iter_rows(min_row=8, max_row=230) if any((keyword.casefold() in str(c.value).casefold() for c in row if c.value is not None))]
        header = [cells(row) for row in s.iter_rows(min_row=1, max_row=7) if any((c.value is not None for c in row))]
        notes = [cells(row) for row in s.iter_rows(min_row=232, max_row=s.max_row) if any((c.value is not None for c in row))]
        return {'source': url, 'report': {'2025': 'Human Development Report 2025, Table 1', '2024': 'Human Development Report 2023/2024, Table 1', '2022': 'Human Development Report 2021/2022, Table 1'}[version], 'reference_year': {'2025': '2023', '2024': '2022', '2022': '2021'}[version] + '; individual schooling values may use most recent year available', 'server_last_modified_observed': {'2025': '2025-05-06 12:55:01 GMT', '2024': '2024-03-13 15:11:12 GMT', '2022': '2022-09-07 17:47:55 GMT'}[version] + ' (observed 2026-11-02; does not independently prove immutable historical content)', 'keyword': keyword, 'headers': header, 'results': hits, 'notes_definitions_sources': notes, 'caution': '原始单元格数值可能比报告显示精度更高；须参照数字格式。前一年排名为各自报告同方法和修订数据重算，不能视作旧版排名；不同报告版本不宜直接比较变化。2025版 PPP 为2021国际美元，2024和2022版为2017国际美元，不直接比较。空值不是零；附注可能标示估计、年份与截顶。关键词是本地文本匹配，不证明返回完整国家范围。'}
    finally:
        book.close()
