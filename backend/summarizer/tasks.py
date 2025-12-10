from celery import shared_task
from .models import Job
import yt_dlp
import os
from openai import OpenAI
import requests
import json
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_video(job_id: int):

    job = Job.objects.get(id = job_id)

    job.status = "DOWNLOADING"
    job.save()
    audio_file_path = download_audio(job.url)

    job.status = "TRANSCRIBING"
    job.save()
    transcript = transcribe_audio(audio_file_path)

    job.status = "ANALYZING"
    job.save()
    analysis = llm_analysis(transcript)

    raw_content = analysis.choices[0].message.content
    data = json.loads(raw_content)
    job.transcript = transcript
    job.summary = data.get('summary')
    job.chapters = data.get("chapters")
    job.highlights = data.get("highlights")
    job.status = "COMPLETED"
    job.save()



@shared_task
def download_audio(url: str):

    """
    Downloads audio and returns the absolute path to the .mp3 file.
    """
    # Good practice: Use absolute paths for Celery tasks to avoid CWD confusion
    output_dir = 'audio' 
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. extract_info(download=True) downloads the video and returns the metadata dict
            info = ydl.extract_info(url, download=True)
            
            # 2. prepare_filename generates the path based on the metadata and outtmpl
            # Note: This usually returns the original extension (e.g., .webm or .m4a)
            temp_path = ydl.prepare_filename(info)
            
            # 3. Update extension to match the postprocessor (mp3)
            # Since FFmpegExtractAudio converts it, the final file on disk is .mp3
            base, _ = os.path.splitext(temp_path)
            final_path = f"{base}.mp3"
            
            # Return absolute path for reliability in other tasks
            return os.path.abspath(final_path)

    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        raise e

@shared_task
def transcribe_audio(path: str):
    transcription = process_chunk(path)

    if os.path.exists(path):
        os.remove(path)
    
    return transcription

@shared_task
def process_chunk(path: str):

    whisper_url = os.environ.get("WHISPER_API_URL", "")

    # Add http:// if no scheme provided
    if whisper_url and not whisper_url.startswith(("http://", "https://")):
        whisper_url = f"http://{whisper_url}"

    # Use Tailscale SOCKS proxy if available (for reaching local network)
    tailscale_proxy = os.environ.get("TAILSCALE_PROXY")
    proxies = {"http": tailscale_proxy, "https": tailscale_proxy} if tailscale_proxy else None

    # Local Whisper container (onerahmet/openai-whisper-asr-webservice)
    # Endpoint is /asr, file goes in multipart form data
    with open(path, "rb") as audio_file:
        response = requests.post(
            f"{whisper_url}/asr",
            files={"audio_file": audio_file},
            params={"output": "json", "task": "transcribe"},
            proxies=proxies,
        )
        response.raise_for_status()
        transcription = response.json()

    if os.path.exists(path):
        os.remove(path)
    return transcription

@shared_task
def llm_analysis(transcript: json):
    ANALYSIS_PROMPT = f"""
    Analyze this video transcript and provide:

    1. A 2-3 paragraph summary of the main content
    2. Chapter breakdown with timestamps (use the [HH:MM:SS] markers in transcript)
    3. 3-5 highlight moments worth watching (use the [HH:MM:SS] markers in transcript)

    Respond in JSON format:
    {{
    "summary": "...",
    "chapters": [
        {{"timestamp": <seconds>, "title": "...", "summary": "..."}}
    ],
    "highlights": [
        {{"timestamp": <seconds>, "description": "..."}}
    ]
    }}

    TRANSCRIPT:
    {transcript}
    """
    
    client = OpenAI()
    
    # CHANGE: Use standard Chat Completions
    response = client.chat.completions.create(
        model="gpt-5-nano", # Keep your preferred model
        messages=[
            {"role": "user", "content": ANALYSIS_PROMPT}
        ],
        response_format={"type": "json_object"} # Force valid JSON
    )
    
    return response
