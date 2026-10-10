import hashlib
from pathlib import Path
import tempfile
import unittest

import build
from verify import check_loader, loader_records, load_main, verify_hooks


class V2SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = build.load_config()
        cls.patches = build.assemble(cls.config)
        cls.data = build.render_patch(cls.config, cls.patches)

    def test_exact_v2_release(self):
        self.assertEqual(hashlib.sha256(self.data).hexdigest(), self.config["pchtxt_sha256"])
        self.assertEqual(sum(len(p["new"]) for p in self.patches), 132)
        # A v3 interface-camera bypass must never leak into this v2 bundle.
        self.assertEqual({p["address"] for p in self.patches},
                         {0x37e594c, 0x3f06e00, 0x37e5968, 0x3f06e80})

    def test_loader_sees_every_record(self):
        self.assertEqual(check_loader(self.config, self.patches, self.data)["records"], 33)

    def test_blank_line_regression(self):
        broken = self.data.replace(b"@enabled\r\n", b"@enabled\r\n\r\n", 1)
        self.assertEqual(loader_records(broken), [])

    def test_hook_cpu_execution(self):
        self.assertEqual(verify_hooks(self.config, self.patches)["executions"], 128)

    def test_rejects_wrong_or_truncated_game(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main"
            path.write_bytes(b"not an NSO")
            with self.assertRaisesRegex(ValueError, "extracted main NSO"):
                load_main(path, self.config)
            wrong = bytearray(0x100)
            wrong[:4] = b"NSO0"
            path.write_bytes(wrong)
            with self.assertRaisesRegex(ValueError, "Wrong main build ID"):
                load_main(path, self.config)

    def test_zip_packaging_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "mod"
            package.mkdir()
            (package / "patch.pchtxt").write_bytes(self.data)
            build.package_zip(root / "a.zip", package)
            build.package_zip(root / "b.zip", package)
            self.assertEqual((root / "a.zip").read_bytes(), (root / "b.zip").read_bytes())


if __name__ == "__main__":
    unittest.main()
