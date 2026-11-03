"""IMF credit outstanding to members at a selected date, original SDR values."""
import release_runtime
import argparse, csv, datetime, io, json, re, requests
URL = 'https://www.imf.org/external/np/fin/tad/extcred2.aspx'

def query(date, member='', limit=100):
    try:
        d = datetime.date.fromisoformat(date)
    except (TypeError, ValueError):
        raise ValueError('date must be ISO YYYY-MM-DD') from None
    if not 2000 <= d.year <= 2100 or not isinstance(member, str) or len(member) > 100 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 300):
        raise ValueError('invalid date, member or limit')
    r = requests.get(URL, params={'tsvflag': 'Y', 'reportdate': date}, timeout=45)
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('unexpected response size')
    lines = r.text.splitlines()
    if len(lines) < 4 or '(in SDRs)' not in lines[1]:
        raise ValueError('unexpected IMF table or unit')
    m = re.fullmatch('IMF Credit Outstanding for all members as of ([A-Za-z]+ \\d{1,2}, \\d{4})', lines[0].strip())
    if not m or datetime.datetime.strptime(m.group(1), '%B %d, %Y').date() != d:
        raise ValueError('IMF returned a different reporting date')
    reader = csv.reader(io.StringIO('\n'.join(lines[3:])), delimiter='\t')
    header = next(reader, None)
    if not header or header[0] != 'Member' or header[-1] != 'Totals':
        raise ValueError('unexpected table header')
    out = []
    total = 0
    for row in reader:
        if len(row) != len(header) or not row[0].strip() or member.casefold() not in row[0].casefold():
            continue
        vals = []
        for value in row[1:]:
            clean = value.strip().replace(',', '')
            if not re.fullmatch('\\d+', clean):
                break
            vals.append(int(clean))
        if len(vals) != len(header) - 1:
            continue
        total += 1
        if len(out) < limit:
            out.append({'member': row[0].strip(), 'values': dict(zip(header[1:], vals))})
    return {'provider': 'International Monetary Fund', 'source': r.url, 'report_date': date, 'unit': 'SDR (Special Drawing Rights)', 'header': header, 'matched_count': total, 'records': out, 'notes': [line.strip() for line in lines if re.match('^\\s*[12]/', line)], 'note': 'Outstanding IMF credit at the report date, not total external debt or new annual borrowing. Country absence does not imply a reported zero. Preserve program categories, report date and IMF footnotes.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('date')
    p.add_argument('--member', default='')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.date, a.member, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
