"""Tests for scripts/free_points.py. Run from the repo root: python3 -m unittest discover -s tests"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import free_points as fp  # noqa: E402

SAMPLE = fp.SAMPLE


def run(*args, home=None):
    buf = io.StringIO()
    old_state = fp.STATE
    if home:
        fp.STATE = os.path.join(home, ".config", "free-points", "courses.json")
    try:
        with redirect_stdout(buf):
            try:
                code = fp.main(list(args))
            except SystemExit as e:
                code = e.code
    finally:
        fp.STATE = old_state
    return code, buf.getvalue()


def write(tmp, data):
    path = os.path.join(tmp, "courses.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


class SampleRun(unittest.TestCase):
    def test_total_and_order(self):
        code, out = run("--sample")
        self.assertEqual(code, 0)
        self.assertIn("About 4.5 points still open across 4 courses", out)
        self.assertIn("plus up to 7.6 more", out)
        first = out.split("Soonest first:")[1].strip().splitlines()[0]
        self.assertIn("Quiz 7 regrade request", first)  # due Tue, the soonest

    def test_grade_bumps(self):
        _, out = run("--sample")
        self.assertIn("PSY 101: 89.2% now; the 2.5 open would reach A- (90%)", out)
        self.assertIn("MAT 265: 78.9% now; 1 open, 0.1 short of B- (80%)", out)

    def test_unclear_goes_to_professor_questions(self):
        _, out = run("--sample")
        listed = out.split("Grade bumps:")[0]
        self.assertNotIn("CHM 113", listed)
        self.assertIn("Ask the professor", out)

    def test_week_only_soon(self):
        code, out = run("--sample", "--week")
        self.assertEqual(code, 0)
        self.assertIn("Expiring in the next 7 days (3)", out)
        self.assertNotIn("research participation", out)

    def test_course_filter(self):
        code, out = run("--sample", "--course", "mat")
        self.assertEqual(code, 0)
        self.assertNotIn("PSY 101", out)
        code, out = run("--sample", "--course", "BIO")
        self.assertEqual(code, 5)

    def test_sample_never_writes_state(self):
        with tempfile.TemporaryDirectory() as home:
            run("--sample", home=home)
            self.assertFalse(os.path.exists(os.path.join(home, ".config")))


class Math(unittest.TestCase):
    def test_points_convert_to_percent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, {"courses": [{"course": "X 101", "course_total_points": 500, "policies": [
                {"type": "extra_credit", "title": "bonus", "worth_points": 10, "deadline": "2026-11-20"}]}]})
            code, out = run("--input", path, "--today", "2026-10-25", "--json")
            self.assertEqual(code, 0)
            self.assertAlmostEqual(json.loads(out)["items"][0]["value"], 2.0)

    def test_regrade_deadline_and_expiry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, {"courses": [{"course": "X 101", "policies": [
                {"type": "regrade_window", "title": "regrades", "window_days": 7,
                 "items": [{"name": "Quiz 1", "released": "2026-10-10"}, {"name": "Quiz 2", "released": "2026-10-22"}]}]}]})
            _, out = run("--input", path, "--today", "2026-10-25", "--json")
            items = {i["title"]: i for i in json.loads(out)["items"]}
            self.assertEqual(items["Quiz 1 regrade request"]["status"], "expired")
            self.assertEqual(items["Quiz 2 regrade request"]["deadline"], "2026-10-29")
            self.assertEqual(items["Quiz 2 regrade request"]["status"], "soon")

    def test_used_up_late_days_are_not_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, {"courses": [{"course": "X 101", "policies": [
                {"type": "late_days", "title": "late days", "total": 2, "used": 2}]}]})
            code, out = run("--input", path, "--today", "2026-10-25")
            self.assertEqual(code, 4)


class Errors(unittest.TestCase):
    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as home:
            code, out = run("--today", "2026-10-25", home=home)
            self.assertEqual(code, 2)
            self.assertIn("No course file yet", out)

    def test_bad_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, {"courses": [{"course": "X 101", "policies": [
                {"type": "extra_credit", "worth_percent": "two"}]}]})
            code, out = run("--input", path, "--today", "2026-10-25")
            self.assertEqual(code, 3)
            self.assertIn("worth_percent should be a number", out)

    def test_unknown_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, {"courses": [{"course": "X 101", "policies": [{"type": "vibes"}]}]})
            code, _ = run("--input", path, "--today", "2026-10-25")
            self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
