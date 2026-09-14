from pathlib import Path
import runpy
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
check = runpy.run_path(str(ROOT/'tools/check_ui.py'))['check']


class UiBuildTests(unittest.TestCase):
    def test_changed_source_missing_output_and_tampered_bundle_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'web',root/'web',ignore=shutil.ignore_patterns('node_modules'))
            (root/'src/kajamite').mkdir(parents=True)
            for name in ['ui-build.json','knowledge-change.html','UI-NOTICES.txt']:
                shutil.copyfile(ROOT/'src/kajamite'/name,root/'src/kajamite'/name)
            check(root)
            source=root/'web/src/app.tsx';original=source.read_bytes()
            source.write_bytes(original+b'\n// changed\n')
            with self.assertRaisesRegex(ValueError,'Stale UI'):check(root)
            source.write_bytes(original)
            bundle=root/'src/kajamite/knowledge-change.html';original=bundle.read_bytes()
            bundle.write_bytes(original+b'\nchanged')
            with self.assertRaisesRegex(ValueError,'Stale UI'):check(root)
            bundle.write_bytes(original)
            extra=root/'web/src/new.ts';extra.write_text('export const example = 1;')
            with self.assertRaisesRegex(ValueError,'source list'):check(root)
            extra.unlink()
            (root/'src/kajamite/UI-NOTICES.txt').unlink()
            with self.assertRaises(FileNotFoundError):check(root)
