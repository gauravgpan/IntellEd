import json
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import traitors_core as core  # noqa: E402


def game_with_players(n=20, seed=1, traitors=4):
    s = core.new_state()
    core.add_players(s, "\n".join(core.EXAMPLE_NAMES[:n]) if n <= 20 else "\n".join(f"P{i}" for i in range(n)))
    core.deal_roles(s, traitors, random.Random(seed))
    return s


def roles(s):
    return [p["role"] for p in s["players"]]


class Dealing(unittest.TestCase):
    def test_suggested_traitors(self):
        self.assertEqual([core.suggest_traitors(n) for n in (2, 3, 7, 8, 12, 20, 25)], [1, 1, 1, 2, 2, 4, 5])

    def test_deal_counts_and_clears_results(self):
        s = game_with_players()
        self.assertEqual(roles(s).count("traitor"), 4)
        self.assertEqual(roles(s).count("faithful"), 16)
        r = s["rounds"][0]
        core.set_murder(s, r["id"], next(p["id"] for p in s["players"] if p["role"] == "faithful"))
        core.deal_roles(s, 4)
        self.assertIsNone(r["murdered"])

    def test_deal_needs_three_players(self):
        s = core.new_state()
        core.add_players(s, "A, B")
        with self.assertRaises(ValueError):
            core.deal_roles(s)

    def test_traitor_count_is_clamped(self):
        s = game_with_players(5, traitors=99)
        self.assertEqual(roles(s).count("traitor"), 4)

    def test_add_players_skips_duplicates_and_blanks(self):
        s = core.new_state()
        self.assertEqual(core.add_players(s, "Ann, Bob\n ann ;; Cy"), (3, 1))
        with self.assertRaises(ValueError):
            core.add_players(s, " , ")

    def test_flip_role(self):
        s = game_with_players(8, traitors=2)
        p = s["players"][0]
        before = p["role"]
        core.flip_role(s, p["id"])
        self.assertNotEqual(p["role"], before)


class Groups(unittest.TestCase):
    def test_groups_cover_everyone_once(self):
        s = game_with_players()
        rid = s["rounds"][2]["id"]
        core.set_round_grouped(s, rid, True)
        core.assign_groups(s, rid, random.Random(3))
        g = s["rounds"][2]["groups"]
        flat = [x for grp in g for x in grp]
        self.assertEqual(sorted(flat), sorted(p["id"] for p in s["players"]))
        self.assertEqual(len(g), 5)
        self.assertTrue(all(3 <= len(x) <= 4 for x in g))
        self.assertEqual(len(s["rounds"][2]["results"]), 5)

    def test_traitors_are_spread_when_enabled(self):
        for seed in range(20):
            s = game_with_players(20, traitors=4)
            rid = s["rounds"][2]["id"]
            core.set_round_grouped(s, rid, True)
            core.assign_groups(s, rid, random.Random(seed))
            by_id = {p["id"]: p for p in s["players"]}
            counts = [sum(by_id[x]["role"] == "traitor" for x in grp) for grp in s["rounds"][2]["groups"]]
            self.assertLessEqual(max(counts), 1, counts)

    def test_groups_exclude_players_who_are_out(self):
        s = game_with_players()
        r0, r2 = s["rounds"][0], s["rounds"][2]
        victim = next(p["id"] for p in s["players"] if p["role"] == "faithful")
        core.set_murder(s, r0["id"], victim)
        core.set_round_grouped(s, r2["id"], True)
        core.assign_groups(s, r2["id"], random.Random(1))
        self.assertNotIn(victim, [x for grp in r2["groups"] for x in grp])

    def test_group_size_is_capped_by_players_left(self):
        s = game_with_players(5, traitors=1)
        rid = s["rounds"][2]["id"]
        core.set_round_grouped(s, rid, True)
        core.set_round_group_size(s, rid, 10)
        core.assign_groups(s, rid, random.Random(1))
        self.assertEqual(len(s["rounds"][2]["groups"]), 1)


