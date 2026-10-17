"""Game logic for the Traitors control room.

Standard library only, so it can be tested without Streamlit. The game state is a
plain JSON-friendly dict. Every mutator takes the state as its first argument,
validates before it changes anything, and raises ValueError with a message that is
fit to show to a host.
"""
from __future__ import annotations

import copy
import json
import math
import os
import random
import re
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

GROUP_NAMES = [
    "Stags", "Ravens", "Thistles", "Herons", "Otters",
    "Wolves", "Falcons", "Badgers", "Foxes", "Owls",
]
EXAMPLE_NAMES = [
    "Aarav", "Beth", "Callum", "Dina", "Elliot", "Farah", "Gareth", "Hana", "Imogen", "Jamal",
    "Kiran", "Lucy", "Marcus", "Nia", "Owen", "Priya", "Quentin", "Rosa", "Sam", "Tess",
]


# ---------------------------------------------------------------- basics

def uid() -> str:
    return uuid.uuid4().hex[:7]


def clamp(n: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, n))


def group_name(i: int) -> str:
    return GROUP_NAMES[i] if i < len(GROUP_NAMES) else f"Group {i + 1}"


def seed_games() -> list[dict]:
    def g(name, minutes, stake, grouped, desc, rule):
        return {"id": uid(), "name": name, "minutes": minutes, "stake": stake,
                "grouped": grouped, "desc": desc, "rule": rule}

    return [
        g("Balloon Keep-Up", 5, 50, False,
          "The whole room keeps one balloon off the floor for 2 minutes. Traitors can quietly let it drop.",
          "Pot % = seconds in the air divided by 120."),
        g("Blind Taste Test", 5, 50, False,
          "Three blindfolded volunteers guess 5 snacks or drinks.",
          "Pot % = correct guesses divided by 5."),
        g("Know Your Host", 5, 60, True,
          "Eight quick questions about the people in the room. Teams answer by hand or phone.",
          "Pot % per team = correct answers divided by 8."),
        g("Photo Scavenger Hunt", 5, 60, True,
          "Teams get 5 minutes to photograph 5 things, like something blue or the oldest thing here.",
          "Pot % per team = photos found divided by 5."),
        g("Memory Tray", 5, 40, False,
          "Show 15 random objects for 30 seconds, cover them, and the room writes down what it remembers.",
          "Pot % = items remembered divided by 15, capped at 100%."),
        g("Guess the Jar", 3, 30, False,
          "Everyone guesses how many sweets are in the jar.",
          "Best guess within 10% of the true count = 100%, within 25% = 50%, otherwise 0%."),
        g("One-Word Story", 4, 30, False,
          "The room builds a story one word at a time and tries to reach 30 words without a pause.",
          "Pot % = words reached divided by 30."),
    ]


def new_round(game: Optional[dict] = None) -> dict:
    grouped = bool(game and game["grouped"])
    return {
        "id": uid(),
        "game_id": game["id"] if game else None,
        "stake": game["stake"] if game else 0,
        "grouped": grouped,
        "group_size": None,
        "groups": None,
        "results": [] if grouped else [None],
        "shield": None,
        "murdered": None,
        "banished": None,
        "banked": None,
    }


def new_state() -> dict:
    games = seed_games()
    return {
        "v": 1,
        "currency": "£",
        "traitors": None,
        "group_size": 4,
        "spread": True,
        "winner_mode": "auto",
        "players": [],
        "games": games,
        "rounds": [new_round(g) for g in games[:5]],
        "adjust": [],
    }


# ---------------------------------------------------------------- lookups

def player(state: dict, pid: Optional[str]) -> Optional[dict]:
    return next((p for p in state["players"] if p["id"] == pid), None)


def game(state: dict, gid: Optional[str]) -> Optional[dict]:
    return next((g for g in state["games"] if g["id"] == gid), None)


def get_round(state: dict, rid: str) -> dict:
    r = next((r for r in state["rounds"] if r["id"] == rid), None)
    if r is None:
        raise ValueError("That round no longer exists.")
    return r


def round_index(state: dict, rid: str) -> int:
    for i, r in enumerate(state["rounds"]):
        if r["id"] == rid:
            return i
    raise ValueError("That round no longer exists.")


# ---------------------------------------------------------------- derived values

def suggest_traitors(n: int) -> int:
    return 1 if n < 3 else max(1, int(n / 5 + 0.5))


def effective_traitors(state: dict) -> int:
    n = len(state["players"])
    k = state["traitors"] if state["traitors"] is not None else suggest_traitors(n)
    return int(clamp(k, 1, max(1, n - 1)))


