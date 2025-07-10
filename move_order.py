import json
import random
import heapq
from collections import deque
from tqdm import tqdm
import numpy as np
from tabulate import tabulate

class RuedaMoves:
    def __init__(self, filepath):
        self.moves = self.load_moves(filepath)
        self.difficulty_types_allowed = None
        self.difficulty_levels_allowed = None
        self.previous_move = None
        self.current_move = "guapea"
        self.sequence_queue = []
        self.recent_history = deque(maxlen=10)
        self.song_duration_beats = 64  # default
        self.locked_out_of_closed_closed = False
        self.move_difficulty = "medium"  # affects dile_que_no weighting

    def load_moves(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def set_difficulty(self):
        difficulty_type = input("Select difficulty (beginner/intermediate/advanced): ").strip().lower()
        try:
            difficulty_level = int(input("Enter difficulty sub‑level (e.g. 1 or 2): ").strip())
        except ValueError:
            print("Invalid level. Defaulting to 1.")
            difficulty_level = 1
        anything_below = input("Include all easier levels too? (y/n): ").strip().lower() == "y"

        if anything_below:
            if isinstance(difficulty_level, list):
                difficulty_level = max(difficulty_level)
            self.difficulty_levels_allowed = range(1, difficulty_level + 1)
            difficulty_types = {"beginner": 1, "intermediate": 2, "advanced": 3}
            input_levels = [difficulty_types.get(difficulty_type)] if isinstance(difficulty_type, str) else []
            highest_level = max(input_levels) if input_levels else 1
            self.difficulty_types_allowed = [d for d, lvl in difficulty_types.items() if lvl <= highest_level]
        else:
            self.difficulty_levels_allowed = [difficulty_level]
            self.difficulty_types_allowed = [difficulty_type]
            
        difficulty_setting = input("How often should 'dile que no' appear? (easy / medium / hard): ").strip().lower()
        self.set_move_difficulty(difficulty_setting)

    def set_move_difficulty(self, level: str):
        if level not in {"easy", "medium", "hard"}:
            raise ValueError("Invalid move difficulty: choose easy, medium, or hard.")
        self.move_difficulty = level

    def generate_sequence(self, max_beats, method="astar"):
        if method == "astar":
            return self.generate_sequence_astar(max_beats)
        elif method == "n-gram":
            return self.generate_sequence_ngram(max_beats)
        else:
            raise ValueError(f"Unknown sequence generation method: {method}")
    
    def get_valid_next_moves(self, move_name, path=None):
        if move_name == "guapea":
            return [
                m_name for m_name, m_data in self.moves.items()
                if m_data["precondition"] == "open_position"
                and m_data["level"][0] in self.difficulty_types_allowed
                and m_data["level"][1] in self.difficulty_levels_allowed
                and m_data.get("called", True)
            ]

        path = path or []
        move_data = self.moves.get(move_name)
        valid = []

        transitioned_to_open = any(
            p in self.moves and
            self.moves[p].get("precondition") == "closed_position" and
            self.moves[p].get("postcondition") == "open_position"
            for p in path
        )

        closed_chain = 0
        for m in reversed(path):
            if m not in self.moves:
                break
            mdata = self.moves[m]
            if mdata.get("precondition") == "closed_position" and mdata.get("postcondition") == "closed_position":
                closed_chain += 1
            else:
                break

        at_intermediate_or_higher = any(
            lvl in self.difficulty_types_allowed
            for lvl in ["intermediate", "advanced"]
        )

        for m_name, m_data in self.moves.items():
            if not m_data.get("called", True):
                continue
            if move_data["postcondition"] != m_data["precondition"]:
                continue
            if "requires" in m_data and move_name not in m_data["requires"]:
                continue
            if m_data["level"][0] not in self.difficulty_types_allowed:
                continue
            if m_data["level"][1] not in self.difficulty_levels_allowed:
                continue
            if "must_be_followed_by" in move_data and m_name not in move_data["must_be_followed_by"]:
                continue
            if path and path[-1] == m_name:
                continue
            if m_name == "dile_que_no" and path and path[-1] == "dile_que_no":
                continue
            if transitioned_to_open and (
                m_data.get("precondition") == "closed_position" and
                m_data.get("postcondition") == "closed_position"
            ):
                if not m_name.startswith("exhibela"):
                    continue
            if (
                at_intermediate_or_higher and
                closed_chain >= 10 and
                m_data.get("precondition") == "closed_position" and
                m_data.get("postcondition") == "closed_position"
            ):
                continue

            valid.append(m_name)

        return valid

    # -------------------------------------------------------------------------
    # generate_sequence_astar(self, max_beats)
    #
    # This function generates a sequence of Rueda dance moves using an A* search
    # strategy. The goal is to construct a path of moves whose total duration
    # (in beats) fills the song's length (rounded to the nearest multiple of 8).
    #
    # The search explores valid transitions between moves, guided by a cost
    # function that balances several factors:
    #
    #  - g: total beats already accumulated in the path
    #  - h: heuristic estimating how many 8-beat moves remain
    #  - recent_weight: penalizes moves that have occurred recently (within the
    #    last 10 moves), with stronger penalties for more frequent repetition.
    #    Grouped moves like "exhibela*" share a repetition penalty.
    #  - bonus: encourages novelty by lowering the cost for new/unseen moves
    #  - partner_pressure_weight: exponentially decreases the cost of
    #    selecting "dile_que_no" the more partner-switching moves occur without
    #    one, encouraging its use for structural flow and position resetting.
    #
    # Additional search constraints include:
    #  - Moves must match allowed difficulty type and level
    #  - Contextual rules such as preventing back-to-back repeats
    #  - Transition logic must satisfy precondition/postcondition compatibility
    #  - Special rules such as locked-out closed→closed after transitioning to
    #    open position (except for exhibela moves), or maximum 10 chained
    #    closed→closed moves at intermediate+ difficulty
    #
    # Once a valid sequence is found that fills the beat target, it is stored
    # in self.sequence_queue for scheduled playback. If no such sequence is
    # found under the given constraints, the function prints an error and returns
    # an empty list.
    # -------------------------------------------------------------------------
    def generate_sequence_astar(self, max_beats):
        def move_key(move_name: str) -> str:
            if move_name.startswith("exhibela"):
                return "exhibela"
            return move_name

        frontier = []
        heapq.heappush(frontier, (0, [self.current_move]))

        seen = set()
        g_scores = {}
        pbar = tqdm(total=1, bar_format="{desc}: {percentage:3.0f}%")

        while frontier:
            cost, path = heapq.heappop(frontier)
            path_key = tuple(path)
            if path_key in seen:
                continue
            seen.add(path_key)

            total_beats = sum(
                8 if m == "guapea" else self.moves[m].get("beat_count", 8)
                for m in path
            )

            key = (path[-1], total_beats)
            if key in g_scores and g_scores[key] <= cost:
                continue
            g_scores[key] = cost

            percent = (total_beats / max_beats) * 100
            pbar.set_description(f"Searching (filled {percent:5.1f}%)")
            pbar.refresh()

            if total_beats > max_beats:
                continue
            if max_beats - total_beats < 8:
                pbar.set_description("Sequence complete")
                pbar.refresh()
                pbar.close()
                self.sequence_queue = path[1:]
                return path

            # Compute total change_partner since last dile_que_no
            partner_change_sum = 0
            for m in reversed(path):
                if m == "dile_que_no":
                    break
                if m == "guapea":
                    continue
                partner_change_sum += self.moves.get(m, {}).get("change_partner", 0)

            last_move = path[-1]
            for next_move in self.get_valid_next_moves(last_move, path):
                if len(path) >= 2 and path[-1] == next_move:
                    continue  # avoid exact repeats

                recent_keys = [move_key(m) for m in path[-10:]]
                current_key = move_key(next_move)
                count = recent_keys.count(current_key)
                recent_weight = 25 * count if count > 0 else 1

                used_moves = set(path)
                bonus = -100 if next_move not in used_moves else 0

                # Exponentially encourage dile_que_no based on partner changes and difficulty
                if next_move == "dile_que_no":
                    base = {"easy": 1.2, "medium": 1.5, "hard": 2.0}.get(self.move_difficulty, 1.5)
                    partner_pressure_weight = 1 / (base ** partner_change_sum)
                else:
                    partner_pressure_weight = 1.0

                next_beat = self.moves[next_move].get("beat_count", 8)
                g = total_beats + next_beat
                h = max(0, max_beats - g) // 8
                f = (g + h * recent_weight + bonus) * partner_pressure_weight

                heapq.heappush(frontier, (f, path + [next_move]))

        pbar.set_description("❌ Sequence failed")
        pbar.close()
        return []

    def generate_sequence_ngram(self, max_beats):
        n_gram_size = input("Enter n-gram size: ").strip()
        n_gram_size = int(n_gram_size) if n_gram_size.isdigit() else 3
        
        first_move = self.current_move
        
        tokenized_moves = {}
        for token, move in enumerate(self.moves.keys()):
               tokenized_moves[move] = token
        
        probabilities = np.zeros(len(self.moves) * n_gram_size, dtype=np.float32)
        sequence = [first_move, random.choice(self.get_valid_next_moves(first_move))]
                
        def unigram():
            def move_key(move_name: str) -> str:
                if move_name.startswith("exhibela"):
                    return "exhibela"
                return move_name

            move_keys = {m: move_key(m) for m in self.moves}
            tokenized_moves = {m: i for i, m in enumerate(self.moves)}

            closed_key_counts = {}
            open_key_counts = {}

            closed_probabilities = np.zeros(len(self.moves), dtype=np.float32)
            open_probabilities = np.zeros(len(self.moves), dtype=np.float32)

            sequence = [self.current_move]
            curr_move = random.choice(self.get_valid_next_moves(self.current_move))
            sequence.append(curr_move)

            total_beats = 8 + self.moves[curr_move].get("beat_count", 8)
            iteration = 0
            
            difficulty_bias = {
                "easy": 3.0,
                "medium": 1.0,
                "hard": 0.3
            }
            dq_bias = difficulty_bias.get(self.move_difficulty, 1.0)

            def is_closed_to_closed(move_name):
                m = self.moves.get(move_name, {})
                return m.get("precondition") == "closed_position" and m.get("postcondition") == "closed_position"

            def is_opening_move(move_name):
                m = self.moves.get(move_name, {})
                return m.get("postcondition") == "open_position"

            def is_closed_position_move(move_name):
                m = self.moves.get(move_name, {})
                return m.get("precondition") == "closed_position"

            in_open_position = False  # tracks if we’ve transitioned to open

            while total_beats <= max_beats:
                # Check last 3 moves to determine if we’re in a chain of closed->closed
                in_closed_chain = (
                    not in_open_position and
                    all(m in self.moves and is_closed_to_closed(m) for m in sequence[-3:])
                )
                context = "closed" if in_closed_chain else "open"

                # Count frequencies for probability
                key_counts = closed_key_counts if context == "closed" else open_key_counts
                key_counts.clear()
                for m in sequence:
                    if m not in move_keys:
                        continue
                    key = move_keys[m]
                    key_counts[key] = key_counts.get(key, 0) + 1

                all_keys = set(move_keys.values())
                key_probs = {
                    key: key_counts.get(key, 0) / len(sequence)
                    for key in all_keys
                }

                probabilities = closed_probabilities if context == "closed" else open_probabilities
                for move, token in tokenized_moves.items():
                    key = move_keys[move]
                    prob = key_probs.get(key, 0)
                    if move == "dile_que_no":
                        prob *= dq_bias
                    probabilities[token] = prob


                min_value = np.min(probabilities)
                min_indices = np.where(probabilities == min_value)[0]
                min_moves = {move for move, token in tokenized_moves.items() if token in min_indices}

                next_possible_moves = self.get_valid_next_moves(curr_move)

                # If we've opened the position, disallow any closed->closed moves
                if in_open_position:
                    next_possible_moves = [
                        m for m in next_possible_moves if not is_closed_to_closed(m)
                    ]

                # Avoid back-to-back exhibelas
                last_key = move_key(sequence[-1])
                min_moves = [
                    m for m in min_moves
                    if m in next_possible_moves and not (last_key == "exhibela" and move_key(m) == "exhibela")
                ]

                if not min_moves:
                    # fallback: still avoid exhibela repeats
                    min_moves = [
                        m for m in next_possible_moves
                        if not (last_key == "exhibela" and move_key(m) == "exhibela")
                    ]
                if not min_moves:
                    min_moves = next_possible_moves  # last resort

                next_move = random.choice(min_moves)
                token = tokenized_moves[next_move]
                chosen_prob = probabilities[token]
                max_prob = np.max(probabilities)
                max_moves = [m for m, tok in tokenized_moves.items() if probabilities[tok] == max_prob]

                print(f"[Step {iteration}] Context: {context.upper()} | Chose: {next_move} "
                    f"| Prob: {chosen_prob:.3f} | Max: {max_prob:.3f} (Move(s): {', '.join(max_moves)})")

                sequence.append(next_move)
                curr_move = next_move
                total_beats += self.moves[curr_move]["beat_count"]
                iteration += 1

                # Update position state
                if is_opening_move(next_move):
                    in_open_position = True

                if context == "closed" and not is_closed_to_closed(next_move):
                    closed_key_counts.clear()
                    closed_probabilities[:] = 0

            return sequence

        
        if n_gram_size == 1:
            return unigram()
        else:
            raise ValueError("Not implemented yet")

    def choose_next_move(self):
        if self.sequence_queue:
            next_seq_move = self.sequence_queue.pop(0)
            self.previous_move = self.current_move
            self.current_move = next_seq_move
            self.recent_history.append(self.current_move)
            return self.moves[next_seq_move]
        return None
