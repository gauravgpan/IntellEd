"""Runs the real Streamlit script with Streamlit's own test harness.

Needs streamlit installed (pip install -r requirements.txt).
"""
import os
import pathlib
import tempfile
import unittest

import streamlit as st
from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).resolve().parent.parent / "streamlit_app.py")


def fresh_app(passcode=None):
    os.environ["TRAITORS_DATA"] = os.path.join(tempfile.mkdtemp(), "game.json")
    if passcode:
        os.environ["HOST_PASSCODE"] = passcode
    else:
        os.environ.pop("HOST_PASSCODE", None)
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


def by_prefix(widgets, prefix):
    hits = [w for w in widgets if w.key and w.key.startswith(prefix)]
    assert hits, f"no widget with key starting {prefix!r}"
    return hits


def button_labelled(at, label):
    return next(b for b in at.button if b.label == label)


def metric(at, label):
    return next(m for m in at.metric if m.label == label).value


class App(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("HOST_PASSCODE", None)

    def test_opens_without_errors(self):
        at = fresh_app()
        self.assertFalse(at.exception)
        self.assertEqual(metric(at, "Players left"), "0 of 0")
        self.assertEqual(metric(at, "Round"), "1 of 5")

    def test_add_players_then_deal(self):
        at = fresh_app()
        at.text_area(key="add_names").input("Ann, Bob, Cy, Di, Ed, Flo, Gus, Hal")
        button_labelled(at, "Add players").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(metric(at, "Players left"), "8 of 8")
        at.button(key="deal").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(metric(at, "Traitors left"), "2 of 2")

    def test_score_and_bank_a_round(self):
        at = fresh_app()
        at.button(key="load_examples").click().run()
        at.button(key="deal").click().run()
        by_prefix(at.number_input, "sc-")[0].set_value(80.0)
        at.run()
        self.assertFalse(at.exception)
        by_prefix(at.button, "bk-")[0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(metric(at, "Pot"), "£40")

    def test_teams_can_be_assigned_and_scored(self):
        at = fresh_app()
        at.button(key="load_examples").click().run()
        at.button(key="deal").click().run()
        before = len(by_prefix(at.number_input, "sc-"))
        by_prefix(at.button, "assign-")[0].click().run()
        self.assertFalse(at.exception)
        self.assertGreater(len(by_prefix(at.number_input, "sc-")), before)

    def test_hide_roles_toggle(self):
        at = fresh_app()
        at.button(key="load_examples").click().run()
        at.button(key="deal").click().run()
        at.toggle(key="hide_roles").set_value(True).run()
        self.assertFalse(at.exception)

    def test_passcode_gate(self):
        at = fresh_app(passcode="letmein")
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric), 0)
        at.text_input[0].input("wrong")
        at.button[0].click().run()
        self.assertEqual(len(at.error), 1)
        at.text_input[0].input("letmein")
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(metric(at, "Players left"), "0 of 0")

    def test_two_sessions_share_one_game(self):
        host = fresh_app()
        cohost = AppTest.from_file(APP, default_timeout=60)
        cohost.run()
        host.text_area(key="add_names").input("Ann, Bob, Cy, Di")
        button_labelled(host, "Add players").click().run()
        cohost.run()
        self.assertFalse(cohost.exception)
        self.assertEqual(metric(cohost, "Players left"), "4 of 4")


if __name__ == "__main__":
    unittest.main()