def out_before(state: dict, idx: int, with_murder: bool = False) -> set:
    """Players already out when round idx starts (optionally including its own murder)."""
    out: set = set()
    for i, r in enumerate(state["rounds"]):
        if i < idx:
            if r["murdered"]:
                out.add(r["murdered"])
            if r["banished"]:
                out.add(r["banished"])
        elif i == idx and with_murder and r["murdered"]:
            out.add(r["murdered"])
    return out


def all_out(state: dict) -> set:
    out: set = set()
    for r in state["rounds"]:
        if r["murdered"]:
            out.add(r["murdered"])
        if r["banished"]:
            out.add(r["banished"])
    return out


def alive_players(state: dict) -> list[dict]:
    out = all_out(state)
    return [p for p in state["players"] if p["id"] not in out]


def status_of(state: dict, pid: str) -> tuple[str, Optional[int]]:
    for i, r in enumerate(state["rounds"]):
        if r["murdered"] == pid:
            return ("murdered", i + 1)
        if r["banished"] == pid:
            return ("banished", i + 1)
    return ("alive", None)


def current_index(state: dict) -> int:
    for i, r in enumerate(state["rounds"]):
        if not r["banished"]:
            return i
    return max(0, len(state["rounds"]) - 1)


def round_pct(r: dict) -> Optional[float]:
    v = r["results"]
    if not v or any(x is None for x in v):
        return None
    return sum(v) / len(v)


def round_amount(r: dict) -> Optional[float]:
    p = round_pct(r)
    if p is None:
        return None
    return math.floor(r["stake"] * p + 0.5) / 100


def pot_total(state: dict) -> float:
    banked = sum(r["banked"] for r in state["rounds"] if r["banked"] is not None)
    return banked + sum(a["amount"] for a in state["adjust"])


def max_pot(state: dict) -> float:
    return sum(r["stake"] or 0 for r in state["rounds"])


def money(state: dict, n: float) -> str:
    v = math.floor(abs(n) * 100 + 0.5) / 100
    sign = "-" if n < 0 and v else ""
    text = f"{int(v)}" if v == int(v) else f"{v:.2f}"
    return f"{sign}{state['currency']}{text}"


def finale(state: dict) -> dict:
    al = alive_players(state)
    traitors = [p for p in al if p["role"] == "traitor"]
    faithful = [p for p in al if p["role"] == "faithful"]
    mode = state["winner_mode"]
    side = ("traitor" if traitors else "faithful") if mode == "auto" else mode
    winners = traitors if side == "traitor" else faithful
    total = pot_total(state)
    return {"side": side, "winners": winners, "total": total,
            "each": total / len(winners) if winners else 0.0}


def sanitize(state: dict) -> None:
    """Drop murders, shields and banishments that no longer make sense."""
    ids = {p["id"] for p in state["players"]}
    out: set = set()
    for r in state["rounds"]:
        if r["murdered"] and (r["murdered"] not in ids or r["murdered"] in out):
            r["murdered"] = None
        mid = set(out)
        if r["murdered"]:
            mid.add(r["murdered"])
        if r["shield"] and (r["shield"] not in ids or r["shield"] in mid):
            r["shield"] = None
        if r["banished"] and (r["banished"] not in ids or r["banished"] in mid or r["banished"] == r["shield"]):
            r["banished"] = None
        if r["murdered"]:
            out.add(r["murdered"])
        if r["banished"]:
            out.add(r["banished"])


# ---------------------------------------------------------------- players

def add_players(state: dict, raw: str) -> tuple[int, int]:
    names = [s.strip() for s in re.split(r"[\n,;]+", raw or "") if s.strip()]
    if not names:
        raise ValueError("Type at least one name.")
    have = {p["name"].lower() for p in state["players"]}
    added = skipped = 0
    for n in names:
        if n.lower() in have:
            skipped += 1
            continue
        have.add(n.lower())
        state["players"].append({"id": uid(), "name": n[:40], "role": None})
        added += 1
    return added, skipped


def load_examples(state: dict) -> None:
    if state["players"]:
        raise ValueError("Examples only load into an empty roster.")
    add_players(state, "\n".join(EXAMPLE_NAMES))


def remove_player(state: dict, pid: str) -> None:
    state["players"] = [p for p in state["players"] if p["id"] != pid]
    sanitize(state)