class Pot(unittest.TestCase):
    def test_single_score_banks_stake_times_percent(self):
        s = core.new_state()
        r = s["rounds"][0]  # Balloon Keep-Up, stake 50, whole room
        core.set_score(s, r["id"], 0, 80)
        self.assertEqual(core.bank_round(s, r["id"]), 40)
        self.assertEqual(core.pot_total(s), 40)

    def test_group_scores_are_averaged(self):
        s = game_with_players()
        r = s["rounds"][2]  # Know Your Host, stake 60, teams
        core.assign_groups(s, r["id"], random.Random(2))
        with self.assertRaises(ValueError):
            core.bank_round(s, r["id"])
        for i, v in enumerate([100, 50, 50, 0, 50]):
            core.set_score(s, r["id"], i, v)
        self.assertEqual(core.bank_round(s, r["id"]), 30)

    def test_banked_round_is_locked_until_undone(self):
        s = core.new_state()
        r = s["rounds"][0]
        core.set_score(s, r["id"], 0, 100)
        core.bank_round(s, r["id"])
        for call in (lambda: core.set_score(s, r["id"], 0, 10),
                     lambda: core.set_round_stake(s, r["id"], 99),
                     lambda: core.set_round_game(s, r["id"], None)):
            with self.assertRaises(ValueError):
                call()
        core.unbank_round(s, r["id"])
        core.set_score(s, r["id"], 0, 10)

    def test_adjustments_and_money_format(self):
        s = core.new_state()
        core.add_adjust(s, "Best costume", 10)
        core.add_adjust(s, "Late penalty", -2.5)
        self.assertEqual(core.pot_total(s), 7.5)
        self.assertEqual(core.money(s, 7.5), "£7.50")
        self.assertEqual(core.money(s, 40), "£40")
        self.assertEqual(core.money(s, -2.5), "-£2.50")
        with self.assertRaises(ValueError):
            core.add_adjust(s, "", 5)

    def test_score_is_clamped(self):
        s = core.new_state()
        r = s["rounds"][0]
        core.set_score(s, r["id"], 0, 250)
        self.assertEqual(r["results"][0], 100)


class Finale(unittest.TestCase):
    def test_traitors_win_if_one_survives_otherwise_faithful(self):
        s = game_with_players(8, traitors=2)
        core.add_adjust(s, "Seed money", 100)
        f = core.finale(s)
        self.assertEqual(f["side"], "traitor")
        self.assertEqual(len(f["winners"]), 2)
        self.assertEqual(f["each"], 50)
        # banish both traitors across two rounds
        for rd, p in zip(s["rounds"], [p for p in s["players"] if p["role"] == "traitor"]):
            core.set_banished(s, rd["id"], p["id"])
        f = core.finale(s)
        self.assertEqual(f["side"], "faithful")
        self.assertEqual(len(f["winners"]), 6)
        self.assertAlmostEqual(f["each"], 100 / 6)

    def test_manual_override_and_empty_side(self):
        s = game_with_players(8, traitors=2)
        core.set_winner_mode(s, "faithful")
        self.assertEqual(core.finale(s)["side"], "faithful")
        with self.assertRaises(ValueError):
            core.set_winner_mode(s, "nobody")


class Consistency(unittest.TestCase):
    def setUp(self):
        self.s = game_with_players()
        self.faithful = [p["id"] for p in self.s["players"] if p["role"] == "faithful"]
        self.traitors = [p["id"] for p in self.s["players"] if p["role"] == "traitor"]
        self.r = [r["id"] for r in self.s["rounds"]]

    def test_only_a_faithful_can_be_murdered(self):
        with self.assertRaises(ValueError):
            core.set_murder(self.s, self.r[0], self.traitors[0])
        core.set_murder(self.s, self.r[0], self.faithful[0])

    def test_out_players_cannot_be_picked_in_later_rounds(self):
        core.set_murder(self.s, self.r[0], self.faithful[0])
        core.set_banished(self.s, self.r[0], self.faithful[1])
        for call in (lambda: core.set_murder(self.s, self.r[1], self.faithful[0]),
                     lambda: core.set_shield(self.s, self.r[1], self.faithful[1]),
                     lambda: core.set_banished(self.s, self.r[1], self.faithful[0])):
            with self.assertRaises(ValueError):
                call()

    def test_shielded_player_cannot_be_banished(self):
        core.set_shield(self.s, self.r[0], self.faithful[2])
        with self.assertRaises(ValueError):
            core.set_banished(self.s, self.r[0], self.faithful[2])

    def test_shielding_the_banished_player_clears_the_banishment(self):
        core.set_banished(self.s, self.r[0], self.faithful[2])
        core.set_shield(self.s, self.r[0], self.faithful[2])
        self.assertIsNone(self.s["rounds"][0]["banished"])

    def test_removing_a_player_clears_what_pointed_at_them(self):
        core.set_murder(self.s, self.r[0], self.faithful[0])
        core.remove_player(self.s, self.faithful[0])
        self.assertIsNone(self.s["rounds"][0]["murdered"])

    def test_alive_status_and_current_round(self):
        self.assertEqual(core.current_index(self.s), 0)
        core.set_murder(self.s, self.r[0], self.faithful[0])
        core.set_banished(self.s, self.r[0], self.faithful[1])
        self.assertEqual(core.current_index(self.s), 1)
        self.assertEqual(len(core.alive_players(self.s)), 18)
        self.assertEqual(core.status_of(self.s, self.faithful[0]), ("murdered", 1))
        self.assertEqual(core.status_of(self.s, self.faithful[1]), ("banished", 1))

    def test_deleting_a_game_unlinks_rounds(self):
        gid = self.s["games"][0]["id"]
        core.delete_game(self.s, gid)
        self.assertIsNone(self.s["rounds"][0]["game_id"])

    def test_choosing_a_game_copies_stake_and_mode(self):
        gid = next(g["id"] for g in self.s["games"] if g["name"] == "Know Your Host")
        core.set_round_game(self.s, self.r[0], gid)
        r = self.s["rounds"][0]
        self.assertEqual((r["stake"], r["grouped"], r["results"]), (60, True, []))

    def test_reset_keeps_games_and_rounds(self):
        core.reset_game(self.s)
        self.assertEqual((len(self.s["players"]), len(self.s["rounds"]), len(self.s["games"])), (0, 5, 7))

    def test_round_must_remain(self):
        s = core.new_state()
        for r in list(s["rounds"])[:-1]:
            core.delete_round(s, r["id"])
        with self.assertRaises(ValueError):
            core.delete_round(s, s["rounds"][0]["id"])


