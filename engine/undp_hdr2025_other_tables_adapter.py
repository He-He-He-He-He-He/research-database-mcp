"""UNDP HDR 2025 official statistical annex tables 3, 4, 5, 7."""
import release_runtime
import io, subprocess
import openpyxl
TABLES = {'3': ('IHDI', 'Table 3. IHDI'), '4': ('GDI', 'Table 4. GDI'), '5': ('GII', 'Table 5. GII'), '7': ('PHDI', 'Table 7. PHDI')}
BASE = 'https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Statistical_Annex_{}_Table.xlsx'

def search(table, keyword, version='2025'):
    if version not in ('2025', '2024', '2022'):
        raise ValueError('版本应为 2025、2024 或 2022')
    if version in ('2024', '2022') and str(table) == '3':
        raise ValueError('此历史版附表 3 暂未接通')
    if str(table) not in TABLES:
        raise ValueError('表号须为 3、4、5 或 7')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('关键词须为 1 至 150 字符')
    code, sheet = TABLES[str(table)]
    if version == '2024':
        url = f'https://hdr.undp.org/sites/default/files/2023-24_HDR/HDR23-24_Statistical_Annex_{code}_Table.xlsx'
        sheet = {'4': 'Table 4', '5': 'Table 5', '7': 'PHDI'}[str(table)]
    elif version == '2022':
        url = f'https://hdr.undp.org/sites/default/files/2021-22_HDR/HDR21-22_Statistical_Annex_{code}_Table.xlsx'
        sheet = {'4': 'Table 4', '5': 'Table 5', '7': 'Table 7'}[str(table)]
    else:
        url = BASE.format(code)
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '1000000', url], capture_output=True, timeout=35)
    if p.returncode or len(p.stdout) > 1000000:
        raise RuntimeError('UNDP 附表下载失败')
    w = openpyxl.load_workbook(io.BytesIO(p.stdout), data_only=False)
    try:
        s = w[sheet]

        def cells(row):
            return [{'cell': c.coordinate, 'value': c.value, 'number_format': c.number_format} for c in row if c.value is not None]
        first = next((row[0].row for row in s if isinstance(row[0].value, int)))
        note = next((row[0].row for row in s if len(row) > 1 and str(row[1].value).strip().lower() in ('notes', 'footnotes')))
        headers = [cells(row) for row in s.iter_rows(min_row=1, max_row=first - 1) if any((c.value is not None for c in row))]
        hits = [cells(row) for row in s.iter_rows(min_row=first, max_row=note - 1) if len(row) > 1 and keyword.casefold() in str(row[1].value or '').casefold()]
        notes = [cells(row) for row in s.iter_rows(min_row=note, max_row=s.max_row) if any((c.value is not None for c in row))]
        return {'source': url, 'report': {'2025': 'Human Development Report 2025', '2024': 'Human Development Report 2023/2024', '2022': 'Human Development Report 2021/2022'}[version], 'report_release': {'2025': '2025-05-06', '2024': '2024-03-13', '2022': '2022-09-08'}[version], 'table': str(table), 'index': code, 'server_last_modified_observed': ('2022-09-07 ' + ('20:44:35' if code == 'PHDI' else '17:47:54') + ' GMT' if version == '2022' else '2024-03-13 15:17:24 GMT' if version == '2024' else '2025-05-06 12:55:02 GMT' if code == 'PHDI' else '2025-05-06 12:55:01 GMT') + ' (observed 2026-11-02; not proof of unchanged historical content)', 'keyword': keyword, 'headers': headers, 'results': hits, 'notes_definitions_sources': notes, 'caution': '按表头逐列确认指标、单位和年份；学校等指标可能采用最近可得年；各版的调查年份不同。原值可能高于显示精度，须参照数字格式；空缺、破折号和点号不是零。指数为 UNDP 综合估计，脚注与来源适用各表，跨报告比较应考虑修订。'}
    finally:
        w.close()