def rename_player(state: dict, pid: str, name: str) -> None:
    p = player(state, pid)
    if p is None:
        raise ValueError("That player no longer exists.")
    name = (name or "").strip()
    if not name:
        raise ValueError("A player needs a name.")
    p["name"] = name[:40]


def flip_role(state: dict, pid: str) -> None:
    p = player(state, pid)
    if p is None or not p["role"]:
        raise ValueError("That player has no role to swap.")
    p["role"] = "faithful" if p["role"] == "traitor" else "traitor"


def set_traitors(state: dict, k: Optional[int]) -> None:
    state["traitors"] = None if k is None else int(max(1, k))


def deal_roles(state: dict, k: Optional[int] = None, rng: Optional[random.Random] = None) -> int:
    n = len(state["players"])
    if n < 3:
        raise ValueError("Add at least 3 players before dealing roles.")
    k = effective_traitors(state) if k is None else int(clamp(k, 1, n - 1))
    rng = rng or random.SystemRandom()
    ids = [p["id"] for p in state["players"]]
    rng.shuffle(ids)
    traitors = set(ids[:k])
    for p in state["players"]:
        p["role"] = "traitor" if p["id"] in traitors else "faithful"
    for r in state["rounds"]:
        r["shield"] = r["murdered"] = r["banished"] = None
    return k


def reset_game(state: dict) -> None:
    """Clear players, pot and results. The game catalog stays."""
    state["players"] = []
    state["adjust"] = []
    state["traitors"] = None
    for r in state["rounds"]:
        r["groups"] = None
        r["results"] = [] if r["grouped"] else [None]
        r["shield"] = r["murdered"] = r["banished"] = r["banked"] = None


# ---------------------------------------------------------------- settings

def set_group_size(state: dict, size: int) -> None:
    state["group_size"] = int(clamp(size, 2, 10))


def set_spread(state: dict, spread: bool) -> None:
    state["spread"] = bool(spread)


def set_currency(state: dict, symbol: str) -> None:
    state["currency"] = (symbol or "").strip()[:3] or "£"


def set_winner_mode(state: dict, mode: str) -> None:
    if mode not in ("auto", "faithful", "traitor"):
        raise ValueError("Choose Auto, Faithfuls or Traitors.")
    state["winner_mode"] = mode


def add_adjust(state: dict, label: str, amount: float) -> None:
    label = (label or "").strip()
    if not label or not amount:
        raise ValueError("Add a label and a non-zero amount.")
    state["adjust"].append({"id": uid(), "label": label[:60], "amount": float(amount)})


def delete_adjust(state: dict, aid: str) -> None:
    state["adjust"] = [a for a in state["adjust"] if a["id"] != aid]


# ---------------------------------------------------------------- games

def add_game(state: dict, name: str, minutes: int, stake: float, grouped: bool, desc: str, rule: str) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Give the game a name.")
    state["games"].append({
        "id": uid(), "name": name[:60], "minutes": int(max(0, minutes or 0)),
        "stake": float(max(0, stake or 0)), "grouped": bool(grouped),
        "desc": (desc or "").strip(), "rule": (rule or "").strip(),
    })


def update_game(state: dict, gid: str, field: str, value: Any) -> None:
    g = game(state, gid)
    if g is None:
        raise ValueError("That game no longer exists.")
    if field == "minutes":
        g[field] = int(max(0, value or 0))
    elif field == "stake":
        g[field] = float(max(0, value or 0))
    elif field == "grouped":
        g[field] = bool(value)
    elif field in ("name", "desc", "rule"):
        g[field] = str(value or "")
    else:
        raise ValueError("Unknown game field.")


def delete_game(state: dict, gid: str) -> None:
    state["games"] = [g for g in state["games"] if g["id"] != gid]
    for r in state["rounds"]:
        if r["game_id"] == gid:
            r["game_id"] = None


# ---------------------------------------------------------------- rounds

def _unlocked(r: dict) -> dict:
    if r["banked"] is not None:
        raise ValueError("This round is banked. Undo the bank to change it.")
    return r


def add_round(state: dict) -> str:
    r = new_round(state["games"][0] if state["games"] else None)
    state["rounds"].append(r)
    return r["id"]


def delete_round(state: dict, rid: str) -> None:
    if len(state["rounds"]) < 2:
        raise ValueError("Keep at least one round.")
    get_round(state, rid)
    state["rounds"] = [r for r in state["rounds"] if r["id"] != rid]
    sanitize(state)


