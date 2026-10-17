"""Traitors Control Room: a shared host console for a Traitors party game.

Everyone who opens the app and knows the passcode works on the same game. The
game lives in one server-side store (see traitors_core.Store), so a host on a
laptop and a co-host on a phone stay in step without any extra setup.
"""
from __future__ import annotations

import hmac
import os
from pathlib import Path

import streamlit as st

import traitors_core as core

st.set_page_config(page_title="Traitors Control Room", layout="wide")

DATA_FILE = Path(os.environ.get("TRAITORS_DATA") or Path(__file__).resolve().parent / "data" / "game.json")


@st.cache_resource
def get_store(path: str) -> core.Store:
    return core.Store(path)


store = get_store(str(DATA_FILE))


# ---------------------------------------------------------------- access

def configured_passcode() -> str | None:
    code = os.environ.get("HOST_PASSCODE")
    if not code:
        try:
            code = st.secrets.get("HOST_PASSCODE")
        except Exception:  # no secrets file on this machine
            code = None
    return str(code) if code else None


def gate() -> None:
    code = configured_passcode()
    if not code:
        st.sidebar.warning("No HOST_PASSCODE is set, so anyone with this link can see roles and change the game.")
        return
    if st.session_state.get("authed"):
        return
    st.title("Traitors Control Room")
    with st.form("login_form"):
        entered = st.text_input("Host passcode", type="password")
        submitted = st.form_submit_button("Open")
    if submitted:
        if hmac.compare_digest(entered.encode(), code.encode()):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("That passcode is not right.")
    st.stop()


# ---------------------------------------------------------------- change helpers

def run(fn, *args, done: str | None = None):
    """Apply a change to the shared game and tell this host how it went."""
    try:
        result = store.update(lambda state: fn(state, *args))
    except ValueError as exc:
        st.toast(str(exc))
        return None
    if done:
        st.toast(done)
    return result


def do(fn, *args, done: str | None = None):
    return lambda: run(fn, *args, done=done)


def on_value(key: str, fn, *args):
    """Callback for a widget: pass its new value as the last argument of fn(state, ...)."""
    def callback():
        run(fn, *args, st.session_state[key])
    return callback


def confirm_action(label: str, key: str, fn, *args, done: str | None = None):
    """A button that needs a second tap before it does anything."""
    if st.session_state.get("armed") == key:
        yes, no = st.columns(2)
        if yes.button("Tap again to confirm", key=f"{key}-yes", type="primary"):
            st.session_state["armed"] = None
            run(fn, *args, done=done)
            st.rerun()
        if no.button("Cancel", key=f"{key}-no"):
            st.session_state["armed"] = None
            st.rerun()
    elif st.button(label, key=key):
        st.session_state["armed"] = key
        st.rerun()


# ---------------------------------------------------------------- display helpers

def role_text(p: dict, show: bool) -> str:
    if not p["role"]:
        return "No role"
    return p["role"].title() if show else "••••"


def tag(S: dict, pid: str, show: bool) -> str:
    p = core.player(S, pid)
    if not p:
        return "Unknown"
    if show and p["role"]:
        return f"{p['name']} · {p['role'].title()}"
    return p["name"]


def status_text(S: dict, p: dict) -> str:
    kind, rnd = core.status_of(S, p["id"])
    return "" if kind == "alive" else f"{kind.title()} · R{rnd}"


def person_select(S, show, label, key, options, current, fn, *args, none_label):
    opts = [None] + list(options)
    st.selectbox(
        label, opts,
        index=opts.index(current) if current in opts else 0,
        key=key,
        format_func=lambda pid: none_label if pid is None else tag(S, pid, show),
        on_change=on_value(key, fn, *args),
    )


# ---------------------------------------------------------------- players tab

def add_players_cb():
    result = run(core.add_players, st.session_state.get("add_names", ""))
    if result:
        added, skipped = result
        st.toast(f"{added} added" + (f", {skipped} duplicate skipped" if skipped else ""))


