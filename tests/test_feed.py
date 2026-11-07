"""Test kanału Atom z raportami swing (build.atom_feed)."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build  # noqa: E402

ATOM = "{http://www.w3.org/2005/Atom}"


class AtomFeedTests(unittest.TestCase):
    ENTRIES = [("2026-11-06", "Swing Raport 6.11.2026", "https://www.gpwradar.pl/reports/2026-11-06.html", "TOP 3: A & B <ok>"),
               ("2026-11-05", "Swing Raport 5.11.2026", "https://www.gpwradar.pl/reports/2026-11-05.html", "TOP 3: C")]

    def test_wellformed_and_escaped(self):
        root = ET.fromstring(build.atom_feed("pl", self.ENTRIES))
        self.assertEqual(root.tag, ATOM + "feed")
        self.assertEqual(root.get("{http://www.w3.org/XML/1998/namespace}lang"), "pl")
        self.assertEqual(root.find(ATOM + "updated").text, "2026-11-06T00:00:00Z")
        self.assertEqual(root.findtext(f"{ATOM}author/{ATOM}name"), build.BRAND)                # RFC 4287: autor kanału wymagany
        entries = root.findall(ATOM + "entry")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].find(ATOM + "summary").text, "TOP 3: A & B <ok>")        # znaki specjalne poprawnie zakodowane
        self.assertEqual(entries[0].find(ATOM + "id").text, entries[0].find(ATOM + "link").get("href"))

    def test_language_specific_self_link(self):
        pl = ET.fromstring(build.atom_feed("pl", self.ENTRIES)).find(f"{ATOM}link[@rel='self']").get("href")
        en = ET.fromstring(build.atom_feed("en", self.ENTRIES)).find(f"{ATOM}link[@rel='self']").get("href")
        self.assertEqual((pl, en), (build.SITE + "/feed.xml", build.SITE + "/en/feed.xml"))


if __name__ == "__main__":
    unittest.main()
