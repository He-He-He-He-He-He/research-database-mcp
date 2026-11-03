"""Search raw state rows of Census ACSBR-025 Appendix Table 1."""
import release_runtime
import re, subprocess, fitz
URL = 'https://www2.census.gov/library/publications/2025/demo/acsbr-025.pdf'
PAGE = 'https://www.census.gov/library/publications/2025/acs/acsbr-025.html'

def find(geography, limit=5):
    if not isinstance(geography, str) or not geography.strip() or len(geography) > 100:
        raise ValueError('geography required')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '30', '--max-filesize', '5000000', URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Census report download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 5000000 or not p.stdout.startswith(b'%PDF'):
        raise RuntimeError('Invalid Census PDF')
    with fitz.open(stream=p.stdout, filetype='pdf') as d:
        if len(d) < 8:
            raise RuntimeError('Unexpected report length')
        t = d[7].get_text(sort=True)
    if 'Appendix Table 1.' not in t or 'Median Household Income and Gini Index' not in t or '90 percent confidence' not in t:
        raise RuntimeError('Report structure changed')
    rows = []
    for line in t.splitlines():
        m = re.match('^([A-Za-z][A-Za-z ]+?)\\s+(?:\\.\\s*){2,}\\s*(.*)$', line)
        if m and geography.casefold() in m.group(1).casefold():
            rows.append({'geography': m.group(1).strip(), 'raw_row': line.strip()})
    return {'source': 'US Census Bureau ACSBR-025 Appendix Table 1', 'source_page': PAGE, 'pdf_url': URL, 'physical_pdf_page': 8, 'query': geography, 'matches': len(rows), 'items': rows[:limit], 'columns': ['2023 median household income estimate', '2023 income margin of error', '2024 income estimate', '2024 income margin of error', 'income percent change', 'income percent change margin of error', '2023 Gini estimate', '2023 Gini margin of error', '2024 Gini estimate', '2024 Gini margin of error', 'Gini percent change', 'Gini percent change margin of error'], 'note': '2023 and 2024 income are in 2024 inflation-adjusted USD. Margins form 90% confidence intervals. * means statistically different from zero at 90%; Z is zero or rounds to zero. Household population excludes group quarters. Raw PDF text may have extraction/layout defects; verify original page and notes.'}