def tab_players(S, K, show):
    n = len(S["players"])
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.subheader("Add players")
        with st.form("add_players_form", clear_on_submit=True):
            st.text_area("Names, one per line or separated by commas", key="add_names", height=110)
            st.form_submit_button("Add players", on_click=add_players_cb)

        st.subheader("Deal roles")
        if n < 3:
            st.caption("Add at least 3 players to deal roles.")
        else:
            kmax = n - 1
            k = int(core.clamp(core.effective_traitors(S), 1, kmax))
            st.number_input("Traitors", min_value=1, max_value=kmax, value=k, step=1, key=K("traitors"),
                            on_change=on_value(K("traitors"), core.set_traitors))
            st.caption(f"{k} Traitors and {n - k} Faithfuls. Suggested for {n} players: {core.suggest_traitors(n)}.")
            if S["traitors"] is not None:
                st.button("Use the suggested number", key="traitors_auto", on_click=do(core.set_traitors, None))
            dealt = any(p["role"] for p in S["players"])
            if dealt:
                st.caption("Re-dealing clears shields, murders and banishments.")
                confirm_action("Re-deal roles", "redeal", core.deal_roles, k, done="Roles dealt")
            else:
                st.button("Deal roles randomly", key="deal", type="primary", on_click=do(core.deal_roles, k, done="Roles dealt"))

    with right:
        st.subheader(f"Roster · {len(core.alive_players(S))} alive")
        if not n:
            st.info("No players yet. Add names on the left, or load a set of example names to try things out.")
            st.button("Load 20 example names", key="load_examples", on_click=do(core.load_examples, done="Example names loaded"))
        for i, p in enumerate(S["players"], 1):
            cols = st.columns([0.5, 3, 1.6, 1.8])
            cols[0].write(f"{i:02d}")
            name_key = K(f"nm-{p['id']}")
            cols[1].text_input("Name", value=p["name"], key=name_key, label_visibility="collapsed",
                               on_change=on_value(name_key, core.rename_player, p["id"]))
            if p["role"] and show:
                cols[2].button(p["role"].title(), key=K(f"fl-{p['id']}"), help="Tap to swap this player's role",
                               on_click=do(core.flip_role, p["id"]))
            else:
                cols[2].write(role_text(p, show))
            cols[3].write(status_text(S, p))
        if n:
            st.divider()
            st.caption("Remove a player")
            pick = st.selectbox("Player to remove", [p["id"] for p in S["players"]], key=K("rm_pick"),
                                format_func=lambda pid: core.player(S, pid)["name"], label_visibility="collapsed")
            confirm_action("Remove player", "rm_player", core.remove_player, pick, done="Player removed")


# ---------------------------------------------------------------- games tab

def add_game_cb():
    ss = st.session_state
    run(core.add_game, ss.get("ng_name", ""), ss.get("ng_min", 5), ss.get("ng_stake", 0.0),
        ss.get("ng_grouped", False), ss.get("ng_desc", ""), ss.get("ng_rule", ""), done="Game added")


def tab_games(S, K, show):
    st.subheader("Add a game")
    with st.form("add_game_form", clear_on_submit=True):
        st.text_input("Name", key="ng_name", placeholder="Pass the Parcel")
        a, b, c = st.columns(3)
        a.number_input("Minutes", min_value=1, value=5, step=1, key="ng_min")
        b.number_input("Pot at stake", min_value=0.0, value=50.0, step=5.0, key="ng_stake")
        c.checkbox("Played in teams", key="ng_grouped")
        st.text_area("How it works", key="ng_desc", height=80)
        st.text_area("How the pot is scored", key="ng_rule", height=80, placeholder="Pot % = items found divided by 10.")
        st.form_submit_button("Add game", on_click=add_game_cb)

    st.subheader(f"Game catalog · {len(S['games'])}")
    if not S["games"]:
        st.info("No games yet. Add one above.")
    for g in S["games"]:
        gid = g["id"]
        used = sum(1 for r in S["rounds"] if r["game_id"] == gid)
        title = f"{g['name'] or 'Untitled game'} · {g['minutes']} min · {core.money(S, g['stake'])} · {'Teams' if g['grouped'] else 'Whole room'}"
        with st.expander(title):
            def key(field):
                return K(f"g-{gid}-{field}")
            st.text_input("Name", value=g["name"], key=key("name"), on_change=on_value(key("name"), core.update_game, gid, "name"))
            a, b, c = st.columns(3)
            a.number_input("Minutes", min_value=0, value=int(g["minutes"]), step=1, key=key("minutes"),
                           on_change=on_value(key("minutes"), core.update_game, gid, "minutes"))
            b.number_input("Pot at stake", min_value=0.0, value=float(g["stake"]), step=5.0, key=key("stake"),
                           on_change=on_value(key("stake"), core.update_game, gid, "stake"))
            c.checkbox("Played in teams", value=g["grouped"], key=key("grouped"),
                       on_change=on_value(key("grouped"), core.update_game, gid, "grouped"))
            st.text_area("How it works", value=g["desc"], key=key("desc"), height=80,
                         on_change=on_value(key("desc"), core.update_game, gid, "desc"))
            st.text_area("How the pot is scored", value=g["rule"], key=key("rule"), height=80,
                         on_change=on_value(key("rule"), core.update_game, gid, "rule"))
            st.caption(f"Used in {used} round{'' if used == 1 else 's'}. A round copies the stake when you pick the game.")
            confirm_action("Delete game", f"dg-{gid}", core.delete_game, gid, done="Game deleted")


