import os, uuid, shutil, subprocess, zipfile
from pathlib import Path
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

APP_DIR = Path(__file__).parent.resolve()
WORK_DIR = APP_DIR / "work"
UPLOAD_DIR = WORK_DIR / "uploads"
OUTPUT_DIR = WORK_DIR / "outputs"
for d in (UPLOAD_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-for-production")
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "500"))
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}

def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or "Processing failed")[-1800:])
    return result.stdout

def duration_seconds(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return float(out.strip())

def make_clips(source, outdir, clip_length):
    duration = duration_seconds(source)
    if duration <= 0:
        raise RuntimeError("Could not read video duration.")
    count = 0
    start = 0.0
    while start < duration and count < 60:
        length = min(clip_length, duration - start)
        target = outdir / f"short_{count+1:02d}.mp4"
        # Simple, reliable cut; crop/AI reframing can be added in a later version.
        run(["ffmpeg", "-y", "-ss", str(start), "-i", str(source), "-t", str(length),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target)])
        count += 1
        start += clip_length
    return count

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_id = uuid.uuid4().hex[:10]
        jobdir = OUTPUT_DIR / job_id
        jobdir.mkdir(parents=True, exist_ok=True)
        source = None
        try:
            clip_length = int(request.form.get("clip_length", "30"))
            if clip_length not in (15, 30, 45, 60):
                clip_length = 30
            upload = request.files.get("video")
            youtube_url = (request.form.get("youtube_url") or "").strip()
            if upload and upload.filename:
                ext = Path(secure_filename(upload.filename)).suffix.lower()
                if ext not in ALLOWED:
                    raise RuntimeError("Please upload MP4, MOV, MKV, WEBM, or M4V video.")
                source = UPLOAD_DIR / f"{job_id}{ext}"
                upload.save(source)
            elif youtube_url:
                if not (youtube_url.startswith("https://www.youtube.com/") or
                        youtube_url.startswith("https://youtube.com/") or
                        youtube_url.startswith("https://youtu.be/") or
                        youtube_url.startswith("https://m.youtube.com/")):
                    raise RuntimeError("Please enter a valid HTTPS YouTube URL.")
                source = UPLOAD_DIR / f"{job_id}.source"
                run(["yt-dlp", "--no-playlist", "-f", "bv*[height<=1080]+ba/b[height<=1080]",
                     "--merge-output-format", "mp4", "-o", str(source) + ".%(ext)s", youtube_url])
                candidates = list(UPLOAD_DIR.glob(source.name + ".*"))
                if not candidates:
                    raise RuntimeError("YouTube download did not produce a file. The video may be restricted or unsupported.")
                source = candidates[0]
            else:
                raise RuntimeError("Upload a video or paste a YouTube link.")
            count = make_clips(source, jobdir, clip_length)
            zip_path = OUTPUT_DIR / f"{job_id}_shorts.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                for clip in sorted(jobdir.glob("*.mp4")):
                    z.write(clip, clip.name)
            return render_template("index.html", result_url=url_for("download", job_id=job_id),
                                   clip_count=count, clip_length=clip_length, error=None)
        except Exception as e:
            shutil.rmtree(jobdir, ignore_errors=True)
            return render_template("index.html", error=str(e), result_url=None, clip_count=None, clip_length=30)
        finally:
            if source and source.exists():
                try: source.unlink()
                except OSError: pass
            if source:
                for f in UPLOAD_DIR.glob(source.name + ".*"):
                    try: f.unlink()
                    except OSError: pass
    return render_template("index.html", error=None, result_url=None, clip_count=None, clip_length=30)

@app.route("/download/<job_id>")
def download(job_id):
    if not job_id.isalnum() or len(job_id) != 10:
        return "Invalid download ID", 400
    path = OUTPUT_DIR / f"{job_id}_shorts.zip"
    if not path.exists():
        return "Download expired or unavailable. Process the video again.", 404
    return send_file(path, as_attachment=True, download_name="my_shorts.zip")

@app.errorhandler(413)
def too_large(_):
    return render_template("index.html", error=f"File too large. Limit is {MAX_UPLOAD_MB} MB.", result_url=None, clip_count=None, clip_length=30), 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