class Messages(unittest.TestCase):
    def test_role_messages(self):
        s = game_with_players(8, traitors=2)
        t = next(p for p in s["players"] if p["role"] == "traitor")
        f = next(p for p in s["players"] if p["role"] == "faithful")
        other = next(p["name"] for p in s["players"] if p["role"] == "traitor" and p["id"] != t["id"])
        self.assertIn("You are a TRAITOR", core.role_dm(s, t))
        self.assertIn(other, core.role_dm(s, t))
        self.assertIn("You are a FAITHFUL", core.role_dm(s, f))
        self.assertNotIn(t["name"], core.role_dm(s, f))
        self.assertIn(t["name"], core.traitors_text(s))

    def test_briefing_lists_teams_and_amount(self):
        s = game_with_players()
        rid = s["rounds"][2]["id"]
        core.assign_groups(s, rid, random.Random(5))
        text = core.brief_text(s, 2)
        self.assertIn("ROUND 3 · Know Your Host", text)
        self.assertIn("Pot at stake: £60", text)
        self.assertIn("Stags:", text)
        self.assertIn("Everyone plays together.", core.brief_text(s, 0))

    def test_private_notices(self):
        s = game_with_players()
        rid = s["rounds"][0]["id"]
        self.assertEqual(core.murder_text(s, 0), "")
        victim = next(p for p in s["players"] if p["role"] == "faithful")
        core.set_murder(s, rid, victim["id"])
        core.set_shield(s, rid, s["players"][-1]["id"])
        self.assertIn(victim["name"], core.murder_text(s, 0))
        self.assertIn("shield", core.shield_text(s, 0))


class Storage(unittest.TestCase):
    def test_backup_round_trip(self):
        s = game_with_players()
        core.set_murder(s, s["rounds"][0]["id"], next(p["id"] for p in s["players"] if p["role"] == "faithful"))
        self.assertEqual(core.from_json(core.to_json(s)), s)

    def test_bad_backups_are_rejected(self):
        for bad in ("not json", "[]", json.dumps({"v": 2}), json.dumps({"v": 1, "players": "x"})):
            with self.assertRaises(ValueError):
                core.from_json(bad)

    def test_store_persists_and_bumps_version(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "game.json")
            a = core.Store(path)
            self.assertEqual(a.version, 0)
            a.update(lambda st: core.add_players(st, "Ann, Bob, Cy"))
            self.assertEqual(a.version, 1)
            b = core.Store(path)
            self.assertEqual([p["name"] for p in b.state["players"]], ["Ann", "Bob", "Cy"])

    def test_failed_update_changes_nothing(self):
        st = core.Store()

        def bad(state):
            state["currency"] = "$"
            raise ValueError("nope")

        with self.assertRaises(ValueError):
            st.update(bad)
        self.assertEqual((st.state["currency"], st.version), ("£", 0))

    def test_snapshot_is_a_copy(self):
        st = core.Store()
        snap, _ = st.snapshot()
        snap["currency"] = "$"
        self.assertEqual(st.state["currency"], "£")

    def test_corrupt_file_falls_back_to_a_new_game(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "game.json")
            with open(path, "w") as fh:
                fh.write("{broken")
            st = core.Store(path)
            self.assertEqual(len(st.state["rounds"]), 5)

    def test_restore_replaces_state_for_everyone(self):
        st = core.Store()
        other = game_with_players(8, traitors=2)
        st.replace(other)
        self.assertEqual(len(st.state["players"]), 8)
        self.assertEqual(st.version, 1)


if __name__ == "__main__":
    unittest.main()