def set_round_game(state: dict, rid: str, gid: Optional[str]) -> None:
    r = _unlocked(get_round(state, rid))
    r["game_id"] = gid or None
    g = game(state, r["game_id"])
    if g:
        r["stake"] = g["stake"]
        r["grouped"] = g["grouped"]
    r["groups"] = None
    r["results"] = [] if r["grouped"] else [None]


def set_round_stake(state: dict, rid: str, stake: Optional[float]) -> None:
    _unlocked(get_round(state, rid))["stake"] = float(max(0, stake or 0))


def set_round_grouped(state: dict, rid: str, grouped: bool) -> None:
    r = _unlocked(get_round(state, rid))
    r["grouped"] = bool(grouped)
    r["groups"] = None
    r["results"] = [] if r["grouped"] else [None]


def set_round_group_size(state: dict, rid: str, size: int) -> None:
    get_round(state, rid)["group_size"] = int(clamp(size, 2, 10))


def assign_groups(state: dict, rid: str, rng: Optional[random.Random] = None) -> None:
    r = _unlocked(get_round(state, rid))
    idx = round_index(state, rid)
    out = out_before(state, idx, True)
    pool = [p for p in state["players"] if p["id"] not in out]
    if len(pool) < 2:
        raise ValueError("Not enough players left to make groups.")
    rng = rng or random.SystemRandom()
    size = int(clamp(r["group_size"] or state["group_size"], 2, len(pool)))
    k = max(1, math.ceil(len(pool) / size))
    if state["spread"]:
        traitors = [p for p in pool if p["role"] == "traitor"]
        others = [p for p in pool if p["role"] != "traitor"]
        rng.shuffle(traitors)
        rng.shuffle(others)
        order = traitors + others
    else:
        order = pool[:]
        rng.shuffle(order)
    offset = rng.randrange(k)
    groups: list[list[str]] = [[] for _ in range(k)]
    for i, p in enumerate(order):
        groups[(i + offset) % k].append(p["id"])
    r["groups"] = groups
    r["results"] = [None] * k


def set_score(state: dict, rid: str, idx: int, value: Optional[float]) -> None:
    r = _unlocked(get_round(state, rid))
    if idx < 0 or idx >= len(r["results"]):
        raise ValueError("Assign groups before scoring them.")
    r["results"][idx] = None if value is None else float(clamp(value, 0, 100))


def bank_round(state: dict, rid: str) -> float:
    r = get_round(state, rid)
    amount = round_amount(r)
    if amount is None:
        raise ValueError("Score every group first." if r["grouped"] else "Score the mission first.")
    r["banked"] = amount
    return amount


def unbank_round(state: dict, rid: str) -> None:
    get_round(state, rid)["banked"] = None


def set_murder(state: dict, rid: str, pid: Optional[str]) -> None:
    r = get_round(state, rid)
    if pid:
        p = player(state, pid)
        if p is None or p["role"] != "faithful" or pid in out_before(state, round_index(state, rid), False):
            raise ValueError("Pick a Faithful who is still in the game.")
    r["murdered"] = pid or None
    sanitize(state)


def set_shield(state: dict, rid: str, pid: Optional[str]) -> None:
    r = get_round(state, rid)
    if pid and (player(state, pid) is None or pid in out_before(state, round_index(state, rid), True)):
        raise ValueError("Pick a player who is still in the game.")
    r["shield"] = pid or None
    sanitize(state)


def set_banished(state: dict, rid: str, pid: Optional[str]) -> None:
    r = get_round(state, rid)
    if pid:
        if player(state, pid) is None or pid in out_before(state, round_index(state, rid), True):
            raise ValueError("Pick a player who is still in the game.")
        if pid == r["shield"]:
            raise ValueError("That player is shielded this round.")
    r["banished"] = pid or None
    sanitize(state)


# ---------------------------------------------------------------- messages

def role_dm(state: dict, p: dict) -> str:
    if p["role"] == "traitor":
        allies = [q["name"] for q in state["players"] if q["role"] == "traitor" and q["id"] != p["id"]]
        return (f"THE TRAITORS · secret message for {p['name']}\n\nYou are a TRAITOR.\n"
                + (f"Your fellow Traitors: {', '.join(allies)}.\n" if allies else "")
                + "You will be added to the Traitors’ private chat. Each round, agree on one Faithful to murder "
                  "before the mission starts. Stay in character and never show this message to anyone.")
    if p["role"] == "faithful":
        return (f"THE TRAITORS · secret message for {p['name']}\n\nYou are a FAITHFUL.\n"
                "Work out who the Traitors are and banish them at the round table. "
                "Never show this message to anyone.")
    return f"No role has been dealt for {p['name']} yet."


