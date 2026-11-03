"""UNEP GEMS/Water open archive: bounded random-access to Zenodo ZIP members."""
import release_runtime
import csv, io, re, zipfile
import requests
VERSIONS = {'v2': ('14230628', 'GFQA_v2.zip', 108686194, '2024-11-27'), 'v3': ('18459694', 'GFQA_v3.zip', 201278791, '2026-02-02')}
NOTES = ['UNEP GEMS/Water open-data subset of GEMStat; coverage is selected, not all stations or countries, and does not represent all freshwater bodies.', 'Version publication date differs from sampling date. Select a version published by the research cutoff; later revisions cannot be treated as earlier snapshots.', 'All CSV fields are retained as strings, including station ID, sample date/time/depth, parameter, method, value flags, value, unit and quality. A < flag is a detection-limit qualifier, not an exact measurement; do not turn blanks into zero.', 'Compare like parameters and units and inspect station, method and quality metadata; sample values are not automatically suitable for national averages or drinking-water safety conclusions.', 'Official archive is CC BY 4.0 or equivalent, with dataset-specific attribution; use the cited Zenodo record and originating providers. File and local response size limits apply.']

class RemoteZip(io.RawIOBase):

    def __init__(self, url, size):
        self.url = url
        self.size = size
        self.pos = 0
        self.session = requests.Session()

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        if pos < 0:
            raise ValueError('Negative seek')
        self.pos = pos
        return pos

    def read(self, n=-1):
        n = max(0, self.size - self.pos) if n is None or n < 0 else min(n, max(0, self.size - self.pos))
        if not n:
            return b''
        start = self.pos
        end = start + n - 1
        with self.session.get(self.url, headers={'Range': f'bytes={start}-{end}'}, timeout=60, stream=True) as r:
            r.raise_for_status()
            if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}':
                raise ValueError('Server did not return the requested byte range')
            raw = bytearray()
            for chunk in r.iter_content(65536):
                raw.extend(chunk)
                if len(raw) > n:
                    raise ValueError('Range response too large')
        if len(raw) != n:
            raise ValueError('Incomplete range response')
        self.pos += n
        return bytes(raw)

    def close(self):
        self.session.close()
        super().close()

def _version(version):
    if version not in VERSIONS:
        raise ValueError('Unknown archive version')
    rid, name, size, pub = VERSIONS[version]
    return {'version': version, 'record_id': rid, 'publication_date': pub, 'doi': 'https://doi.org/10.5281/zenodo.' + rid, 'archive_url': f'https://zenodo.org/api/records/{rid}/files/{name}/content', 'archive_size': size}

def files(version='v2'):
    meta = _version(version)
    with RemoteZip(meta['archive_url'], meta['archive_size']) as source, zipfile.ZipFile(source) as z:
        entries = [{'name': i.filename, 'compressed_bytes': i.compress_size, 'uncompressed_bytes': i.file_size, 'readable_under_limit': i.file_size <= 25000000 and i.compress_size <= 8000000} for i in z.infolist()]
    return {'source': meta, 'notes': NOTES, 'files': entries}

def records(member, version='v2', station=None, limit=20, offset=0):
    if not isinstance(member, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}\\.csv', member) or (station is not None and (not isinstance(station, str) or not re.fullmatch('[A-Za-z0-9_-]{1,40}', station))) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('Invalid member, station or pagination')
    meta = _version(version)
    with RemoteZip(meta['archive_url'], meta['archive_size']) as source, zipfile.ZipFile(source) as z:
        try:
            i = z.getinfo(member)
        except KeyError:
            raise ValueError('Archive member not found') from None
        if i.file_size > 25000000 or i.compress_size > 8000000:
            raise ValueError('Archive member exceeds bounded read limit')
        data = z.read(i)
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''), delimiter=';' if version == 'v2' else ',')
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError('Missing or duplicate CSV columns')
    station_field = next((x for x in ('GEMS.Station.Number', 'GEMS Station Number') if x in reader.fieldnames), None)
    if station is not None and station_field is None:
        raise ValueError('This member has no station field')
    rows = []
    count = 0
    for row in reader:
        if None in row:
            raise ValueError('Unexpected CSV row width')
        if station is not None and row.get(station_field) != station:
            continue
        if offset <= count < offset + limit:
            rows.append(row)
        count += 1
    return {'source': meta, 'member': member, 'columns': reader.fieldnames, 'station': station, 'total_matching': count, 'offset': offset, 'notes': NOTES, 'records': rows}
