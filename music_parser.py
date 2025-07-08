import os
import json
import subprocess
import tempfile
from moviepy.editor import AudioFileClip
from pytube import YouTube

from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor
import numpy as np

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
    # Use madmom to detect beat activations
    beat_proc = RNNBeatProcessor()(audio_path)
    bpm_proc = DBNBeatTrackingProcessor(fps=100)
    beat_times = bpm_proc(beat_proc)

    if len(beat_times) < 2:
        raise ValueError("Could not detect enough beats for BPM estimation.")

    # Calculate BPM from median beat interval
    intervals = np.diff(beat_times)
    avg_interval = np.median(intervals)
    bpm = 60.0 / avg_interval

    first_beat_time = beat_times[0]
    return round(bpm), round(first_beat_time, 2)


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

        print("🎧 Detecting BPM and downbeat using madmom...")
        bpm, first_beat = detect_bpm(audio_file)
        bpm *= 2  # Adjust BPM for double time
        save_bpm_and_first_beat(source_name, bpm, first_beat)
        return bpm, first_beat


if __name__ == "__main__":
    print(f"\n🔍 Looking for files in: {MUSIC_DIR}/")
    local_files = sorted([
        f for f in os.listdir(MUSIC_DIR)
        if f.endswith((".mp3", ".wav", ".mp4", ".mov", ".avi"))
    ])

    print("\n🎶 Available music files:")
    for i, fname in enumerate(local_files, 1):
        print(f"  {i}. {fname}")
    print("  0. Enter YouTube URL")

    choice = input("\nEnter number to select a file, or 0 to paste a YouTube URL: ").strip()

    if choice == "0":
        source = input("Paste YouTube URL: ").strip()
    else:
        try:
            index = int(choice) - 1
            if 0 <= index < len(local_files):
                source = local_files[index]
            else:
                raise ValueError
        except ValueError:
            print("❌ Invalid selection.")
            exit()

    # try:
    bpm, first_beat = get_bpm_from_input(source)
    print(f"\n✅ BPM: {bpm}, first beat at {first_beat:.2f}s")
    os.system(f'python call_moves.py {bpm}')
    # except Exception as e:
    #     print(f"❌ Error: {e}")