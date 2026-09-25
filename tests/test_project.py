#!/usr/bin/env python3
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

class ProjectTests(unittest.TestCase):
    def test_profile_database(self):
        data = json.loads((ROOT / "patchdb" / "profiles.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], 1)
        self.assertIn("m154-broadwell", data["profiles"])
        self.assertFalse(data["profiles"]["m154-broadwell"]["patch_approved"])

    def test_core_imports(self):
        mod = load(ROOT / "chrome_patcher.py", "core_test")
        self.assertTrue(callable(mod.detect_gpu))
        self.assertTrue(callable(mod.status_report))

    def test_phase16_parser(self):
        mod = load(ROOT / "phase16_static_gate.py", "phase16_test")
        sample = '''
segname __TEXT
sectname __text
addr 0x1000
size 0x2000
offset 8192
segname __TEXT
sectname __cstring
addr 0x4000
size 0x100
offset 16384
'''
        sections = mod.parse_section_table(sample)
        self.assertEqual(sections["__text"], (0x1000, 0x2000, 8192))
        self.assertEqual(sections["__cstring"], (0x4000, 0x100, 16384))

    def test_phase16_rip_reference(self):
        mod = load(ROOT / "phase16_static_gate.py", "phase16_rip_test")
        code_vm = 0x1000
        target_vm = 0x3000
        disp = target_vm - (code_vm + 7)
        data = bytes([0x48, 0x8d, 0x3d]) + disp.to_bytes(4, "little", signed=True)
        self.assertEqual(mod.rip_refs(data, code_vm, {target_vm}), [(0, target_vm)])

if __name__ == "__main__":
    unittest.main(verbosity=2)
