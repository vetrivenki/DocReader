import base64
import io
import os
from pathlib import Path

from docx import Document
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

app = FastAPI(title="DocReader API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
client = OpenAI()

MAX_FILE_BYTES = 20 * 1024 * 1024
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

class SpeechRequest(BaseModel):
    text: str
    voice: str = "marin"
    instructions: str = "Speak clearly, naturally, and professionally at a comfortable learning pace."

@app.get("/")
def root():
    return {"service": "DocReader API", "status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

def pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()

def docx_text(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()

def image_text(data: bytes, mime: str) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    response = client.responses.create(
        model=os.getenv("VISION_MODEL", "gpt-4.1-mini"),
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Extract all readable text from this image. Preserve headings and useful line breaks. Return only the extracted text."},
                {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"},
            ],
        }],
    )
    return response.output_text.strip()

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, "File is larger than 20 MB.")

    suffix = Path(file.filename or "").suffix.lower()
    try:
        if suffix == ".pdf":
            text = pdf_text(data)
        elif suffix == ".docx":
            text = docx_text(data)
        elif suffix in TEXT_EXTENSIONS:
            text = data.decode("utf-8", errors="replace").strip()
        elif suffix in IMAGE_EXTENSIONS:
            text = image_text(data, file.content_type or "image/png")
        else:
            raise HTTPException(415, "Supported: PDF, DOCX, TXT/MD/CSV/JSON/YAML, PNG/JPG/WEBP.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Could not read document: {exc}")

    if not text:
        raise HTTPException(422, "No readable text found. Scanned PDFs may require OCR.")
    return {"filename": file.filename, "characters": len(text), "text": text}

def chunks(text: str, size: int = 10000):
    text = text.strip()
    while text:
        if len(text) <= size:
            yield text
            break
        cut = text.rfind("\n", 0, size)
        if cut < size // 2:
            cut = text.rfind(". ", 0, size)
        if cut < size // 2:
            cut = size
        yield text[:cut].strip()
        text = text[cut:].strip()

@app.post("/speech")
def speech(req: SpeechRequest):
    if not req.text.strip():
        raise HTTPException(400, "Text is required.")
    if len(req.text) > 120000:
        raise HTTPException(413, "Narration is limited to 120,000 characters per request.")

    audio = bytearray()
    try:
        for part in chunks(req.text):
            result = client.audio.speech.create(
                model=os.getenv("TTS_MODEL", "gpt-4o-mini-tts"),
                voice=req.voice,
                input=part,
                instructions=req.instructions,
                response_format="mp3",
            )
            audio.extend(result.content)
    except Exception as exc:
        raise HTTPException(502, f"Speech generation failed: {exc}")

    return Response(
        content=bytes(audio),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="docreader.mp3"'},
    )
