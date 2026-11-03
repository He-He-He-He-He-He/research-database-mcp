"""World Bank Projects & Operations API: search worldwide project records.

Source: https://datahelpdesk.worldbank.org/knowledgebase/articles/889386-developer-information-overview
Projects and financing amounts are returned as originally published; do not infer
currency, scale, commitments versus disbursements, or current project status.
"""
import release_runtime
import json, subprocess
from urllib.parse import urlencode
BASE = 'https://search.worldbank.org/api/v2/projects'
MAX_BYTES = 8000000

def search(keyword, offset=0, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('keyword must be 1 to 200 characters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 50):
        raise ValueError('offset must be nonnegative and limit 1 to 50')
    url = BASE + '?' + urlencode({'format': 'json', 'qterm': keyword, 'rows': limit, 'os': offset})
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('World Bank projects API failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('project response exceeds 8 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or not isinstance(obj.get('projects'), dict) or 'total' not in obj:
        raise ValueError('unexpected World Bank projects response')
    return {'source': url, 'response': obj, 'note': 'Results are World Bank project records, not statistical time series. Project commitments and other monetary fields must be interpreted using their official metadata.'}
