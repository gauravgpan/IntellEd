# IntellEd — ThinkTurf Workflow Docs

Internal docs site comparing three possible business workflows for
ThinkTurf's content-authoring and assessment approach: platform-based
chess tutorial, tutor-based feedback, and a hybrid of the two.

## First-time setup

1. Create an **empty** repo at `github.com/gauravgpan/IntellEd` (public,
   so free GitHub Pages works — use GitHub Pro/Enterprise if it needs to
   stay private).
2. Push this folder's contents to the `main` branch:
   ```bash
   git init
   git add .
   git commit -m "Initial IntellEd docs site"
   git branch -M main
   git remote add origin https://github.com/gauravgpan/IntellEd.git
   git push -u origin main
   ```
3. In the repo: **Settings → Pages → Source → GitHub Actions**. Select it once.
4. Push (step 2) triggers `.github/workflows/deploy.yml`, which builds and
   publishes automatically. No local `npm install` needed.
5. Site will be live at: **https://gauravgpan.github.io/IntellEd/**

## Local development (optional)

```bash
npm install
npm start        # live-reload dev server
npm run build     # static build, output in ./build
```

## Structure

- `docs/intro.md` — context and the three-option overview
- `docs/workflows/*.md` — one Mermaid diagram per option
- `docs/comparison.md` — pros/cons/effort table
- Edit any `.md` file and re-push to update the live site.
