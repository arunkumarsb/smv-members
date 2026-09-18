import io
import json
import os

from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, ImageDraw

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image as RLImage, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "members.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
THUMB_DIR = os.path.join(UPLOAD_DIR, "thumbs")
PLACEHOLDER_NAME = "placeholder.jpg"
STAMP_SIZE = (150, 180)  # width, height in px

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}

app = Flask(__name__)
app.secret_key = "member-roster-dev-key"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_members():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_members(members):
    with open(DATA_FILE, "w") as f:
        json.dump(members, f, indent=2)


def ensure_placeholder():
    path = os.path.join(THUMB_DIR, PLACEHOLDER_NAME)
    if os.path.exists(path):
        return
    img = Image.new("RGB", STAMP_SIZE, color=(230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, STAMP_SIZE[0] - 1, STAMP_SIZE[1] - 1], outline=(180, 180, 180), width=2)
    text = "No\nPhoto"
    draw.multiline_text(
        (STAMP_SIZE[0] / 2, STAMP_SIZE[1] / 2),
        text,
        fill=(140, 140, 140),
        anchor="mm",
        align="center",
    )
    img.save(path, "JPEG", quality=85)


def make_stamp_thumb(source_path, dest_path):
    with Image.open(source_path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        fitted = ImageOps.fit(img, STAMP_SIZE, Image.LANCZOS)
        fitted.save(dest_path, "JPEG", quality=85)


def next_id(members):
    return (max((m["id"] for m in members), default=0)) + 1


@app.route("/")
def home():
    members = load_members()
    return render_template("index.html", member_count=len(members))


@app.route("/members")
def view_members():
    members = load_members()
    return render_template("view_members.html", members=members)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        designation = request.form.get("designation", "").strip()
        site_number = request.form.get("site_number", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not designation:
            errors.append("Designation is required.")
        if not site_number:
            errors.append("Site Number is required.")

        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename and not allowed_file(photo_file.filename):
            errors.append("Photo must be an image file (png, jpg, jpeg, gif, webp, bmp).")

        if errors:
            return render_template("add_member.html", errors=errors, form=request.form)

        members = load_members()
        member_id = next_id(members)

        photo_thumb_name = PLACEHOLDER_NAME
        if photo_file and photo_file.filename:
            ext = photo_file.filename.rsplit(".", 1)[1].lower()
            original_name = secure_filename(f"{member_id}.{ext}")
            original_path = os.path.join(UPLOAD_DIR, original_name)
            photo_file.save(original_path)

            thumb_name = f"{member_id}.jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_name)
            make_stamp_thumb(original_path, thumb_path)
            photo_thumb_name = thumb_name

        members.append({
            "id": member_id,
            "name": name,
            "designation": designation,
            "site_number": site_number,
            "photo": photo_thumb_name,
        })
        save_members(members)
        return redirect(url_for("view_members"))

    return render_template("add_member.html", errors=None, form={})


@app.route("/members/pdf")
def members_pdf():
    members = load_members()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="Members Roster")
    styles = getSampleStyleSheet()

    elements = [Paragraph("Members Roster", styles["Title"]), Spacer(1, 12)]

    table_data = [["Photo", "Name", "Designation", "Site Number"]]
    for m in members:
        thumb_path = os.path.join(THUMB_DIR, m.get("photo") or PLACEHOLDER_NAME)
        if not os.path.exists(thumb_path):
            thumb_path = os.path.join(THUMB_DIR, PLACEHOLDER_NAME)
        img = RLImage(thumb_path, width=1 * inch, height=1.2 * inch)
        table_data.append([img, m["name"], m["designation"], m["site_number"]])

    table = Table(table_data, colWidths=[1.2 * inch, 2 * inch, 2 * inch, 1.6 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="members.pdf",
    )


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)
    ensure_placeholder()
    app.run(debug=True, port=8080)
