from celery import shared_task
from .models import Job
import yt_dlp
import os
from openai import OpenAI
import math
import subprocess
import json

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
        print(f"Error downloading audio: {e}")
        # Re-raise the exception so Celery marks the task as FAILED
        raise e

@shared_task
def transcribe_audio(path: tuple):
    file_paths = split_audio_if_needed(path, 25)
    results = []
    for index, (chunk_path, offset) in enumerate(file_paths):
        response = process_chunk(chunk_path)
        results.append(response.text)

    if os.path.exists(path):
        os.remove(path)
    
    transcription = " ".join(results)
    return transcription

@shared_task
def process_chunk(path: str):
    client = OpenAI()
    audio_file = open(path, "rb")
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe", 
        file=audio_file,
    )
    if os.path.exists(path):
        os.remove(path)
    return transcription

@shared_task
def get_audio_duration(file_path):
    """Get duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'json', 
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

@shared_task
def split_audio_if_needed(file_path: str, max_size_mb: int = 25):
    """
    Splits audio using raw FFmpeg (works on Python 3.13 without pydub).
    Returns a list of tuples: [(path, start_offset_seconds), ...]
    """
    file_size = os.path.getsize(file_path)
    limit_bytes = max_size_mb * 1024 * 1024
    
    # If small enough, return original with 0 offset
    if file_size <= limit_bytes:
        return [(file_path, 0.0)]

    print(f"File size {file_size} exceeds limit {limit_bytes}. Splitting...")

    # 1. Get total duration in seconds
    try:
        total_duration = get_audio_duration(file_path)
    except Exception as e:
        print(f"Error getting duration: {e}")
        raise e

    # 2. Calculate chunk length
    # Target 24MB to be safe
    safe_limit_bytes = (max_size_mb - 1) * 1024 * 1024
    chunk_length_seconds = math.floor((safe_limit_bytes / file_size) * total_duration)

    chunks_data = []
    base_name, ext = os.path.splitext(file_path)
    
    current_time = 0.0
    part_num = 1

    while current_time < total_duration:
        chunk_filename = f"{base_name}_part{part_num}{ext}"
        
        # FFmpeg command to slice: 
        # -ss = start time
        # -t = duration
        # -c copy = fast copy without re-encoding quality loss
        cmd = [
            'ffmpeg',
            '-y', # Overwrite if exists
            '-i', file_path,
            '-ss', str(current_time),
            '-t', str(chunk_length_seconds),
            '-c', 'copy', # FAST: Copies stream, no re-encoding
            chunk_filename
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        chunks_data.append((chunk_filename, current_time))
        
        current_time += chunk_length_seconds
        part_num += 1

    # Optional: Delete original
    # os.remove(file_path)

    return chunks_data

@shared_task
def llm_analysis(transcript: str):
    ANALYSIS_PROMPT = f"""
    Analyze this video transcript and provide:
    1. A 2-3 paragraph summary of the main content

    Respond in valid JSON format:
    {{
    "summary": "..."
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
