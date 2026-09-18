# SMV Members

A simple Flask app for managing a member roster: add members with a
photo, view them in a table, and export the full roster as a PDF with
each member's photo resized to a consistent stamp size.

## Features

- **Home** — landing page with member count.
- **View Members** — table of all members (photo, name, designation, site number).
- **Add Member** — form to add a member (Name, Designation, Site Number, photo upload).
- **Get PDF** — downloads a PDF listing all members in a table, photos resized to a fixed stamp size (150x180 px) so the layout stays clean.

## Setup

Requires Python 3.9+.

```bash
git clone https://github.com/arunkumarsb/smv-members.git
cd smv-members
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Run

```bash
venv/bin/python app.py
```

The app starts on `http://127.0.0.1:8080/`.

## Data storage

Member records are stored in `data/members.json` (created automatically
on first run). Uploaded photos are saved in `static/uploads/`, with
stamp-size thumbnails in `static/uploads/thumbs/` — these are generated
locally and are not committed to the repo.
