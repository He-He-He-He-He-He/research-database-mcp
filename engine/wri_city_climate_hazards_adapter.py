"""WRI city-scale climate hazard scenarios (2024 fixed release)."""
import release_runtime
import hashlib, io, os, tempfile, time, zipfile
from pathlib import Path
import requests, openpyxl
URL = 'https://datasets.wri.org/private-admin/dataset/b5018a2b-31e2-4bfd-9a74-53675bf13dd3/resource/72e04330-416b-4b52-bbe8-b2e378ec4191/download/city_scale_climate_hazards_at_1p5_2_3_c_warming.zip'
SOURCE = 'https://datasets.wri.org/datasets/city-scale-climate-hazard-indicators-warming-scenarios'
SHA = '2f58249c64985a4e4edf5adb1ff36766969471ada3edaacaec8cb3da014a5da2'
XLSX = 'city_scale_climate_hazards_at_1p5_2_3_C_warming/cityhazards_1p5_2_3_C_warming.xlsx'
NOTE = 'WRI 2024 city-scale scenario model, 0.25-degree resolution; not observed events, high-confidence forecasts or neighbourhood/project-specific risk. Cities use GHS urban-centre boundaries; national and city figures do not identify the CBD. Three model ranks are separate model estimates, not additive; mean and standard deviation are distinct. 1.5C/2C/3C describe global warming relative to 1880–1900, not city temperature or calendar year. Published website says 1994–2014 historical baseline but workbook says 1995–2014; preserve discrepancy. Hazards are driven by temperature, precipitation, and humidity where relevant and omit other local vulnerability/adaptation factors. Workbook 2020 population is model-derived and may be fractional, not census count. CC BY; credit WRI.'

def _hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def download(path, session=None):
    p = Path(path)
    if os.path.lexists(p):
        raise FileExistsError('destination already exists')
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.wri-city-', dir=str(p.parent))
    os.close(fd)
    try:
        with (session or requests).get(URL, params={'_': int(time.time())}, stream=True, timeout=120) as r:
            r.raise_for_status()
            size = 0
            h = hashlib.sha256()
            with open(tmp, 'wb') as f:
                for chunk in r.iter_content(1024 * 1024):
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > 50000000:
                        raise ValueError('archive too large')
                    h.update(chunk)
                    f.write(chunk)
        if h.hexdigest() != SHA:
            raise ValueError('source snapshot hash changed; revalidation required')
        with zipfile.ZipFile(tmp) as z:
            inf = z.getinfo(XLSX)
            if inf.file_size > 50000000:
                raise ValueError('workbook too large')
        os.link(tmp, p)
        return {'path': str(p.resolve()), 'sha256': SHA, 'bytes': size, 'source': SOURCE, 'note': NOTE}
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def _workbook(path):
    if _hash(path) != SHA:
        raise ValueError('archive does not match verified WRI snapshot')
    with zipfile.ZipFile(path) as z:
        info = z.getinfo(XLSX)
        if info.file_size > 50000000:
            raise ValueError('workbook too large')
        data = z.read(info)
    w = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    if not {'City info', 'Hazard indicators', 'Data overview'}.issubset(w.sheetnames):
        raise ValueError('unexpected workbook structure')
    return w

def cities(path, country, limit=100):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('country required')
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError('invalid limit')
    w = _workbook(path)
    try:
        rows = w['City info'].iter_rows(values_only=True)
        header = next(rows)
        if tuple(header) != ('loc_id', 'city', 'country', 'latitude', 'longitude', 'World_Bank_region', 'World_Bank_country_income_level', 'population_2020'):
            raise ValueError('unexpected city header')
        items = [dict(zip(header, r)) for r in rows if isinstance(r[2], str) and r[2].casefold() == country.strip().casefold()]
        return {'country_source_label': country, 'total': len(items), 'items': items[:limit], 'truncated': len(items) > limit, 'source': SOURCE, 'note': NOTE}
    finally:
        w.close()

def hazards(path, loc_id, hazard=None, scenario=None, indicator=None, limit=100):
    if type(loc_id) is not int or loc_id < 0:
        raise ValueError('loc_id must be nonnegative integer')
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError('invalid limit')
    for v in (hazard, scenario, indicator):
        if v is not None and (not isinstance(v, str) or not v.strip() or len(v) > 80):
            raise ValueError('invalid filter')
    w = _workbook(path)
    try:
        rows = w['Hazard indicators'].iter_rows(values_only=True)
        header = next(rows)
        if tuple(header) != ('loc_id', 'city', 'country', 'latitude', 'longitude', 'hazard', 'scenario', 'model', 'model_rank', 'indicator', 'threshold', 'mean_estimate', 'stdev_estimate'):
            raise ValueError('unexpected hazard header')
        count = 0
        out = []
        for row in rows:
            if row[0] != loc_id or (hazard and row[5] != hazard) or (scenario and row[6] != scenario) or (indicator and row[9] != indicator):
                continue
            count += 1
            if len(out) < limit:
                out.append(dict(zip(header, row)))
        return {'loc_id': loc_id, 'filters': {'hazard': hazard, 'scenario': scenario, 'indicator': indicator}, 'total': count, 'items': out, 'truncated': count > limit, 'source': SOURCE, 'note': NOTE}
    finally:
        w.close()
