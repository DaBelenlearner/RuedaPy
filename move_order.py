import json
import random

class RuedaMoves:
    def __init__(self, filepath):
        self.moves = self.load_moves(filepath)
        self.difficulty_types_allowed = None
        self.difficulty_levels_allowed = None
        self.previous_move = None
        self.current_move = "guapea"
        self.sequence_queue = []

    def load_moves(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_current_move_data(self):
        return self.moves.get(self.current_move)

    def set_difficulty(self, difficulty_type, difficulty_level, anything_below=False):
        if anything_below:
            if isinstance(difficulty_level, list):
                difficulty_level = max(difficulty_level)
            self.difficulty_levels_allowed = range(1, difficulty_level + 1)

            difficulty_types = {"beginner": 1, "intermediate": 2, "advanced": 3}
            if isinstance(difficulty_type, list):
                input_levels = [difficulty_types[d] for d in difficulty_type if d in difficulty_types]
            else:
                input_levels = [difficulty_types.get(difficulty_type)]

            if input_levels:
                highest_level = max(input_levels)
                self.difficulty_types_allowed = [d for d, level in difficulty_types.items() if level <= highest_level]
            else:
                print("No valid difficulty levels provided.")
        else:
            self.difficulty_levels_allowed = difficulty_level if isinstance(difficulty_level, list) else [difficulty_level]
            self.difficulty_types_allowed = difficulty_type if isinstance(difficulty_type, list) else [difficulty_type]

    def queue_sequence(self, sequence):
        if not sequence:
            print("Empty sequence.")
            return False

        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_move = sequence[i + 1]

            current_data = self.moves.get(current)
            next_data = self.moves.get(next_move)

            if not current_data or not next_data:
                print(f"Invalid move name(s): {current} or {next_move}")
                return False

            if current_data["postcondition"] != next_data["precondition"]:
                print(f"Invalid transition: {current} → {next_move} (postcondition mismatch)")
                return False

            if "requires" in next_data and current not in next_data["requires"]:
                print(f"Invalid transition: {next_move} requires one of {next_data['requires']}, not {current}")
                return False

            if "must_be_followed_by" in current_data and next_move not in current_data["must_be_followed_by"]:
                print(f"{current} must be followed by one of: {current_data['must_be_followed_by']}")
                return False

        self.sequence_queue.extend(sequence)
        return True

    def choose_next_move(self):
        if self.sequence_queue:
            next_seq_move = self.sequence_queue.pop(0)
            self.previous_move = self.current_move
            self.current_move = next_seq_move
            return self.moves[next_seq_move]

        # Handle simulated guapea as a valid open_position starter
        if self.current_move == "guapea":
            self.previous_move = "guapea"
            valid_moves = [
                name for name, data in self.moves.items()
                if data["precondition"] == "open_position"
                and data["level"][0] in self.difficulty_types_allowed
                and data["level"][1] in self.difficulty_levels_allowed
                and data.get("called", True)
            ]
            if valid_moves:
                chosen = random.choice(valid_moves)
                self.current_move = chosen
                return self.moves[chosen]
            else:
                return None

        current_move = self.moves.get(self.current_move)
        if not current_move:
            print(f"Move '{self.current_move}' not found.")
            return None

        possible_moves = []
        for move_name, move_data in self.moves.items():
            if not move_data.get("called", True):
                continue
            if current_move["postcondition"] != move_data["precondition"]:
                continue
            if "requires" in move_data and self.current_move not in move_data["requires"]:
                continue
            if move_data["level"][0] not in self.difficulty_types_allowed:
                continue
            if move_data["level"][1] not in self.difficulty_levels_allowed:
                continue
            if "must_be_followed_by" in current_move and move_name not in current_move["must_be_followed_by"]:
                continue
            possible_moves.append(move_name)

        if possible_moves:
            chosen = random.choice(possible_moves)
            self.previous_move = self.current_move
            self.current_move = chosen
            return self.moves[chosen]
        else:
            return None


# -------------------- Example usage --------------------

if __name__ == "__main__":
    rueda = RuedaMoves('moves.json')
    rueda.set_difficulty("intermediate", 2, anything_below=True)

    rueda.current_move = input("First move (lowercase with underscores): ").strip()

    for i in range(20):
        move_data = rueda.choose_next_move()
        if move_data:
            print(f"Next move: {move_data['called_name']}")
            if move_data.get("change_partner", 0) > 0:
                print("changed partner")
        else:
            print("No next move found that matches the difficulty criteria.")
