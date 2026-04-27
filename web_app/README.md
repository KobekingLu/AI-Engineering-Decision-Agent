# Web App MVP

This folder contains the local Streamlit demo UI for `AI Engineering Decision Agent`.

The web app is intentionally small.  
Its role is to make the current `decision_agent` flow easy to demo, not to introduce a second decision engine.

## What The App Does

The app accepts one case at a time and sends that case into the existing decision flow.

It supports:

- one freeform text box for manual case input
- multi-file upload for one case bundle
- single-case analysis
- single-case HTML report generation

## Supported Inputs

You can use:

- pasted issue text
- `.json`
- `.txt`
- `.pdf`
- `.html` / `.htm`
- common image files such as `.png`, `.jpg`, `.jpeg`, and `.webp`

For a realistic demo, one case bundle can include several files at once, for example:

- issue PDF
- screenshot images
- HTML export
- text log
- bundle notes

## OCR

The MVP can use local OCR for scanned PDF and image inputs when OCR is available in the environment.

OCR is helpful for real-world cases, but not always perfect.  
The most reliable inputs are still:

- clean text
- normalized JSON
- HTML with readable text
- PDF or image plus a short note or helper text file

## Decision Path

The web app does **not** implement separate judgment logic.

It reuses the current `decision_agent` output for:

- issue type
- risk level
- missing information
- recommended action
- decision summary
- reasoning trace

## Start

From the repo root:

```powershell
python web_app/run_app.py
```

## Typical Demo Flow

1. Paste one issue summary or upload one case bundle
2. Let the app normalize available evidence
3. Run the existing decision flow
4. Review the single-case decision result
5. Open the generated HTML report

## Output Location

The app writes local artifacts under:

- `output/web_app/input/`
- `output/web_app/json/`
- `output/web_app/html/`
- `output/web_app/uploads/`

## Design Intent

This MVP is designed for:

- local demo use
- quick iteration
- easy explanation during review

It prioritizes clarity and maintainability over complex architecture.
