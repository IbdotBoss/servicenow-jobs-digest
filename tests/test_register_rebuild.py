"""Tests for the register refresh, the newest-sighting rule in rebuild_master, and recruiter detection.

Run from the repo root: python3 -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import export_site as ex  # noqa: E402
import rebuild_master as rb  # noqa: E402
import scan_sponsorship as scan  # noqa: E402
import sponsor_register as reg  # noqa: E402


class Register(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = reg.REGISTER_DIR
        reg.REGISTER_DIR = self.tmp.name

    def tearDown(self):
        reg.REGISTER_DIR = self.saved
        self.tmp.cleanup()

    def touch(self, name):
        open(os.path.join(self.tmp.name, name), "w").close()

    def test_newest_copy_wins_and_partial_downloads_are_ignored(self):
        for n in ("2026-10-20.csv", "2026-10-27.csv", "2026-10-28.csv.part"):
            self.touch(n)
        self.assertEqual(os.path.basename(reg.current()), "2026-10-27.csv")

    def test_falls_back_to_the_legacy_copy_when_none_downloaded(self):
        self.assertEqual(reg.current(), reg.LEGACY)
        self.assertEqual(reg.date_of(reg.LEGACY), "2026-05-06")

    def test_picks_the_newest_dated_link(self):
        page = ('<a href="https://assets.publishing.service.gov.uk/media/a/Register_-_2026-10-26.csv">'
                '<a href="https://assets.publishing.service.gov.uk/media/b/Register_-_2026-10-27.csv">')
        self.assertEqual(reg.latest_link(page)[0], "2026-10-27")
        self.assertEqual(reg.latest_link("<html>moved</html>"), (None, None))

    def test_rejects_a_file_that_is_not_the_register(self):
        bad = os.path.join(self.tmp.name, "bad.csv")
        with open(bad, "w") as f:
            f.write("<html>Service unavailable</html>\n")
        self.assertFalse(reg.looks_like_register(bad))
        good = os.path.join(self.tmp.name, "good.csv")
        with open(good, "w") as f:
            f.write("Organisation Name,Town/City,County,Type & Rating,Route\n" + "Acme Ltd,London,,Worker (A rating),Skilled Worker\n" * 3)
        saved, reg.MIN_ROWS = reg.MIN_ROWS, 3
        try:
            self.assertTrue(reg.looks_like_register(good))
        finally:
            reg.MIN_ROWS = saved


class NewestSightingWins(unittest.TestCase):
    """A licence the register drops, or a matcher fix, must reach a job the next time it is seen."""

    def test_licence_and_recruiter_follow_the_newest_snapshot(self):
        today = date.today()
        job = {"title": "ServiceNow Developer", "company": "Acme", "url": "https://example.com/1", "source": "JobServe"}
        with tempfile.TemporaryDirectory() as d:
            daily = os.path.join(d, "daily")
            os.makedirs(daily)
            for day, licensed, recruiter in ((today - timedelta(days=1), True, True), (today, False, False)):
                with open(os.path.join(daily, f"jobs_{day}.json"), "w") as f:
                    json.dump({"jobs": [dict(job, sponsor_licence=licensed, recruiter=recruiter)]}, f)
            saved = rb.DAILY_DIR, rb.MASTER_FILE, rb.JOBS_FILE
            rb.DAILY_DIR, rb.MASTER_FILE, rb.JOBS_FILE = daily, os.path.join(d, "master.json"), os.path.join(d, "jobs.json")
            try:
                master = rb.rebuild()
            finally:
                rb.DAILY_DIR, rb.MASTER_FILE, rb.JOBS_FILE = saved
        (row,) = master["jobs"]
        self.assertFalse(row["sponsor_licence"])
        self.assertFalse(row["recruiter"])


class Recruiters(unittest.TestCase):
    def test_names_that_say_so(self):
        self.assertTrue(scan.is_agency("LSA RECRUIT LIMITED"))
        self.assertTrue(scan.is_agency("Atrium Workforce Solutions UK Limited"))
        self.assertTrue(scan.is_agency("Logix Resourcing"))

    def test_names_listed_in_data_recruiters_txt(self):
        self.assertTrue(scan.is_agency("Next Ventures Ltd"))
        self.assertTrue(scan.is_agency("NONSTOP CONSULTING LIMITED"))
        self.assertTrue(scan.is_agency("STOTT & MAY PROFESSIONAL SEARCH LIMITED"))

    def test_employers_are_not_recruiters(self):
        for name in ("Deloitte LLP", "GSK Plc", "Department for Work and Pensions", "ServiceNow", "KPMG UK"):
            self.assertFalse(scan.is_agency(name), name)

    def test_page_label(self):
        job = {"visa_sponsorship": "unknown", "sponsor_licence": False, "recruiter": True}
        self.assertEqual(ex.sponsor_status(job), "recruiter")
        self.assertEqual(ex.sponsor_status(dict(job, visa_sponsorship="sc_blocked")), "clearance")


if __name__ == "__main__":
    unittest.main()
