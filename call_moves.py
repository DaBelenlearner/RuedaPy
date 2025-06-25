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
    return (60 / bpm) * beats


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


def prompt_difficulty():
    difficulty_type = input("Select difficulty (beginner/intermediate/advanced): ").strip().lower()
    try:
        level = int(input("Enter difficulty sub‑level (e.g. 1 or 2): ").strip())
    except ValueError:
        print("Invalid level. Defaulting to 1.")
        level = 1
    below = input("Include all easier levels too? (y/n): ").strip().lower() == "y"
    return difficulty_type, level, below


def start_audio_playback(filepath):
    full_path = os.path.join(MUSIC_DIR, filepath)
    audio = AudioSegment.from_file(full_path)
    play(audio)


def start_calling_moves(bpm, song_filename, first_beat_time, num_moves=20):
    rueda = RuedaMoves('moves.json')
    difficulty_type, level, below = prompt_difficulty()
    rueda.set_difficulty(difficulty_type, level, anything_below=below)

    engine = pyttsx3.init()
    engine.setProperty('rate', 150)

    input("\n🎤 Press Enter to start music and moves...")

    # Start music playback
    threading.Thread(target=start_audio_playback, args=(song_filename,), daemon=True).start()

    # Wait until beat 1 + 8 counts
    total_wait = first_beat_time + beats_to_seconds(8, bpm)
    print(f"⏳ Waiting {total_wait:.2f} seconds before first call to align with beat 1...")
    time.sleep(total_wait)

    # Determine starting context
    start_position = random.choice(["open_position", "closed_position"])
    if start_position == "open_position":
        print("🎬 Starting position: open — simulating 'Guapea'")
        rueda.previous_move = "guapea"
        first_move = {
            "called_name": "Guapea",
            "precondition": "open_position",
            "postcondition": "open_position",
            "beat_count": 8,
        }
    else:
        print("🎬 Starting position: closed — starting with 'Pa'l Medio'")
        rueda.current_move = "pal_medio"
        first_move = rueda.get_current_move_data()
        if not first_move:
            print("❌ Could not retrieve 'Pa'l Medio'. Check JSON or difficulty.")
            return

    # Call first move immediately
    print(f"\nCALL: {first_move['called_name']}")
    engine.say(first_move["called_name"])
    engine.runAndWait()

    # Wait (beat_count - 4) beats before next call
    wait_time = beats_to_seconds(first_move.get("beat_count", 8) - 4, bpm)
    num_moves -= 1

    # Continue calling loop
    while num_moves > 0:
        print(f"⏱️  Waiting {wait_time:.2f}s before next call")
        time.sleep(wait_time)
        
        move = rueda.choose_next_move()
        if not move:
            print("No valid move found. Ending.")
            break

        beat_count = move.get("beat_count", 8)
        wait_time = beats_to_seconds(beat_count - 4, bpm)

        print(f"\n➡️  Next move: {move['called_name']}")
        print(f"    Beat count: {beat_count}")

        print(f"CALL: {move['called_name']}")
        engine.say(move["called_name"])
        engine.runAndWait()

        num_moves -= 1


if __name__ == "__main__":
    song_filename, bpm, first_beat = select_music_and_get_bpm()
    print(f"\n✅ Detected BPM: {bpm}, first beat at {first_beat:.2f}s")
    start_calling_moves(bpm, song_filename, first_beat)
