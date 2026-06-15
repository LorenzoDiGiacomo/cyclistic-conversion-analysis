# Publishing guide — GitHub + Kaggle

Step-by-step to publish this project. The repository was prepared so that the
large data files stay out of Git and the notebooks run unchanged on both your
machine and Kaggle.

---

## 1 · GitHub

The repo already has a clean history (no large files) and a `.gitignore` that
excludes `data/`, `archive/`, and notebook/OS noise.

### Option A — with the GitHub CLI (`gh`)

```bash
# one-time: install + log in
brew install gh
gh auth login

# from the project root
gh repo create cyclistic-conversion-analysis --public --source=. --remote=origin \
  --description "Behavioural segmentation of Chicago bike-share data (Jun 2025 – May 2026)"
git push -u origin main
```

### Option B — from the GitHub website

1. Create a new **empty** repo at <https://github.com/new>
   (no README/.gitignore — this project already has them).
   Suggested name: `cyclistic-conversion-analysis`.
2. Then, from the project root:

```bash
git remote add origin https://github.com/LorenzoDiGiacomo/cyclistic-conversion-analysis.git
git push -u origin main
```

> First push uploads ~30 MB (notebooks + rendered reports + figures). The
> `data/` folder is **not** uploaded — that's by design.

### Sanity check before pushing

```bash
git ls-files | grep -E "data/(raw|processed|interim)" | grep -v .gitkeep   # must be empty
git count-objects -vH | grep size-pack                                     # should be tens of MB, not GB
```

---

## 2 · Kaggle

Two pieces: a **Dataset** (the cleaned data) and a **Notebook/kernel** (notebook 04
reading that dataset). Metadata templates are in `.kaggle_publish/`.

### One-time setup

```bash
pip install kaggle
# Get an API token: kaggle.com → account → "Create New API Token"
#   → downloads kaggle.json → place it at ~/.kaggle/kaggle.json, then:
chmod 600 ~/.kaggle/kaggle.json
```

### 2a · Upload the dataset

1. Edit `.kaggle_publish/dataset-metadata.json` and replace `YOUR_KAGGLE_USERNAME`
   with your real Kaggle username (in **both** json files).
2. Stage the data file(s) the dataset should contain and push:

```bash
mkdir -p /tmp/cyclistic_ds
cp data/processed/df_clean.csv /tmp/cyclistic_ds/
cp .kaggle_publish/dataset-metadata.json /tmp/cyclistic_ds/
kaggle datasets create -p /tmp/cyclistic_ds --dir-mode zip
```

> `df_clean.csv` is ~1 GB; the upload takes a while. To also run notebook 03 on
> Kaggle, add the `interim/` files and the two Chicago city CSVs to the same folder.

### 2b · Push the notebook

```bash
# from the project root — kernel-metadata.json points at notebooks/04...ipynb
kaggle kernels push -p .kaggle_publish
```

The notebook's **bootstrap cell** auto-detects Kaggle and symlinks the attached
dataset as `../data`, so the existing `../data/processed/df_clean.csv` path resolves
with no edits. If you attach more than one dataset, make the Cyclistic one first.

---

## 3 · Other platforms

- **nbviewer** — paste the GitHub URL of any notebook at <https://nbviewer.org> for a
  clean rendered view (good to link from a CV).
- **Portfolio site / LinkedIn** — link the rendered report
  `reports/cyclistic_conversion_strategy.html` (GitHub serves it raw; for a live
  page enable GitHub Pages on the repo and link `/reports/...`).

---

## Notes

- `.kaggle_publish/` is committed as a template; the real `~/.kaggle/kaggle.json`
  token is personal and must **never** be committed (it's covered by `.gitignore`).
- The old Git history (with the 2.3 GB of data baked in) was backed up outside the
  repo at `../Ciclistic_git_backup_DELETE_LATER/` — delete it once you've confirmed
  the new repo pushes cleanly.
