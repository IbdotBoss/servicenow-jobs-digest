"""Tests for the export step and the sponsorship scanner.

Run from the repo root: python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import export_site as ex  # noqa: E402
import scan_sponsorship as scan  # noqa: E402


class CleanTitle(unittest.TestCase):
    def test_brand_casing(self):
        self.assertEqual(ex.clean_title("Servicenow Enterprise Architect"), "ServiceNow Enterprise Architect")
        self.assertEqual(ex.clean_title("SERVICENOW Developer"), "ServiceNow Developer")
        self.assertEqual(ex.clean_title("Service Now Admin"), "ServiceNow Admin")

    def test_separators(self):
        self.assertEqual(ex.clean_title("Project Manager |ServiceNow | Contract |Outside IR35"),
                         "Project Manager | ServiceNow | Contract | Outside IR35")
        self.assertEqual(ex.clean_title("  ServiceNow   Architect - "), "ServiceNow Architect")

    def test_shouting_words_but_not_acronyms(self):
        self.assertEqual(ex.clean_title("Transition Lead - OUTSIDE IR35"), "Transition Lead - Outside IR35")
        self.assertEqual(ex.clean_title("ServiceNow ITSM CMDB Developer"), "ServiceNow ITSM CMDB Developer")
        self.assertEqual(ex.clean_title("ServiceNow HRSD Consultant"), "ServiceNow HRSD Consultant")

    def test_lowercase_title_gets_a_capital(self):
        self.assertEqual(ex.clean_title("servicenow architect"), "ServiceNow architect")

    def test_leaves_ordinary_titles_alone(self):
        t = "Senior ServiceNow Technical Consultant (on-site Erskine)"
        self.assertEqual(ex.clean_title(t), t)


class CleanCompany(unittest.TestCase):
    def test_all_caps_company(self):
        self.assertEqual(ex.clean_company("SOFTNICE UK LIMITED"), "Softnice UK Limited")
        self.assertEqual(ex.clean_company("EXCEED SOLUTIONS LTD"), "Exceed Solutions Ltd")

    def test_short_acronyms_survive(self):
        self.assertEqual(ex.clean_company("EPAM SYSTEMS"), "EPAM Systems")

    def test_placeholder_is_empty(self):
        self.assertEqual(ex.clean_company("[view listing]"), "")
        self.assertEqual(ex.clean_company("N/A"), "")
        self.assertEqual(ex.clean_company("Unknown"), "")

    def test_mixed_case_untouched(self):
        self.assertEqual(ex.clean_company("Ubique Systems UK Limited"), "Ubique Systems UK Limited")
        self.assertEqual(ex.clean_company("KPMG UK"), "KPMG UK")


class Slim(unittest.TestCase):
    BASE = {"title": "ServiceNow Developer", "company": "Acme", "location": "London", "url": "https://x",
            "source": "hunt_uk", "role_type": "developer", "visa_sponsorship": "unknown",
            "sponsor_licence": False, "first_seen": "2026-10-27", "last_seen": "2026-10-27",
            "status": "active", "remote": "onsite"}

    def job(self, **kw):
        return {**self.BASE, **kw}

    def test_source_names_are_normalised(self):
        self.assertEqual(ex.slim(self.job())["src"], "Hunt UK")

    def test_onsite_is_not_stated(self):
        # The scrapers default to "onsite" when they can't tell, so it is not shown as a fact.
        self.assertIsNone(ex.slim(self.job())["r"])
        self.assertEqual(ex.slim(self.job(remote="hybrid"))["r"], "hybrid")

    def test_sponsor_status(self):
        self.assertEqual(ex.slim(self.job(sponsor_licence=True))["sp"], "licensed")
        self.assertEqual(ex.slim(self.job(visa_sponsorship="sc_blocked", sponsor_licence=True))["sp"], "clearance")
        self.assertEqual(ex.slim(self.job(visa_sponsorship="unavailable"))["sp"], "no")
        self.assertEqual(ex.slim(self.job(visa_sponsorship="agency_unknown"))["sp"], "agency")
        self.assertEqual(ex.slim(self.job())["sp"], "unknown")

    def test_mention_flag_never_contradicts_a_refusal(self):
        self.assertFalse(ex.slim(self.job(visa_sponsorship="unavailable", sponsorship_mentioned=True))["m"])
        self.assertFalse(ex.slim(self.job(visa_sponsorship="sc_blocked", sponsorship_mentioned=True))["m"])
        self.assertTrue(ex.slim(self.job(sponsor_licence=True, sponsorship_mentioned=True))["m"])

    def test_not_listed_salary_is_blank(self):
        self.assertEqual(ex.slim(self.job(salary_display="Not listed"))["s"], "")


class Split(unittest.TestCase):
    def test_active_and_monthly_archive(self):
        jobs = [
            {"title": "A", "status": "active", "last_seen": "2026-10-27"},
            {"title": "B", "status": "stale", "last_seen": "2026-10-05"},
            {"title": "C", "status": "expired", "last_seen": "2026-09-30"},
        ]
        active, archive = ex.split(jobs)
        self.assertEqual([j["title"] for j in active], ["A"])
        self.assertEqual(sorted(archive), ["2026-09", "2026-10"])
        self.assertEqual([j["title"] for j in archive["2026-10"]], ["B"])


class ScannerMention(unittest.TestCase):
    def test_refusal_is_not_a_mention(self):
        self.assertFalse(scan.mentions_sponsorship("We cannot offer Skilled Worker visa sponsorship for this role."))
        self.assertFalse(scan.mentions_sponsorship("No sponsorship is available."))

    def test_clearance_page_is_not_a_mention(self):
        self.assertFalse(scan.mentions_sponsorship("SC cleared candidates only. Sponsorship available."))

    def test_refusal_with_words_between_is_tagged(self):
        self.assertEqual(scan.scan_text("We cannot offer Skilled Worker visa sponsorship.")[0], "unavailable")
        self.assertEqual(scan.scan_text("The client is unable to provide sponsorship.")[0], "unavailable")
        self.assertIsNone(scan.scan_text("We offer visa sponsorship for this role.")[0])

    def test_real_mention(self):
        self.assertTrue(scan.mentions_sponsorship("Visa sponsorship is available for the right candidate."))
        self.assertTrue(scan.mentions_sponsorship("We can sponsor a Skilled Worker visa."))


class SponsorMatch(unittest.TestCase):
    """Cases taken from the live data on 2026-10-27, when matching was by substring."""
    REGISTER = ["Gadgetxperts Limited", "Light Methods Limited", "Custom & Contract Power Solutions (CCPS) Ltd",
                "Dhammakaya International Society of the United Kingdom", "IBM UK Ltd", "Allen Lane Limited",
                "Deloitte LLP", "Stott and May Professional Search Limited", "Ernst & Young LLP"]

    def setUp(self):
        self.register = {scan.normalize_company(n) for n in self.REGISTER}

    def licensed(self, company):
        return scan.company_has_licence(company, self.register)[0]

    def test_substrings_no_longer_match(self):
        self.assertFalse(self.licensed("TXP"))           # was matched inside "gadgeTXPerts"
        self.assertFalse(self.licensed("Methods"))       # was matched inside "light methods"
        self.assertFalse(self.licensed("CPS Group (UK) Limited"))
        self.assertFalse(self.licensed("Honeywell"))     # the "ey inside honey" class of match

    def test_placeholders_never_match(self):
        self.assertFalse(self.licensed("United Kingdom"))
        self.assertFalse(self.licensed("N/A"))

    def test_same_employer_written_differently(self):
        self.assertTrue(self.licensed("IBM UNITED KINGDOM LIMITED"))
        self.assertTrue(self.licensed("Allen Lane Ltd."))
        self.assertTrue(self.licensed("Deloitte"))
        self.assertTrue(self.licensed("Ernst and Young"))

    def test_resourcing_firms_are_agencies(self):
        self.assertFalse(self.licensed("Alexander Mann Solutions - Public Sector Resourcing"))


if __name__ == "__main__":
    unittest.main()