def traitors_text(state: dict) -> str:
    names = [p["name"] for p in state["players"] if p["role"] == "traitor"]
    return ("THE ROUND TABLE · Traitors only\n\nMembers: " + (", ".join(names) or "none yet")
            + "\n\nEach round, send me ONE Faithful’s name before the mission starts. "
              "If you cannot agree in time, I will choose for you. Never mention this chat in the room.")


def brief_text(state: dict, i: int) -> str:
    if not 0 <= i < len(state["rounds"]):
        return ""
    r = state["rounds"][i]
    g = game(state, r["game_id"])
    lines = [f"ROUND {i + 1} · {g['name'] if g else 'Mission'}"]
    if g and g["desc"]:
        lines += ["", g["desc"]]
    lines += ["", f"Pot at stake: {money(state, r['stake'])}" + (f". {g['rule']}" if g and g["rule"] else "")]
    if r["grouped"] and r["groups"]:
        out = out_before(state, i, True)
        lines += ["", "Teams:"]
        for gi, ids in enumerate(r["groups"]):
            names = [player(state, x)["name"] for x in ids if player(state, x) and x not in out]
            lines.append(f"{group_name(gi)}: {', '.join(names)}")
    else:
        lines += ["", "Everyone plays together."]
    return "\n".join(lines)


def murder_text(state: dict, i: int) -> str:
    r = state["rounds"][i] if 0 <= i < len(state["rounds"]) else None
    p = player(state, r["murdered"]) if r else None
    if not p:
        return ""
    return (f"You have been murdered by the Traitors, {p['name']}. Stay silent and do not hint at who did it "
            f"until the reveal at the start of round {i + 1}. You can still watch the game and help judge missions.")


def shield_text(state: dict, i: int) -> str:
    r = state["rounds"][i] if 0 <= i < len(state["rounds"]) else None
    p = player(state, r["shield"]) if r else None
    if not p:
        return ""
    return (f"{p['name']}, you have won a shield in round {i + 1}. You cannot be banished in this round’s vote. "
            "Keep it secret until you choose to reveal it.")


# ---------------------------------------------------------------- backup and storage

def validate_state(obj: Any) -> dict:
    if not isinstance(obj, dict) or obj.get("v") != 1:
        raise ValueError("That is not a Traitors backup.")
    for key in ("players", "games", "rounds", "adjust"):
        if not isinstance(obj.get(key), list):
            raise ValueError("That is not a Traitors backup.")
    base = new_state()
    for key, default in base.items():
        obj.setdefault(key, default)
    for p in obj["players"]:
        if not (isinstance(p, dict) and p.get("id") and isinstance(p.get("name"), str)):
            raise ValueError("That is not a Traitors backup.")
        p.setdefault("role", None)
    for r in obj["rounds"]:
        if not (isinstance(r, dict) and r.get("id")):
            raise ValueError("That is not a Traitors backup.")
        for key, default in new_round().items():
            if key != "id":
                r.setdefault(key, default)
    sanitize(obj)
    return obj


def to_json(state: dict) -> str:
    return json.dumps(state, indent=2, ensure_ascii=False)


def from_json(text: str) -> dict:
    try:
        return validate_state(json.loads(text))
    except json.JSONDecodeError:
        raise ValueError("That is not a Traitors backup.")


class Store:
    """The one shared game. Every host session reads and writes through this."""

    def __init__(self, path: Optional[os.PathLike | str] = None):
        self.path = Path(path) if path else None
        self._lock = threading.RLock()
        self.version = 0
        self.save_error: Optional[str] = None
        self.state = self._load() or new_state()

    def _load(self) -> Optional[dict]:
        if not self.path or not self.path.exists():
            return None
        try:
            return from_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _save(self) -> None:
        if not self.path:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(to_json(self.state))
            os.replace(tmp, self.path)
            self.save_error = None
        except OSError as exc:
            self.save_error = str(exc)

    def snapshot(self) -> tuple[dict, int]:
        with self._lock:
            return copy.deepcopy(self.state), self.version

    def update(self, fn: Callable[[dict], Any]) -> Any:
        """Apply fn to a copy. Commit it only if fn succeeds, so a rejected change leaves no trace."""
        with self._lock:
            draft = copy.deepcopy(self.state)
            result = fn(draft)
            self.state = draft
            self.version += 1
            self._save()
            return result

    def replace(self, state: dict) -> None:
        state = validate_state(copy.deepcopy(state))
        with self._lock:
            self.state = state
            self.version += 1
            self._save()
