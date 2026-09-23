# DocReader

DocReader turns documents into AI-narrated MP3 audio.

## Features

- Upload PDF, DOCX, TXT/Markdown/CSV/JSON/YAML, PNG/JPG/WEBP
- Extract and edit document text
- Image text extraction using an OpenAI vision model
- Multiple TTS voices and narration styles
- Browser audio player and MP3 download
- Responsive GitHub Pages frontend
- FastAPI backend ready for Google Cloud Run
- OpenAI API key stays server-side

## Architecture

Browser / GitHub Pages → FastAPI on Cloud Run → OpenAI API

## Deploy the backend

From the repository root:

```bash
cd backend
gcloud run deploy docreader-api --source . --region us-south1 --allow-unauthenticated --set-env-vars OPENAI_API_KEY=YOUR_KEY
```

For production, store the API key in Google Secret Manager rather than committing it or placing it in frontend code.

After deployment, copy the Cloud Run service URL. Open DocReader, expand **Backend settings**, paste the URL, and save it.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=YOUR_KEY
uvicorn main:app --reload --port 8080
```

Then set the frontend backend URL to `http://localhost:8080`.

## GitHub Pages

In repository **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`.

## Security

Never commit an OpenAI API key. The frontend intentionally contains no API secret.
