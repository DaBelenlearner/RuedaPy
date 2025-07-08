import json
import os

def load_moves(filepath):
    if not os.path.exists(filepath):
        print("File not found. Starting with empty moves.")
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_moves(filepath, moves):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(moves, f, indent=2)

def prompt_user_choice(prompt, options):
    print(f"{prompt}:")
    for idx, option in enumerate(options, 1):
        print(f"{idx}. {option}")
    choice = input("Enter the number(s) separated by commas (e.g. 1,3): ").strip()
    try:
        selected = [options[int(i)-1] for i in choice.split(",") if i.strip().isdigit()]
        return selected
    except (ValueError, IndexError):
        print("Invalid selection.")
        return []

def add_new_move(moves):
    print("\n--- Add a New Rueda Move ---")

    move_key = input("Internal move key (e.g. 'setenta_variation'): ").strip().lower().replace(" ", "_")
    if move_key in moves:
        print("Move already exists.")
        return

    called_name = input("Name to call the move (e.g. 'Setenta Variation'): ").strip()
    description = input("Short description of the move: ").strip()

    difficulty_type = prompt_user_choice("Select difficulty type", ["beginner", "intermediate", "advanced"])
    if not difficulty_type:
        print("At least one difficulty type is required.")
        return
    try:
        difficulty_level = int(input("Enter sub-level (e.g. 1, 2): ").strip())
    except ValueError:
        print("Invalid level.")
        return

    change_partner = int(input("How many partners do you switch? (can be negative): ").strip())
    precondition = input("Enter precondition (e.g. open_position, closed_position): ").strip()
    postcondition = input("Enter postcondition (e.g. closed_position, open_position): ").strip()
    beat_count = int(input("How many beats does this move last? ").strip())

    requires = prompt_user_choice("Does this move require any specific preceding moves?", list(moves.keys()))
    must_be_followed_by = prompt_user_choice("Must this move be followed by any specific move(s)?", list(moves.keys()))

    # Construct the move entry
    new_move = {
        "called_name": called_name,
        "description": description,
        "level": [difficulty_type[0], difficulty_level],
        "change_partner": change_partner,
        "precondition": precondition,
        "postcondition": postcondition,
        "beat_count": beat_count
    }
    if requires:
        new_move["requires"] = requires
    if must_be_followed_by:
        new_move["must_be_followed_by"] = must_be_followed_by

    moves[move_key] = new_move
    print(f"✅ Move '{called_name}' added as key '{move_key}'.")

# ----------------- Usage --------------------

if __name__ == "__main__":
    while True:
        cont = input("Do you want to add a new move? (y/n): ").strip().lower()
        if cont != 'y':
            break
        filepath = "moves.json"
        moves = load_moves(filepath)
        add_new_move(moves)
        save_moves(filepath, moves)
        print("✅ Moves file updated.")
