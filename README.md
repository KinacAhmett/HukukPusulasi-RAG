# Bitirme Projesi

This repository shares only the `code/` folder (Jupyter notebooks and code) while keeping datasets, outputs, and secrets private.

## Setup
1. Install Python 3.11 and create a virtual environment (optional).
2. Install dependencies inside the notebook as prompted (the notebook installs PyMuPDF and python-dotenv).
3. Create a `.env` file at the project root with:
```
GEMINI_API_KEY=your_key_here
```

## Privacy & Repo Layout
- Only `code/` is tracked. Large data, outputs, and media are ignored via `.gitignore`.
- Never commit real API keys. Use `.env` (ignored) and keep `.env.example` as a template.

## Git Workflow (Quick Start)
Initialize the repository and push to a new private repo:
```
git init
git add .
git commit -m "Initial commit: share code only"
# Create a new PRIVATE repo on GitHub named bitirme-projesi (from the UI)
# Then set the remote and push
git branch -M main
git remote add origin https://github.com/<your-username>/bitirme-projesi.git
git push -u origin main
```

## Notes
- The notebook `code/dataset_create.ipynb` reads API key from `.env` using `python-dotenv`.
- Data sources under `hukukPusulasi-veri/` and generated CSVs under `outputs/` are excluded from version control.