# ---------------------------------------------------------------- rounds tab

def score_input(S, K, r, idx, label, lock):
    current = r["results"][idx] if idx < len(r["results"]) else None
    key = K(f"sc-{r['id']}-{idx}")
    st.number_input(f"{label}: share of the pot won (%)", min_value=0.0, max_value=100.0, step=5.0,
                    value=None if current is None else float(current), placeholder="0 to 100",
                    key=key, disabled=lock, on_change=on_value(key, core.set_score, r["id"], idx))


def round_card(S, K, show, i, r, cur):
    rid = r["id"]
    g = core.game(S, r["game_id"])
    lock = r["banked"] is not None
    label = f"R{i + 1} · {g['name'] if g else 'No game chosen'}"
    if lock:
        label += f" · +{core.money(S, r['banked'])}"
    if i == cur:
        label += " · current"

    with st.expander(label, expanded=(i == cur)):
        st.markdown("**1 · Murder reveal**")
        victims = [p["id"] for p in S["players"] if p["role"] == "faithful" and p["id"] not in core.out_before(S, i, False)]
        person_select(S, show, "Faithful chosen by the Traitors", K(f"mu-{rid}"), victims, r["murdered"],
                      core.set_murder, rid, none_label="No murder this round")

        st.markdown("**2 · Mission**")
        game_ids = [x["id"] for x in S["games"]]
        gkey = K(f"gm-{rid}")
        opts = [None] + game_ids
        c1, c2 = st.columns(2)
        c1.selectbox("Game", opts, index=opts.index(r["game_id"]) if r["game_id"] in opts else 0, key=gkey, disabled=lock,
                     format_func=lambda x: "Choose a game" if x is None else core.game(S, x)["name"],
                     on_change=on_value(gkey, core.set_round_game, rid))
        skey = K(f"st-{rid}")
        c2.number_input("Pot at stake", min_value=0.0, value=float(r["stake"] or 0), step=5.0, key=skey, disabled=lock,
                        on_change=on_value(skey, core.set_round_stake, rid))
        if g:
            st.caption("  \n".join(x for x in (g["desc"], g["rule"], f"{g['minutes']} min") if x))
        pkey = K(f"gr-{rid}")
        st.checkbox("Played in teams", value=r["grouped"], key=pkey, disabled=lock,
                    on_change=on_value(pkey, core.set_round_grouped, rid))

        if r["grouped"]:
            a, b = st.columns(2)
            zkey = K(f"gs-{rid}")
            a.number_input("Players per group", min_value=2, max_value=10, value=int(r["group_size"] or S["group_size"]),
                           step=1, key=zkey, disabled=lock, on_change=on_value(zkey, core.set_round_group_size, rid))
            b.write("")
            b.button("Reshuffle groups" if r["groups"] else "Assign groups", key=f"assign-{rid}-{K('')}", disabled=lock,
                     on_click=do(core.assign_groups, rid))
            if r["groups"]:
                out = core.out_before(S, i, True)
                for gi, ids in enumerate(r["groups"]):
                    members = [core.player(S, x) for x in ids if core.player(S, x) and x not in out]
                    names = ", ".join(
                        m["name"] + (" (T)" if show and m["role"] == "traitor" else "") for m in members)
                    with st.container(border=True):
                        st.markdown(f"**{core.group_name(gi)}** · {len(members)} players")
                        st.write(names)
                        score_input(S, K, r, gi, core.group_name(gi), lock)
            else:
                st.caption("Assign groups, then score each one.")
        else:
            score_input(S, K, r, 0, "The room", lock)

        pct = core.round_pct(r)
        amount = core.round_amount(r)
        left, right = st.columns([3, 1])
        if pct is None:
            left.write("Score the mission to see what goes in the pot.")
        else:
            left.write(f"{core.money(S, r['stake'])} × {round(pct, 1):g}% = **{core.money(S, amount)}**")
        if lock:
            right.button("Undo bank", key=K(f"ub-{rid}"), on_click=do(core.unbank_round, rid))
        else:
            right.button("Bank to pot", key=K(f"bk-{rid}"), type="primary",
                         on_click=do(core.bank_round, rid, done="Added to the pot"))

        pool = [p["id"] for p in S["players"] if p["id"] not in core.out_before(S, i, True)]
        person_select(S, show, "Shield awarded to", K(f"sh-{rid}"), pool, r["shield"],
                      core.set_shield, rid, none_label="No shield this round")

        st.markdown("**3 · Banishment**")
        vote = [x for x in pool if x != r["shield"]]
        person_select(S, show, "Player banished by the vote", K(f"ba-{rid}"), vote, r["banished"],
                      core.set_banished, rid, none_label="Nobody banished yet")
        banished = core.player(S, r["banished"])
        if banished:
            st.write(f"Reveal: **{role_text(banished, show)}**" if show else "Roles are hidden. Show roles to see the reveal.")

        if len(S["rounds"]) > 1:
            confirm_action("Remove round", f"dr-{rid}", core.delete_round, rid, done="Round removed")


