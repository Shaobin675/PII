# main.py
import os
import tempfile
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from detectors import run_regex_detectors, deterministic_pseudonymize, redact_spans
from utils import extract_text_and_images_from_pdf, extract_text_from_image_file, ocr_image
import spacy

# Load spaCy model (small). For better results replace with a larger model.
nlp = spacy.load("en_core_web_sm")

app = FastAPI(title="PII Scanner MVP")

# Secret key for pseudonymization (in prod store this in KMS/Vault)
SECRET_KEY = os.environ.get("PII_SECRET", "change-me-secret")


def run_spacy_ner(text: str):
    doc = nlp(text)
    results = []
    for ent in doc.ents:
        # Map spaCy labels to a general category if desired
        results.append({
            "type": ent.label_,
            "span": (ent.start_char, ent.end_char),
            "text": ent.text,
            "confidence": 0.85,
            "source": "spacy"
        })
    return results

def merge_findings(all_findings):
    """
    Deduplicate and merge overlapping findings (simple strategy).
    We prefer regex findings (higher precision) over NER if overlap occurs.
    """
    # Sort findings by start index
    all_findings = sorted(all_findings, key=lambda f: (f["span"][0], -f["span"][1]))
    merged = []
    for f in all_findings:
        s,e = f["span"]
        # check overlap with last
        if merged and (s < merged[-1]["span"][1]):
            # overlapping: keep the higher confidence one
            if f.get("confidence",0) > merged[-1].get("confidence",0):
                merged[-1] = f
        else:
            merged.append(f)
    return merged

@app.post("/scan")
async def scan_file(file: UploadFile = File(...), redact: bool = Form(False)):
    """
    Upload a PDF or an image. Returns JSON with findings and a redacted version link if requested.
    """
    filename = file.filename.lower()
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    all_findings = []

    # If PDF
    if filename.endswith(".pdf"):
        text, images = extract_text_and_images_from_pdf(tmp_path)
        # regex on pdf text
        all_findings.extend(run_regex_detectors(text))
        # NER on extracted text
        all_findings.extend(run_spacy_ner(text))
        # OCR embedded images
        for img in images:
            ocr_text = ocr_image(img)
            all_findings.extend(run_regex_detectors(ocr_text))
            all_findings.extend(run_spacy_ner(ocr_text))

    # If image
    elif filename.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
        ocr_text = extract_text_from_image_file(tmp_path)
        all_findings.extend(run_regex_detectors(ocr_text))
        all_findings.extend(run_spacy_ner(ocr_text))
        text = ocr_text
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    merged = merge_findings(all_findings)

    # Prepare redaction if requested
    redacted_path = None
    if redact:
        # Build mask spans for redaction
        spans = [f["span"] for f in merged]
        # remove overlapping by sorting and merging simple
        spans_sorted = sorted(spans, key=lambda s: (s[0], -s[1]))
        flattened = []
        cur_s, cur_e = None, None
        for s,e in spans_sorted:
            if cur_s is None:
                cur_s, cur_e = s,e
            elif s <= cur_e:
                cur_e = max(cur_e, e)
            else:
                flattened.append((cur_s, cur_e))
                cur_s, cur_e = s,e
        if cur_s is not None:
            flattened.append((cur_s, cur_e))

        redacted_text = redact_spans(text, flattened, mask="[REDACTED]")
        # Save redacted text to a file and return path
        redacted_path = tmp_path + ".redacted.txt"
        with open(redacted_path, "w", encoding="utf-8") as f:
            f.write(redacted_text)

    response = {
        "filename": filename,
        "num_findings": len(merged),
        "findings": merged,
    }

    if redacted_path:
        # return filepath for download (in prod, stream or store in secure storage)
        response["redacted_file"] = redacted_path

    return JSONResponse(response)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
