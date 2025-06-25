import os
import json
import subprocess
import tempfile
import librosa
from moviepy.editor import AudioFileClip
from pytube import YouTube

MUSIC_DIR = "music"
CACHE_FILE = os.path.join(MUSIC_DIR, "bpm_cache.json")

def download_audio_from_youtube(youtube_url, output_path):
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(only_audio=True).first()
    temp_file = stream.download(output_path=output_path)
    base, _ = os.path.splitext(temp_file)
    mp3_file = base + ".mp3"
    subprocess.run(["ffmpeg", "-y", "-i", temp_file, mp3_file],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(temp_file)
    return mp3_file

def extract_audio_from_video(video_path, output_path):
    audio_clip = AudioFileClip(video_path)
    audio_file = os.path.join(output_path, "extracted_audio.wav")
    audio_clip.write_audiofile(audio_file, logger=None)
    return audio_file

def detect_bpm(audio_path):
    y, sr = librosa.load(audio_path)
    tempo_array, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_array)

    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    first_beat_time = beat_times[0] if len(beat_times) > 0 else 0.0

    return round(tempo), first_beat_time

def get_cached_bpm_and_first_beat(source_name):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
            entry = cache.get(source_name)
            if isinstance(entry, dict) and "bpm" in entry and "first_beat" in entry:
                return entry["bpm"], entry["first_beat"]
    return None

def save_bpm_and_first_beat(source_name, bpm, first_beat):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
    else:
        cache = {}

    cache[source_name] = {
        "bpm": bpm,
        "first_beat": first_beat
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_bpm_from_input(source_name):
    cached = get_cached_bpm_and_first_beat(source_name)
    if cached:
        print(f"📦 Cached BPM found: {cached[0]} (first beat at {cached[1]:.2f}s)")
        return cached

    full_path = os.path.join(MUSIC_DIR, source_name)

    with tempfile.TemporaryDirectory() as tmpdir:
        if source_name.startswith("http"):
            print("🎵 Downloading from YouTube...")
            audio_file = download_audio_from_youtube(source_name, tmpdir)
        elif source_name.endswith((".mp4", ".mov", ".avi")):
            print("🎬 Extracting audio from video...")
            audio_file = extract_audio_from_video(full_path, tmpdir)
        elif source_name.endswith((".mp3", ".wav")):
            audio_file = full_path
        else:
            raise ValueError("Unsupported file type or URL")

        print("🎧 Detecting BPM and downbeat...")
        bpm, first_beat = detect_bpm(audio_file)
        save_bpm_and_first_beat(source_name, bpm, first_beat)
        return bpm, first_beat