def tab_rounds(S, K, show):
    a, b, c = st.columns([1, 1, 1])
    a.number_input("Default players per group", min_value=2, max_value=10, value=int(S["group_size"]), step=1,
                   key=K("dgs"), on_change=on_value(K("dgs"), core.set_group_size))
    b.checkbox("Spread Traitors across groups", value=S["spread"], key=K("spread"),
               on_change=on_value(K("spread"), core.set_spread))
    c.button("Add round", key="add_round", on_click=do(core.add_round, done="Round added"))
    st.caption("Each round runs in order: murder reveal, mission, banishment.")
    cur = core.current_index(S)
    for i, r in enumerate(S["rounds"]):
        round_card(S, K, show, i, r, cur)


# ---------------------------------------------------------------- pot tab

def adjust_cb():
    run(core.add_adjust, st.session_state.get("adj_label", ""), st.session_state.get("adj_amt", 0.0), done="Added to the ledger")


def tab_pot(S, K, show):
    total, most = core.pot_total(S), core.max_pot(S)
    st.metric("Prize pot", core.money(S, total))
    st.progress(float(core.clamp(total / most, 0.0, 1.0)) if most > 0 else 0.0)
    st.caption(f"Most it could reach from round stakes: {core.money(S, most)}")
    st.text_input("Currency symbol", value=S["currency"], max_chars=3, key=K("cur"),
                  on_change=on_value(K("cur"), core.set_currency))

    st.subheader("Ledger")
    rows = []
    for i, r in enumerate(S["rounds"]):
        g = core.game(S, r["game_id"])
        pct = core.round_pct(r)
        rows.append({
            "Round": f"R{i + 1}", "Game": g["name"] if g else "No game chosen",
            "Score": "—" if pct is None else f"{round(pct, 1):g}%",
            "Added": "pending" if r["banked"] is None else f"+{core.money(S, r['banked'])}",
        })
    for a in S["adjust"]:
        rows.append({"Round": "Adj.", "Game": a["label"], "Score": "—",
                     "Added": ("+" if a["amount"] > 0 else "") + core.money(S, a["amount"])})
    st.table(rows)
    for a in S["adjust"]:
        st.button(f"Remove adjustment: {a['label']}", key=K(f"da-{a['id']}"), on_click=do(core.delete_adjust, a["id"]))

    with st.form("adjust_form", clear_on_submit=True):
        st.text_input("Bonus or penalty", key="adj_label", placeholder="Bonus for the best costume")
        st.number_input("Amount (use a minus to deduct)", value=0.0, step=1.0, key="adj_amt")
        st.form_submit_button("Add to ledger", on_click=adjust_cb)

    st.subheader("Prize split")
    modes = ["auto", "faithful", "traitor"]
    labels = {"auto": "Auto", "faithful": "Faithfuls", "traitor": "Traitors"}
    st.radio("Who wins", modes, index=modes.index(S["winner_mode"]), format_func=labels.get, horizontal=True,
             key=K("winner"), on_change=on_value(K("winner"), core.set_winner_mode))
    st.caption("Auto: if any Traitor is still alive at the end they win, otherwise the Faithfuls do.")
    if not any(p["role"] for p in S["players"]):
        st.info("Deal roles on the Players tab to see the split.")
    else:
        f = core.finale(S)
        side = "Traitors" if f["side"] == "traitor" else "Faithfuls"
        st.write(f"If the game ended now: **{side} win** with {len(f['winners'])} player{'' if len(f['winners']) == 1 else 's'} left.")
        if f["winners"]:
            st.metric("Each winner gets", core.money(S, f["each"]))
            if show:
                st.write(", ".join(p["name"] for p in f["winners"]))
        else:
            st.write("Nobody is left on that side, so the pot is not shared.")


# ---------------------------------------------------------------- messages tab

