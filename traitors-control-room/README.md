# Traitors Control Room

A shared host console for running a Traitors party game: deal secret roles, pick missions, split people into teams, track the prize pot, and copy ready-made WhatsApp messages.

Everyone who opens the app and enters the passcode works on the **same game**, so a host on a laptop and a co-host on a phone stay in step. Changes show up on the other screen within a few seconds.

## What it does

- **Players**: paste names, set the number of Traitors, deal roles at random. A "Hide roles on this screen" switch is per device.
- **Games**: an editable catalog of missions, each with minutes, pot at stake, team or whole-room play, and how it is scored.
- **Rounds**: murder reveal, mission, banishment. Teams are assigned at random with Traitors spread across them. Scores are a share of the stake, banked into the pot.
- **Pot**: running total, ledger, bonuses and penalties, and the prize split (Traitors win if any survive).
- **Messages**: role messages, the Traitors' chat welcome, round briefings, and private murder and shield notices. Each box has a copy button.

## Run it on your computer

```bash
cd traitors-control-room
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the address it prints. To protect it with a passcode, set one first:

```bash
HOST_PASSCODE="choose-something" streamlit run streamlit_app.py
```

## Host it for free on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Choose **Create app**, then pick this repository and the branch you pushed this folder to.
3. Set **Main file path** to `traitors-control-room/streamlit_app.py`.
4. Open **Advanced settings**, then **Secrets**, and add:
   ```toml
   HOST_PASSCODE = "choose-something"
   ```
5. Deploy. Send the app link and the passcode to your co-host only.

Without a passcode, anyone who has the link can see every role. Set one.

## Good to know

- The game is held on the server and saved to `data/game.json`. Free apps go to sleep when nobody visits for a while, and a restart or redeploy can wipe the file. **Use Download backup in the sidebar** before you leave the app idle, and **Restore a backup** to bring it back.
- Hide roles only changes your own screen. Role messages and the Traitors' chat stay hidden until you tick the box on the Messages tab.
- Two people changing the same field at the same moment: the last change wins.

## Tests

```bash
python -m unittest discover -s tests -p "test_core.py"   # game logic, no Streamlit needed
python -m unittest discover -s tests -p "test_app.py"    # runs the real app with Streamlit's test harness
```

The game rules live in `traitors_core.py` (standard library only). `streamlit_app.py` is the screen on top of it.
