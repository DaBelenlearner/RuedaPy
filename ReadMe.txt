# 🌀 AI Rueda Caller

**An AI-powered system that dynamically generates and calls Rueda de Casino dance sequences in sync with music.**

## 🎯 Project Overview

Rueda de Casino is a Cuban social dance form where couples perform synchronized moves in a circle based on calls from a leader (caller or "cantante"). This project automates the caller's role using AI to generate move sequences, respect dance constraints, and call moves in perfect sync with the music.

The system includes:
- Dynamic move generation using **A\*** search and **unigram procedural generation**
- Constraint-based knowledge representation with JSON-formatted moves
- Real-time text-to-speech (TTS) calling synchronized to music BPM
- Modular design for extensibility and real-world use in dance practice or events

## 🧠 Key Features

- 🎵 **Music Analysis**: Detects beats per minute (BPM) and downbeats from audio.
- 🤖 **A\* Sequence Planner**: Generates optimal move sequences to fill a song, balancing novelty and flow.
- 🎲 **Unigram Generator**: Chooses valid moves with lowest usage frequency, simulating human creativity.
- 📢 **Synchronized TTS Calling**: Uses a beat-aligned event timeline to trigger vocal calls on rhythm.
- 🧩 **Constraint Logic**: Precondition, postcondition, and combo logic encoded in `moves.json`.

## 📂 Project Structure

ai-rueda-caller/
├── music_parser.py         # BPM and beat detection from audio
├── call_moves.py           # Timing and TTS calling logic
├── move_order.py           # A* and Unigram move sequence generation
├── moves.json              # Knowledge base of all moves and rules
├── visualize_rueda_graph.py# Graph visualizer of move connectivity
└── README.md               # This file

## 🧠 Algorithms

**A\* Search**
- Cost = elapsed beats + estimated remaining beats
- Penalties for repeated moves or awkward transitions
- Rewards for novelty, partner swaps, and smooth flow

**Unigram Generation**
- Tracks frequency of each move
- Chooses the least-used valid move to ensure variability
- No training data required (procedural generation)

## 🗃️ Sample JSON Move Format

{
  "called_name": "Dile Que No",
  "beat_count": 8,
  "precondition": "closed_position",
  "postcondition": "open_position",
  "level": ["beginner", 1],
  "change_partner": true
}

## 🙋‍♀️ Why This Matters

This project shows how AI planning, constraint modeling, and real-time systems can come together to enhance cultural and social activities. It’s a fusion of technology and dance that automates the caller’s role without losing the soul of Rueda de Casino.

## 🛠️ Future Improvements

- GUI for live interaction
- Spotify/streaming input
- LSTM/Transformer-based move prediction
- Custom voice and intonation control
- Feedback loop from dancers or sensors

---

💃 *Created with love for Salsa & AI.*
