# etapasJuego/wordsearch/engine.py
import random
from typing import List, Tuple, Dict

# === Utilidades base (adaptadas del PDF) ===
def fill_soup_random(available_letters: List[str], board_size: int) -> List[List[str]]:
    soup = []
    for _ in range(board_size):
        row = [random.choice(available_letters) for _ in range(board_size)]
        soup.append(row)
    return soup

def get_params():
    is_horizontal = random.choice([True, False])
    is_reverse = random.choice([True, False])
    return is_horizontal, is_reverse

def get_indexes(word: str, board_size: int, horizontal: bool, reverse: bool):
    if horizontal and not reverse:
        return list(range(board_size)), list(range(0, board_size - len(word) + 1))
    elif horizontal and reverse:
        return list(range(board_size)), list(range(len(word) - 1, board_size))
    elif (not horizontal) and (not reverse):
        return list(range(0, board_size - len(word) + 1)), list(range(board_size))
    else:
        return list(range(len(word) - 1, board_size)), list(range(board_size))

def get_word_positions(start_r: int, start_c: int, is_horizontal: bool, is_reverse: bool, word: str):
    positions = []
    if is_horizontal:
        if not is_reverse:
            rng = range(start_c, start_c + len(word))
        else:
            rng = range(start_c, start_c - len(word), -1)
        for j in rng:
            positions.append((start_r, j))
    else:
        if not is_reverse:
            rng = range(start_r, start_r + len(word))
        else:
            rng = range(start_r, start_r - len(word), -1)
        for i in rng:
            positions.append((i, start_c))
    return positions

def is_valid_position(word_positions, used_positions):
    used = set(used_positions)
    for p in word_positions:
        if p in used:
            return False
    return True

# === Generación principal ===
def create_soup(words: List[str], board_size: int = 10, alphabet: List[str] = None):
    if alphabet is None:
        alphabet = list("abcdefghijklmnñopqrstuvwxyz")  # español
    soup = fill_soup_random(alphabet, board_size)
    used_positions = []
    dict_word_position: Dict[str, List[Tuple[int, int]]] = {}

    for w in words:
        valid = False
        tries = 0
        while not valid:
            tries += 1
            if tries > 5000:
                # Reintenta logicamente: cambia a un nuevo tablero (fallback simple)
                soup = fill_soup_random(alphabet, board_size)
                used_positions.clear()
                dict_word_position.clear()
                tries = 0
            is_h, is_r = get_params()
            rows, cols = get_indexes(w, board_size, is_h, is_r)
            start_r = random.choice(rows)
            start_c = random.choice(cols)
            positions = get_word_positions(start_r, start_c, is_h, is_r, w)
            valid = is_valid_position(positions, used_positions)
        dict_word_position[w] = positions
        for k, (i, j) in enumerate(positions):
            soup[i][j] = w[k] if not is_r else w[::-1][k]
            used_positions.append((i, j))

    return soup, dict_word_position

# === Validación de una selección concreta enviada desde el frontend ===
def validate_selection(selection: List[Tuple[int, int]], dict_word_position: Dict[str, List[Tuple[int, int]]]):
    """
    selection: lista de (i, j) contiguos que el jugador marcó
    Devuelve: (found: bool, word: str | None)
    """
    sel = selection
    sel_rev = list(reversed(selection))
    for w, pos in dict_word_position.items():
        if sel == pos or sel_rev == pos:
            return True, w
    return False, None
