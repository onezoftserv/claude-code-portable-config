import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_svg  # noqa: E402
from svgjob import Job  # noqa: E402

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="60mm" viewBox="0 0 100 60">'
CUT = 'fill="none" stroke="#ff0000" stroke-width="0.1"'


class SvgCase(unittest.TestCase):
    def run_check(self, body, head=HEAD, module="laser"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.svg"
            path.write_text(f"{head}{body}</svg>", encoding="utf-8")
            return check_svg.check(path, module)

    def assertError(self, body, text, **kw):
        errors, _, _ = self.run_check(body, **kw)
        self.assertTrue(any(text in e for e in errors), errors)

    def test_valid_job(self):
        errors, warnings, summary = self.run_check(
            f'<rect x="0" y="0" width="100" height="60" {CUT}/>'
            '<line x1="5" y1="5" x2="50" y2="5" fill="none" stroke="blue"/>'
            '<circle cx="50" cy="30" r="10" fill="#00aa00"/>')
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(summary, {"cut": 1, "score": 1, "print": 1})

    def test_units_must_be_mm(self):
        head = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" viewBox="0 0 100 60">'
        self.assertError("<rect width='1' height='1'/>", "must be given in mm", head=head)

    def test_viewbox_must_match(self):
        head = '<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="60mm" viewBox="0 0 377.95 226.77">'
        self.assertError("<rect width='1' height='1'/>", "1 unit = 1 mm", head=head)

    def test_document_larger_than_bed(self):
        head = '<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="300mm" viewBox="0 0 420 300">'
        errors, _, _ = self.run_check(f'<rect width="1" height="1" {CUT}/>', head=head)
        self.assertEqual(errors, [])
        self.assertError(f'<rect width="1" height="1" {CUT}/>', "exceeds the ir bed", head=head, module="ir")

    def test_out_of_bounds(self):
        self.assertError(f'<rect x="90" y="0" width="20" height="10" {CUT}/>', "outside the document")

    def test_arc_bulge_out_of_bounds(self):
        # endpoints are inside, the arc bulges above y=0
        self.assertError(f'<path d="M 10 5 A 20 20 0 0 1 50 5" {CUT}/>', "outside the document")

    def test_relative_path_in_bounds(self):
        errors, _, _ = self.run_check(f'<path d="m 10 10 h 20 v 20 c 0 5 -20 5 -20 0 z" {CUT}/>')
        self.assertEqual(errors, [])

    def test_cut_with_fill(self):
        self.assertError('<rect width="10" height="10" stroke="#f00"/>', 'must have fill="none"')

    def test_inherited_paint(self):
        errors, _, summary = self.run_check(
            f'<g {CUT}><rect width="10" height="10"/><g><circle cx="20" cy="20" r="5"/></g></g>')
        self.assertEqual(errors, [])
        self.assertEqual(summary["cut"], 2)

    def test_style_attribute(self):
        _, _, summary = self.run_check('<rect width="10" height="10" style="fill:none;stroke:rgb(0,0,255)"/>')
        self.assertEqual(summary["score"], 1)

    def test_duplicates(self):
        self.assertError(f'<line x1="0" y1="0" x2="9" y2="9" {CUT}/><line x1="9" y1="9" x2="0" y2="0" {CUT}/>',
                         "duplicate")

    def test_same_geometry_different_role_is_fine(self):
        errors, _, _ = self.run_check(
            f'<line x1="0" y1="0" x2="9" y2="9" {CUT}/>'
            '<line x1="0" y1="0" x2="9" y2="9" fill="none" stroke="#0000ff"/>')
        self.assertEqual(errors, [])

    def test_banned_elements(self):
        self.assertError('<text x="1" y="9">hi</text>', "convert text to paths")
        self.assertError(f'<g transform="translate(5 5)"><rect width="1" height="1" {CUT}/></g>', "transform")
        self.assertError("<style>rect{fill:red}</style>", "not allowed")

    def test_units_inside_shapes_rejected(self):
        self.assertError(f'<rect x="1mm" width="10" height="10" {CUT}/>', "plain number")

    def test_print_area_warning(self):
        head = '<svg xmlns="http://www.w3.org/2000/svg" width="400mm" height="300mm" viewBox="0 0 400 300">'
        errors, warnings, _ = self.run_check('<rect width="350" height="100" fill="#123456"/>', head=head)
        self.assertEqual(errors, [])
        self.assertTrue(any("inkjet area" in w for w in warnings), warnings)

    def test_import_test_file_fails_on_purpose(self):
        errors, _, _ = check_svg.check(ROOT / "laser" / "_import-test" / "test.svg")
        joined = "\n".join(errors)
        for expected in ("transform", "convert text", "duplicate"):
            self.assertIn(expected, joined)


class JobCase(unittest.TestCase):
    def check_job(self, job):
        with tempfile.TemporaryDirectory() as tmp:
            return check_svg.check(job.save(Path(tmp) / "job.svg"))

    def test_writer_output_validates(self):
        job = Job(120, 80)
        job.cut_rect(0, 0, 120, 80, r=5)
        job.cut_circle(20, 20, 4)
        job.score_line(10, 40, 110, 40)
        job.score_path("M 10 50 Q 60 30 110 50")
        job.print_circle(60, 60, 8, fill="#cc3300")
        errors, warnings, summary = self.check_job(job)
        self.assertEqual((errors, warnings), ([], []))
        self.assertEqual(summary, {"cut": 2, "score": 2, "print": 1})

    def test_layer_order_is_print_score_cut(self):
        job = Job(10, 10)
        job.cut_rect(0, 0, 10, 10)
        job.print_rect(1, 1, 2, 2)
        job.score_line(0, 5, 10, 5)
        svg = job.to_svg()
        self.assertLess(svg.index('id="print"'), svg.index('id="score"'))
        self.assertLess(svg.index('id="score"'), svg.index('id="cut"'))

    def test_examples_validate(self):
        for name in ("name-tag", "_template"):
            spec = importlib.util.spec_from_file_location(f"job_{name}", ROOT / "laser" / name / "job.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            errors, _, _ = self.check_job(module.job)
            self.assertEqual(errors, [], name)


@unittest.skipUnless(importlib.util.find_spec("trimesh"), "trimesh not installed")
class MeshCase(unittest.TestCase):
    def export(self, mesh, tmp):
        path = Path(tmp) / "m.stl"
        mesh.export(path)
        return path

    def test_box_ok_and_limits(self):
        import check_mesh
        import trimesh

        with tempfile.TemporaryDirectory() as tmp:
            errors, info = check_mesh.check(self.export(trimesh.creation.box([20, 30, 10]), tmp))
            self.assertEqual(errors, [])
            self.assertEqual(info["size_mm"], [20.0, 30.0, 10.0])
            # fits single nozzle, too wide for dual in either rotation
            wide = self.export(trimesh.creation.box([250, 250, 10]), tmp)
            self.assertEqual(check_mesh.check(wide)[0], [])
            self.assertTrue(any("dual-nozzle" in e for e in check_mesh.check(wide, dual=True)[0]))
            # rotating on the plate is allowed
            long = self.export(trimesh.creation.box([250, 230, 10]), tmp)
            self.assertEqual(check_mesh.check(long, dual=True)[0], [])

    def test_open_mesh_fails(self):
        import check_mesh
        import trimesh

        box = trimesh.creation.box([10, 10, 10])
        box.update_faces([i != 0 for i in range(len(box.faces))])
        with tempfile.TemporaryDirectory() as tmp:
            errors, _ = check_mesh.check(self.export(box, tmp))
            self.assertTrue(any("watertight" in e for e in errors), errors)


class SnapshotCase(unittest.TestCase):
    def setUp(self):
        import shutil

        self.project = Path(tempfile.mkdtemp(dir=ROOT / "laser", prefix="_t-"))
        self.addCleanup(shutil.rmtree, self.project, True)
        shutil.copy(ROOT / "laser" / "_template" / "job.py", self.project / "job.py")

    def snap(self, *extra):
        import contextlib
        import io

        import snapshot

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = snapshot.main([str(self.project), "-m", "test", "--no-commit", *extra])
        return code, out.getvalue()

    def names(self):
        import snapshot

        return [v.name for v in snapshot.versions(self.project)]

    def test_versions_are_numbered_and_frozen(self):
        self.assertEqual(self.snap()[0], 0)
        v1 = self.project / "versions" / "v001"
        self.assertEqual(sorted(p.name for p in v1.iterdir()), ["VERSION.md", "job.py", "job.svg"])
        self.assertEqual(check_svg.check(v1 / "job.svg")[0], [])

        code, out = self.snap()  # unchanged: no new version
        self.assertEqual((code, self.names()), (0, ["v001"]))
        self.assertIn("no changes since v001", out)

        job = self.project / "job.py"
        job.write_text(job.read_text().replace("WIDTH = 80", "WIDTH = 70"))
        before = (v1 / "job.svg").read_bytes()
        self.assertEqual(self.snap()[0], 0)
        self.assertEqual(self.names(), ["v001", "v002"])
        self.assertEqual((v1 / "job.svg").read_bytes(), before)
        self.assertIn('width="70mm"', (self.project / "versions" / "v002" / "job.svg").read_text())

        self.assertEqual(self.snap("--force")[0], 0)
        self.assertEqual(self.names(), ["v001", "v002", "v003"])

    def test_failed_check_saves_nothing(self):
        job = self.project / "job.py"
        job.write_text(job.read_text().replace("job.cut_rect(0, 0, WIDTH, HEIGHT, r=CORNER)",
                                               "job.cut_rect(5, 0, WIDTH, HEIGHT, r=CORNER)"))
        code, out = self.snap()
        self.assertEqual(code, 1)
        self.assertIn("NOT SAVED", out)
        self.assertEqual(self.names(), [])


if __name__ == "__main__":
    unittest.main()
