"""Regression checks for private runtime contamination and share exports."""
import sys
import _bootstrap
sys.dont_write_bytecode=True
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from distribution import verify
from pack_release import pack

class DistributionChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='distribution-test-');self.root=Path(self.temp.name)/'package';self.root.mkdir()
        self.file=self.root/'src/research_mcp.py';self.file.parent.mkdir();self.file.write_text('print("test-only")\n')
        self.manifest()
    def tearDown(self):self.temp.cleanup()
    def manifest(self):
        digest=hashlib.sha256(self.file.read_bytes()).hexdigest()
        (self.root/'MANIFEST.sha256').write_text(digest+'  src/research_mcp.py\n')
    def test_clean_bundle_passes(self):self.assertTrue(verify(self.root)[0]['ok'])
    def test_extra_config_fails_strict(self):
        (self.root/'mcp-config.generated.json').write_text('{"path":"test-only-local-path"}')
        self.assertFalse(verify(self.root)[0]['ok'])
    def test_extra_venv_fails_strict(self):
        p=self.root/'.venv/pyvenv.cfg';p.parent.mkdir();p.write_text('test-only-interpreter')
        self.assertFalse(verify(self.root)[0]['ok'])
    def test_export_never_includes_private_extras(self):
        (self.root/'mcp-config.generated.json').write_text('test-only-private-marker')
        p=self.root/'__pycache__/local.pyc';p.parent.mkdir();p.write_bytes(b'test-only-private-marker')
        out=Path(self.temp.name)/'clean.zip';result=pack(self.root,out)
        self.assertEqual(result['excluded_unlisted_files'],2)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(len(z.namelist()),2)
            self.assertFalse(any(b'test-only-private-marker' in z.read(n) for n in z.namelist()))
            self.assertTrue(all(i.extra==b'' and i.date_time==(2026,1,1,0,0,0) for i in z.infolist()))
    def test_changed_source_rejected(self):
        self.file.write_text('changed')
        with self.assertRaises(ValueError):pack(self.root,Path(self.temp.name)/'bad.zip')
    def test_archive_cannot_be_written_inside_source(self):
        with self.assertRaises(ValueError):pack(self.root,self.root/'bad.zip')
    def test_manifest_cannot_allow_configuration(self):
        p=self.root/'MANIFEST.sha256';p.write_text('0'*64+'  progress.json\n')
        with self.assertRaises(ValueError):verify(self.root)
    def test_deterministic_archive(self):
        a=Path(self.temp.name)/'a.zip';b=Path(self.temp.name)/'b.zip';pack(self.root,a);pack(self.root,b)
        self.assertEqual(a.read_bytes(),b.read_bytes())

if __name__=='__main__':unittest.main()