def tab_messages(S, K, show):
    st.caption("Copy a message with the button at the top right of each box, then paste it into WhatsApp.")
    st.subheader("Role messages")
    if not S["players"]:
        st.info("Add players first.")
    else:
        reveal = show or st.checkbox("Show role messages", key="reveal_dm")
        if reveal:
            pick = st.selectbox("Player", [p["id"] for p in S["players"]], key=K("dm_pick"),
                                format_func=lambda pid: core.player(S, pid)["name"])
            st.code(core.role_dm(S, core.player(S, pick)), language=None)
            with st.expander("All players"):
                for p in S["players"]:
                    st.markdown(f"**{p['name']}**")
                    st.code(core.role_dm(S, p), language=None)
        else:
            st.caption("Roles are hidden. Tick the box to show these messages.")

    st.subheader("Traitors’ private chat")
    st.caption("Make a WhatsApp group with an innocent name and add only the Traitors and yourself.")
    if show or st.session_state.get("reveal_dm"):
        st.code(core.traitors_text(S), language=None)
    else:
        st.caption("Roles are hidden. Tick the box above to show this message.")

    st.subheader("Round messages")
    cur = core.current_index(S)
    i = st.selectbox("Round", list(range(len(S["rounds"]))), index=cur, key="msg_round",
                     format_func=lambda x: f"Round {x + 1} · {(core.game(S, S['rounds'][x]['game_id']) or {'name': 'No game chosen'})['name']}")
    st.markdown("**Briefing for the main group chat**")
    st.code(core.brief_text(S, i), language=None)
    st.markdown("**Private note to the murder victim**")
    text = core.murder_text(S, i)
    if text:
        st.code(text, language=None)
    else:
        st.caption("Pick a murder victim in this round first.")
    st.markdown("**Private note to the shield winner**")
    text = core.shield_text(S, i)
    if text:
        st.code(text, language=None)
    else:
        st.caption("Award a shield in this round first.")


# ---------------------------------------------------------------- backup and sidebar

def restore_cb():
    upload = st.session_state.get("restore_file")
    if upload is None:
        st.toast("Choose a backup file first.")
        return
    try:
        state = core.from_json(upload.getvalue().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        st.toast("That is not a Traitors backup.")
        return
    store.replace(state)
    st.toast("Backup restored")


def sidebar(S):
    with st.sidebar:
        st.header("Host tools")
        hide = st.toggle("Hide roles on this screen", key="hide_roles", value=False,
                         help="Only affects this device. Your co-host keeps their own setting.")
        st.caption("The game is shared. Anyone with the link and passcode sees the same game and updates within a few seconds.")
        st.divider()
        st.download_button("Download backup", core.to_json(S), file_name="traitors-backup.json", mime="application/json")
        st.file_uploader("Restore a backup", type="json", key="restore_file")
        st.button("Restore backup", key="restore_btn", on_click=restore_cb)
        st.divider()
        confirm_action("Start a new game", "reset_game", core.reset_game, done="Ready for your players")
        if store.save_error:
            st.warning("Could not save to disk. Download a backup now and then again after big changes.")
        return not hide


# ---------------------------------------------------------------- page

gate()
S, version = store.snapshot()
st.session_state["seen_version"] = version


def K(name: str) -> str:
    """Widget keys carry the game version so every widget shows the shared truth after a change."""
    return f"{name}-{version}"


show_roles = sidebar(S)

st.title("Traitors Control Room")
st.caption("Host console. Keep this screen away from the players.")

alive = core.alive_players(S)
traitors_total = sum(1 for p in S["players"] if p["role"] == "traitor")
traitors_alive = sum(1 for p in alive if p["role"] == "traitor")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Players left", f"{len(alive)} of {len(S['players'])}")
m2.metric("Traitors left", f"{traitors_alive} of {traitors_total}" if traitors_total else "not dealt")
m3.metric("Round", f"{min(core.current_index(S) + 1, len(S['rounds']))} of {len(S['rounds'])}")
m4.metric("Pot", core.money(S, core.pot_total(S)))

t_players, t_games, t_rounds, t_pot, t_msgs = st.tabs(["Players", "Games", "Rounds", "Pot", "Messages"])
with t_players:
    tab_players(S, K, show_roles)
with t_games:
    tab_games(S, K, show_roles)
with t_rounds:
    tab_rounds(S, K, show_roles)
with t_pot:
    tab_pot(S, K, show_roles)
with t_msgs:
    tab_messages(S, K, show_roles)


@st.fragment(run_every=3)
def watch_for_changes():
    """Refresh this page when someone else changes the game."""
    if store.version != st.session_state.get("seen_version"):
        st.rerun()


watch_for_changes()
