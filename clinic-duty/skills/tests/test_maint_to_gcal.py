import json
import os
import sys
import unittest
from datetime import datetime, timezone
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "dc-maintenance-notices", "scripts"))
import maint_to_gcal as m  # noqa: E402

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
CAL = "test-calendar-id"


def notice(windows, **kw):
    n = {"vendor": "TestVendor", "ticket_id": "T-1", "notice_type": "new",
         "summary": "work", "sites": ["S1"], "impact": "no-impact", "windows": windows}
    n.update(kw)
    return n


def win(start, end, tz="UTC", **kw):
    w = {"start": start, "end": end, "tz": tz, "evidence": "line"}
    w.update(kw)
    return w


class TimeConversion(unittest.TestCase):
    def row(self, w):
        return m.process(notice([w]), CAL, NOW)["windows"][0]

    def test_utc(self):
        r = self.row(win("2026-10-20T04:00", "2026-10-20T07:00"))
        self.assertEqual((r["start"], r["end"]), ("2026-10-20 04:00", "2026-10-20 07:00"))
        self.assertIn("dates=20261020T040000Z/20261020T070000Z", r["link"])

    def test_dst_changeover_night_paris(self):
        r = self.row(win("2026-10-25T01:00", "2026-10-25T05:00", "Europe/Paris"))
        self.assertEqual((r["start"], r["end"]), ("2026-10-24 23:00", "2026-10-25 04:00"))

    def test_gmt_plus_8(self):
        r = self.row(win("2026-10-26T01:00", "2026-10-26T05:00", "GMT+8"))
        self.assertEqual(r["start"], "2026-10-25 17:00")

    def test_missing_tz_is_not_guessed(self):
        r = self.row(win("2026-10-21T22:00", "2026-10-22T04:00", None))
        self.assertIsNone(r["link"])
        self.assertTrue(any("timezone" in f for f in r["flags"]))

    def test_ambiguous_abbreviation_is_not_guessed(self):
        r = self.row(win("2026-10-27T01:00", "2026-10-27T05:00", "CEST"))
        self.assertIsNone(r["link"])

    def test_end_before_start(self):
        r = self.row(win("2026-10-29T10:00", "2026-10-29T09:00"))
        self.assertIsNone(r["link"])
        self.assertIn("end is before start", r["flags"])

    def test_long_and_past_flags(self):
        self.assertIn("window longer than 24h",
                      self.row(win("2026-10-30T00:00", "2026-11-02T00:00"))["flags"])
        self.assertIn("window is in the past",
                      self.row(win("2026-10-01T00:00", "2026-10-01T02:00"))["flags"])

    def test_all_day(self):
        r = self.row(win("2026-10-28", "2026-10-28", all_day=True))
        self.assertIn("dates=20261028/20261029", r["link"])


class Links(unittest.TestCase):
    def test_marked_available_not_busy(self):
        r = m.process(notice([win("2026-10-20T04:00", "2026-10-20T07:00")]), CAL, NOW)
        self.assertIn("crm=AVAILABLE", r["windows"][0]["link"])
        self.assertNotIn("trp=", r["windows"][0]["link"])  # ignored by current Google Calendar

    def test_backup_window_title(self):
        r = m.process(notice([win("2026-10-22T04:00", "2026-10-22T07:00",
                                  label="Step 3 backup", conditional=True)]), CAL, NOW)
        self.assertIn("BACKUP", r["windows"][0]["link"])

    def test_url_length_limit(self):
        r = m.process(notice([win("2026-12-01T00:00", "2026-12-01T02:00", evidence="é" * 20000)]), CAL, NOW)
        link = r["windows"][0]["link"]
        u = urlparse(link)
        self.assertLessEqual(len(u.path) + 1 + len(u.query), m.MAX_PATH_QUERY_LEN)
        self.assertTrue(any("truncated" in f for f in r["windows"][0]["flags"]))


class NoticeTypesAndReport(unittest.TestCase):
    def test_cancel_creates_no_link(self):
        r = m.process(notice([win("2026-10-20T04:00", "2026-10-20T07:00")], notice_type="cancel"), CAL, NOW)
        self.assertEqual(r["windows"], [])
        self.assertTrue(any("CANCELLED" in f for f in r["flags"]))

    def test_duplicate_ticket_flagged(self):
        a = m.process(notice([win("2026-10-20T04:00", "2026-10-20T07:00")]), CAL, NOW)
        b = m.process(notice([win("2026-10-20T05:00", "2026-10-20T08:00")]), CAL, NOW)
        self.assertIn("appears 2x", m.render([a, b], NOW))

    def test_ics(self):
        a = m.process(notice([win("2026-10-20T04:00", "2026-10-20T07:00"),
                              win("2026-10-22T04:00", "2026-10-22T07:00", conditional=True)]), CAL, NOW)
        ics = m.render_ics([a], NOW)
        self.assertEqual(ics.count("BEGIN:VEVENT"), 2)
        self.assertEqual(ics.count("TRANSP:TRANSPARENT"), 2)
        self.assertEqual(ics.count("STATUS:TENTATIVE"), 1)
        self.assertEqual(ics.count("\n"), ics.count("\r\n"))
        self.assertTrue(all(len(line) <= 75 for line in ics.split("\r\n")))


class RealNoticeFixture(unittest.TestCase):
    def test_decix_one_ticket_per_window(self):
        with open(os.path.join(HERE, "fixtures", "decix_3755_3758.json")) as f:
            notices = json.load(f)["notices"]
        res = [m.process(n, CAL, NOW) for n in notices]
        self.assertEqual([r["ticket"] for r in res],
                         ["DXDB:MAINT:3755", "DXDB:MAINT:3756", "DXDB:MAINT:3757", "DXDB:MAINT:3758"])
        self.assertTrue(all(len(r["windows"]) == 1 and r["windows"][0]["link"] for r in res))
        self.assertEqual([r["windows"][0]["start"] for r in res],
                         ["2026-10-20 04:00", "2026-10-22 04:00", "2026-10-27 05:00", "2026-10-29 05:00"])

    def test_arelion_one_ticket_many_windows(self):
        """Opposite of DE-CIX: all service windows hang off one PWIC reference."""
        with open(os.path.join(HERE, "fixtures", "arelion_multi_window_update.json")) as f:
            notices = json.load(f)["notices"]
        res = [m.process(n, CAL, NOW) for n in notices]
        self.assertEqual(len(res), 1)
        r = res[0]
        self.assertEqual(r["ticket"], "PWIC000000")
        self.assertEqual([w["start"] for w in r["windows"]],
                         ["2026-10-11 04:01", "2026-10-17 04:01", "2026-10-18 04:01"])
        # The already-implemented window is kept but surfaced as past, and its
        # link title says so; the two Confirmed ones are clean.
        self.assertEqual(r["windows"][0]["flags"], ["window is in the past"])
        self.assertIn("COMPLETED", r["windows"][0]["link"])
        self.assertTrue(all(w["link"] and not w["flags"] for w in r["windows"][1:]))


if __name__ == "__main__":
    unittest.main()
