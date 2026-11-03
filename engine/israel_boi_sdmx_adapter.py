"""Bank of Israel time-series API, bounded CSV queries."""
import release_runtime
import csv
import io
import re
import subprocess
from datetime import date
from urllib.parse import urlencode
BASE = 'https://edge.boi.org.il/FusionEdgeServer/sdmx/v2/data/dataflow/BOI.STATISTICS/'

def observations(flow, series, start, end, limit=1000):
    if not isinstance(flow, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', flow):
        raise ValueError('Invalid dataflow')
    if not isinstance(series, list) or not 1 <= len(series) <= 10 or any((not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', x) for x in series)):
        raise ValueError('Supply 1–10 valid series IDs')
    a, b = (date.fromisoformat(start), date.fromisoformat(end))
    if a > b or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 10000):
        raise ValueError('Invalid date range or limit')
    query = urlencode({'format': 'csv', 'startperiod': a.isoformat(), 'endperiod': b.isoformat()})
    url = BASE + flow + '/1.0/' + ','.join(series) + '?' + query
    proc = release_runtime.run(['/usr/bin/curl', '-q', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('Bank of Israel request failed: ' + proc.stderr.decode('utf8', 'replace').strip())
    if len(proc.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    rows = list(csv.DictReader(io.StringIO(proc.stdout.decode('utf-8-sig'))))
    return {'source': 'Bank of Israel', 'url': url, 'returned': min(len(rows), limit), 'matched': len(rows), 'truncated': len(rows) > limit, 'rows': rows[:limit]}
