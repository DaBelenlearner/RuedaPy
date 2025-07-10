import os
import time
import json
import random
import threading
import pyttsx3
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio as play
from move_order import RuedaMoves
from music_parser import get_bpm_from_input, MUSIC_DIR

def beats_to_seconds(beats, bpm):
    return (beats / bpm) * 60

def select_music_and_get_bpm():
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
            source = local_files[index]
        except Exception:
            print("❌ Invalid selection.")
            exit()

    bpm, first_beat = get_bpm_from_input(source)
    return source, bpm, first_beat

def start_audio_playback(filepath):
    full_path = os.path.join(MUSIC_DIR, filepath)
    audio = AudioSegment.from_file(full_path)
    play(audio)

def schedule_calls(bpm, first_beat_time, rueda, method="astar"):
    song_duration_beats = rueda.song_duration_beats
    sequence = rueda.generate_sequence(song_duration_beats, method=method)

    if not sequence:
        print("❌ No valid sequence generated.")
        return []

    timeline = []
    current_time = first_beat_time + beats_to_seconds(8, bpm)

    for move_name in sequence:
        # Handle guapea or pa'l medio which may not be in moves.json
        if move_name == "guapea":
            beat_count = 8
            called_name = "Guapea"
        elif move_name == "pal_medio":
            beat_count = 8
            called_name = "Pa'l Medio"
        else:
            move = rueda.moves[move_name]
            beat_count = move.get("beat_count", 8)
            called_name = move["called_name"]

        timeline.append({
            "time": current_time,
            "called_name": called_name
        })
        current_time += beats_to_seconds(beat_count, bpm)

    unique_timeline = set([elem['called_name'] for elem in timeline])

    for elem in timeline:
        print(f"Scheduled {elem['called_name']} at {elem['time']:.2f}s")
    print(f"\nTotal moves scheduled: {len(unique_timeline)}")
    print(f"Unique moves scheduled: {unique_timeline}")
    return timeline

def run_event_based_calls(timeline, audio_filepath):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)

    threading.Thread(target=start_audio_playback, args=(audio_filepath,), daemon=True).start()
    start_time = time.time()

    for event in timeline:
        target_time = event["time"]
        while time.time() - start_time < target_time:
            time.sleep(0.000001)
        print(f"CALL: {event['called_name']} (at {target_time:.2f}s)")
        engine.say(event["called_name"])
        engine.runAndWait()

if __name__ == "__main__":
    song_filename, bpm, first_beat = select_music_and_get_bpm()
    print(f"\n✅ Detected BPM: {bpm}, first beat at {first_beat:.2f}s")

    rueda = RuedaMoves('moves.json')
    rueda.set_difficulty()

    audio = AudioSegment.from_file(os.path.join(MUSIC_DIR, song_filename))
    duration_seconds = (len(audio) / 1000) / 60
    rueda.song_duration_beats = int(duration_seconds * bpm // 8 * 8)

    method = str(input("Which algorithm do you want to use?\nastar\nn-gram\n")).strip()
    
    timeline = schedule_calls(bpm, first_beat, rueda, method)
    run_event_based_calls(timeline, song_filename)
