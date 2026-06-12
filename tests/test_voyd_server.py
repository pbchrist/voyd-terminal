"""The shared body: one portal, one sediment. Hermetic — no LLM, no network
beyond a loopback server on an ephemeral port; state in a temp dir."""
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

import voyd_server


class VoydServerTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self._orig_state = voyd_server.STATE_PATH
        voyd_server.STATE_PATH = Path(self._tmp.name) / "voyd_state.json"
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), voyd_server.VoydHandler)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        voyd_server.STATE_PATH = self._orig_state
        self._tmp.cleanup()

    def _get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as r:
            return json.load(r)

    def _post(self, path, payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    def test_state_starts_small(self):
        d = self._get("/state")
        self.assertEqual(d["visits"], 0)
        self.assertEqual(d["fragments"], [])
        self.assertIsNone(d["kept"])
        self.assertAlmostEqual(d["portal"], 8.0)

    def test_portal_is_global_and_grows_with_feeding(self):
        p0 = self._get("/state")["portal"]
        for _ in range(5):
            self._post("/offer", {"token": "a", "kind": "feed"})
        p1 = self._get("/state")["portal"]
        self.assertGreater(p1, p0)
        # a different visitor sees the same portal — there is one Voyd
        self.assertEqual(self._get("/state?token=zzz")["portal"], p1)

    def test_starving_shrinks_it(self):
        for _ in range(6):
            self._post("/offer", {"token": "a", "kind": "feed"})
        fed = self._get("/state")["portal"]
        for _ in range(6):
            self._post("/offer", {"token": "a", "kind": "starve"})
        self.assertLess(self._get("/state")["portal"], fed)

    def test_portal_clamped(self):
        st = voyd_server._blank_state()
        st["fed"] = 1e9
        self.assertLessEqual(voyd_server.portal_value(st), 96.0)
        st["fed"], st["starved"] = 0.0, 1e9
        self.assertGreaterEqual(voyd_server.portal_value(st), 5.0)

    def test_gifts_queue_for_digestion_not_served_raw(self):
        self._post("/offer", {"token": "a", "kind": "name",
                              "text": "my father, before the winter"})
        # raw gift must never surface as a fragment until digested
        self.assertEqual(self._get("/state")["fragments"], [])
        state = voyd_server.load_state()
        self.assertIn("my father, before the winter", state["pending"])

    def test_sediment_served_once_digested(self):
        state = voyd_server.load_state()
        state["sediment"].append(
            {"text": "someone gave me a father once. he smelled of rain.",
             "at": "2026-06-12T00:00:00"})
        voyd_server.save_state(state)
        frags = self._get("/state")["fragments"]
        self.assertEqual(len(frags), 1)
        self.assertTrue(frags[0].startswith("someone gave me"))

    def test_it_keeps_what_you_gave_it(self):
        self._post("/keep", {"token": "walker1", "text": "the way you said it first"})
        self.assertEqual(self._get("/state?token=walker1")["kept"],
                         "the way you said it first")
        self.assertIsNone(self._get("/state?token=stranger")["kept"])

    def test_visit_counted(self):
        self._post("/offer", {"token": "a", "kind": "visit"})
        self._post("/offer", {"token": "b", "kind": "visit"})
        self.assertEqual(self._get("/state")["visits"], 2)

    def test_sanitize_strips_urls_emails_and_control(self):
        s = voyd_server.sanitize("see http://x.com and me@x.com \x07now")
        self.assertNotIn("http", s)
        self.assertNotIn("@", s)
        self.assertNotIn("\x07", s)
        self.assertEqual(len(voyd_server.sanitize("a" * 999)),
                         voyd_server.MAX_TEXT)

    def test_unknown_paths_and_kinds_rejected(self):
        with self.assertRaises(urllib.error.HTTPError):
            self._get("/secrets")
        with self.assertRaises(urllib.error.HTTPError):
            self._post("/offer", {"token": "a", "kind": "rm -rf"})

    def test_voyd_prefix_tolerated(self):
        # direct-IP access bypasses the funnel's prefix strip
        d = self._get("/voyd/state")
        self.assertIn("portal", d)


if __name__ == "__main__":
    unittest.main()
