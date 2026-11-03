"""Public Crossref metadata for three journals named by ZJU library (RUP 1599)."""
import release_runtime
from crossref_journal_general_adapters import journal_works
_JOURNALS = {'jcb': ('The Journal of Cell Biology', '0021-9525'), 'jem': ('The Journal of Experimental Medicine', '0022-1007'), 'jgp': ('The Journal of General Physiology', '0022-1295')}

def search(keyword, journal='jcb', size=10, offset=0):
    if journal not in _JOURNALS:
        raise ValueError('journal must be jcb, jem, or jgp')
    title, issn = _JOURNALS[journal]
    result = journal_works(issn, keyword, size, offset)
    result.update({'journal': title, 'issn': issn, 'library_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1599', 'note': 'Crossref public metadata for the three journals named in the library introduction, not verified institutional access or full-text entitlements.'})
    return result
