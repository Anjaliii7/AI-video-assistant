import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Local Windows dev machine only — on Streamlit Cloud (Linux) ffmpeg is
# installed via packages.txt and already on PATH, so this path won't exist
# there and we simply skip overriding anything.
FFMPEG_BIN = r"C:\Users\Hp\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
USE_LOCAL_FFMPEG = os.path.isdir(FFMPEG_BIN)

if USE_LOCAL_FFMPEG:
    AudioSegment.converter = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
    AudioSegment.ffprobe = os.path.join(FFMPEG_BIN, "ffprobe.exe")


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 10,
        "overwrites": True,
        # Try pretending to be the Android client — often avoids the
        # 403 Forbidden block that datacenter IPs (like cloud hosts) hit.
        "extractor_args": {"youtube": {"player_client": ["android"]}},
    }

    # Only force a specific ffmpeg path locally on Windows; on Linux
    # (Streamlit Cloud/Render) let yt-dlp find ffmpeg on PATH instead.
    if USE_LOCAL_FFMPEG:
        ydl_opts["ffmpeg_location"] = FFMPEG_BIN

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        base, _ = os.path.splitext(ydl.prepare_filename(info))
        filename = base + ".wav"
    return filename


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # 16khz
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks