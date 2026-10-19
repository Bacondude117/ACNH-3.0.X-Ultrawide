import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import build
from verify import check_loader, loader_records, load_main, verify_hooks
from verify_resources import verify_resource_hooks, run_resource


class V4SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = build.load_config()
        cls.patches = build.assemble(cls.config)
        cls.data = build.render_patch(cls.config, cls.patches)

    def test_exact_release_and_original_camera_sites(self):
        self.assertEqual(hashlib.sha256(self.data).hexdigest(), self.config['pchtxt_sha256'])
        camera = [hook for hook in self.config['hooks']
                  if hook['source'] in ('aspect_getter.s', 'perspective_matrix.s')]
        self.assertEqual([(hook['site'], hook['original']) for hook in camera],
                         [('037E594C', '00B040BD'), ('037E5968', '009840BD')])
        self.assertNotIn(0x376d220, {p['address'] for p in self.patches})

    def test_loader_and_blank_line_regression(self):
        report = check_loader(self.config, self.patches, self.data)
        self.assertEqual(report['payload_bytes'], sum(len(p['new']) for p in self.patches))
        broken = self.data.replace(b'@enabled\r\n', b'@enabled\r\n\r\n', 1)
        self.assertEqual(loader_records(broken), [])

    def test_camera_cpu_execution(self):
        self.assertEqual(verify_hooks(self.config, self.patches)['executions'], 128)

    def test_resource_cpu_execution(self):
        self.assertEqual(verify_resource_hooks(self.config, self.patches)['resources'], 102)

    def test_create_range_cpu_execution(self):
        from verify_create_range import verify_create_range_hook
        self.assertEqual(verify_create_range_hook(self.config, self.patches)['executions'], 24)

    def test_create_range_and_terrain_cell_sphere_hooks(self):
        sites = {hook['site'] for hook in self.config['hooks']}
        self.assertIn('013A29A4', sites)
        self.assertIn('013A37B4', sites)  # 3D half-diagonal terrain-cell bound (rev3)
        self.assertNotIn('01573C3C', sites)  # earlier category-bounds attempt
        hook = next(h for h in self.config['hooks'] if h['source'] == 'create_range.s')
        cave = next(p for p in self.patches if p['address'] == int(hook['cave'], 16))
        self.assertEqual(len(cave['new']), 32)
        self.assertEqual(cave['new'][:4], bytes.fromhex('00102F1E'))  # fmov s0, #1.5

    def test_area_range_cpu_execution(self):
        from verify_area_range import verify_area_range_hooks
        self.assertEqual(verify_area_range_hooks(self.config, self.patches)['executions'], 72)

    def test_terrain_cell_sphere_cpu_execution(self):
        from verify_culling import verify_culling_hook
        self.assertEqual(verify_culling_hook(self.config, self.patches)['executions'], 24)

    def test_unit_max_cpu_execution(self):
        from verify_unit_max import verify_unit_max_hook
        self.assertEqual(verify_unit_max_hook(self.config, self.patches)['executions'], 24)

    def test_area_range_sites_share_one_routine(self):
        hooks = [h for h in self.config['hooks'] if h['source'] == 'area_range.s']
        self.assertEqual(sorted(h['site'] for h in hooks), ['01125FE4', '01126144'])
        self.assertEqual({h['cave'] for h in hooks}, {'03F06E30'})
        self.assertTrue(all(h.get('link') for h in hooks))
        sites = {p['address']: p['new'] for p in self.patches}
        for h in hooks:
            word = int.from_bytes(sites[int(h['site'], 16)], 'little')
            self.assertEqual(word >> 26, 0b100101)  # BL

    def test_compact_camera_hooks_fit_padding(self):
        caves = sorted({(int(h['cave'], 16), h['source']) for h in self.config['hooks']})
        spans = {p['address']: len(p['new']) for p in self.patches}
        end = int(self.config['code_padding_end'], 16)
        for (a, _), (b, _) in zip(caves, caves[1:]):
            self.assertLessEqual(a + spans[a], b)
        self.assertLessEqual(max(a + spans[a] for a, _ in caves), end)

    def test_dal_and_minimap_corrections(self):
        from verify_ui import check_ui_deltas
        self.assertEqual(check_ui_deltas()['dal_mask_geometry'], 'passed')

    def test_phone_capture_and_backgrounds(self):
        from verify_ui import check_phone_menu_deltas
        self.assertEqual(check_phone_menu_deltas()['phone_capture_alignment'], 'passed')

    def test_projection_aware_clipping_cpu(self):
        from verify_ui import verify_scissor_hook
        self.assertEqual(verify_scissor_hook(self.config,self.patches)['executions'],64)

    def test_projection_aware_capture_cpu(self):
        from verify_capture import verify_capture_hook
        self.assertEqual(verify_capture_hook(self.config,self.patches)['executions'],128)

    def test_screenshot_coverage_and_capture_materials(self):
        from verify_sweep import check_sweep
        self.assertEqual(check_sweep()['capture_material_projectors'],8)

    def test_unknown_resource_and_empty_table(self):
        data = bytearray(32); data[12:16] = (32).to_bytes(4, 'little')
        for hook in (2, 3):
            self.assertEqual(run_resource(self.config, self.patches, data, hook), data)
            self.assertEqual(run_resource(self.config, self.patches, data, hook, table=bytes(16)), data)

    def test_rejects_bad_delta_and_conflicting_alias(self):
        items = json.loads((build.ROOT / 'layout_deltas.json').read_text())
        bad = copy.deepcopy(items[0]); bad['changes'][0]['offset'] = bad['size']
        with self.assertRaisesRegex(ValueError, 'bounds'):
            build.resource_table([bad])
        bad = copy.deepcopy(items[0]); bad['changes'][0]['after'] = '0000803F'
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            build.resource_table([items[0], bad])

    def test_rejects_wrong_or_truncated_game(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'main'; path.write_bytes(b'not an NSO')
            with self.assertRaisesRegex(ValueError, 'extracted main NSO'):
                load_main(path, self.config)
            wrong = bytearray(0x100); wrong[:4] = b'NSO0'; path.write_bytes(wrong)
            with self.assertRaisesRegex(ValueError, 'Wrong main build ID'):
                load_main(path, self.config)

    def test_zip_packaging_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); package = root / 'mod'; package.mkdir()
            (package / 'patch.pchtxt').write_bytes(self.data)
            build.package_zip(root / 'a.zip', package)
            build.package_zip(root / 'b.zip', package)
            self.assertEqual((root / 'a.zip').read_bytes(), (root / 'b.zip').read_bytes())


if __name__ == '__main__':
    unittest.main()
