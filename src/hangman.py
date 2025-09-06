# src/hangman.py
import random
import threading
import time
import sys
import os
from queue import Queue, Empty
from typing import Optional, List

DEFAULT_LIVES = 6
DEFAULT_TIMEOUT_SECONDS = 15

# load words or fallback
MSVCRT_AVAILABLE = False
if os.name == "nt":
    try:
        import msvcrt  # type: ignore
        MSVCRT_AVAILABLE = True
    except Exception:
        MSVCRT_AVAILABLE = False


class Dictionary:
    def __init__(self, words_file: str = "words/words_basic.txt", phrases_file: str = "words/phrases.txt"):
        self.words_file = words_file
        self.phrases_file = phrases_file
        self._words = self._load_file(words_file)
        self._phrases = self._load_file(phrases_file)

    def _load_file(self, path: str) -> List[str]:
        try:
            with open(path, encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            return lines
        except FileNotFoundError:
            if "phrases" in path:
                return ["hello world", "unit testing", "test driven development"]
            return ["python", "hangman", "banana", "apple", "testing"]

    def get_random(self, level: str = "basic") -> str:
        if level == "basic":
            return random.choice(self._words)
        elif level == "intermediate":
            return random.choice(self._phrases)
        else:
            raise ValueError("level must be 'basic' or 'intermediate'")


# core game logic
class Game:
    def __init__(self, answer: str, lives: int = DEFAULT_LIVES):
        if not answer or not isinstance(answer, str):
            raise ValueError("answer must be a non-empty string")
        self.answer = answer
        self.lives = lives
        self.guessed_letters = set()
        self._chars = list(answer)

    # reveal masked state
    def current_state(self) -> str:
        parts = []
        for ch in self._chars:
            if not ch.isalpha():
                parts.append(ch)
            elif ch.lower() in self.guessed_letters:
                parts.append(ch)
            else:
                parts.append("_")
        return "".join(parts)

    def reveal_count(self, letter: str) -> int:
        if not letter or len(letter) != 1 or not letter.isalpha():
            raise ValueError("letter must be a single alphabetic character")
        letter = letter.lower()
        if letter in self.guessed_letters:
            return 0
        self.guessed_letters.add(letter)
        return sum(1 for ch in self._chars if ch.lower() == letter)

    def guess_letter(self, letter: str) -> bool:
        if not letter or len(letter) != 1 or not letter.isalpha():
            raise ValueError("must provide a single alphabetic letter")
        letter = letter.lower()
        # If already guessed we won't call this from CLI; keep safe behaviour
        if letter in self.guessed_letters:
            return letter in [ch.lower() for ch in self._chars]
        count = self.reveal_count(letter)
        if count > 0:
            return True
        self.lives -= 1
        return False

    def guess_full(self, attempt: str) -> bool:
        if attempt is None:
            raise ValueError("attempt must be a string")
        if attempt.strip().lower() == self.answer.strip().lower():
            for ch in self._chars:
                if ch.isalpha():
                    self.guessed_letters.add(ch.lower())
            return True
        self.lives -= 1
        return False

    def is_won(self) -> bool:
        for ch in self._chars:
            if ch.isalpha() and ch.lower() not in self.guessed_letters:
                return False
        return True

    def is_lost(self) -> bool:
        return self.lives <= 0


# platform input helper (Windows)
class HangmanCLI:
    def __init__(self, dictionary: Optional[Dictionary] = None, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, input_func=input):
        self.dictionary = dictionary or Dictionary()
        self.timeout_seconds = timeout_seconds
        self.input_func = input_func

    def _input_with_timeout_threaded(self, prompt: str, timeout: float) -> Optional[str]:
        q = Queue()

        def reader():
            try:
                v = self.input_func(prompt)
                q.put(v)
            except Exception:
                q.put(None)

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        start = time.monotonic()
        end = start + timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                try:
                    while True:
                        q.get_nowait()
                except Empty:
                    pass
                return None
            wait = min(1.0, remaining)
            try:
                value = q.get(timeout=wait)
                return value
            except Empty:
                secs_left = int(max(0, end - time.monotonic()))
                sys.stdout.write(f"\rTime left: {secs_left}s ")
                sys.stdout.flush()
                continue

    # platform input helper (Windows)
    def _input_with_timeout_windows(self, prompt: str, timeout: float) -> Optional[str]:
        if not MSVCRT_AVAILABLE:
            return self._input_with_timeout_threaded(prompt, timeout)
        sys.stdout.write(prompt)
        sys.stdout.flush()
        start = time.monotonic()
        end = start + timeout
        buf_chars = []
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch == '\r' or ch == '\n':
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return "".join(buf_chars)
                if ch == '\x08':
                    if buf_chars:
                        buf_chars.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue
                if ch == '\x03':
                    raise KeyboardInterrupt()
                buf_chars.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
            remaining = end - time.monotonic()
            if remaining <= 0:
                while msvcrt.kbhit():
                    _ = msvcrt.getwch()
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            secs_left = int(max(0, remaining))
            sys.stdout.write(f"\r{prompt}{''.join(buf_chars)}   Time left: {secs_left}s ")
            sys.stdout.flush()
            time.sleep(0.1)

    # platform input helper (Unix)
    def _input_with_timeout_unix(self, prompt: str, timeout: float) -> Optional[str]:
        import select
        sys.stdout.write(prompt)
        sys.stdout.flush()
        start = time.monotonic()
        end = start + timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None
            wait = min(1.0, remaining)
            rlist, _, _ = select.select([sys.stdin], [], [], wait)
            if rlist:
                line = sys.stdin.readline()
                if line is None:
                    return None
                return line.rstrip('\n').rstrip('\r')
            secs_left = int(max(0, end - time.monotonic()))
            sys.stdout.write(f"\r{prompt}   Time left: {secs_left}s ")
            sys.stdout.flush()

    def input_with_timeout(self, prompt: str, timeout: float) -> Optional[str]:
        if self.input_func is not input:
            return self._input_with_timeout_threaded(prompt, timeout)
        if os.name == "nt" and MSVCRT_AVAILABLE:
            return self._input_with_timeout_windows(prompt, timeout)
        else:
            return self._input_with_timeout_unix(prompt, timeout)

    # main loop
    def play(self):
        print("Welcome to Hangman (TDD project).")
        while True:
            lvl = self.input_func("Choose level: (b)asic word or (i)ntermediate phrase [b/i]: ").strip().lower()
            if lvl in ("b", "basic"):
                level = "basic"
                break
            if lvl in ("i", "intermediate"):
                level = "intermediate"
                break
            print("Invalid choice. Please enter 'b' or 'i'.")

        answer = self.dictionary.get_random(level)
        game = Game(answer, lives=DEFAULT_LIVES)
        print(f"Starting a {level} game. You have {game.lives} lives. Type 'quit' to exit.")

        while True:
            print("\nWord:", game.current_state())
            prompt = "Enter a letter (or full word/phrase) > "
            try:
                user_in = self.input_with_timeout(prompt, timeout=self.timeout_seconds)
            except KeyboardInterrupt:
                print("\nInterrupted. Goodbye.")
                return

            if user_in is None:
                game.lives -= 1
                print(f"\nTime is up! You lost one life. Lives left: {game.lives}")
            else:
                user_in = user_in.strip()
                if user_in.lower() == "quit":
                    print("You quit the game. Answer was:", game.answer)
                    return
                if len(user_in) == 0:
                    print("No input provided.")
                    continue

                if len(user_in) == 1:
                    # check for repeated guess first
                    if user_in.lower() in game.guessed_letters:
                        print(f"You already guessed '{user_in}'. Try another letter.")
                        continue
                    try:
                        correct = game.guess_letter(user_in)
                    except ValueError as e:
                        print("Invalid guess:", e)
                        continue
                    if correct:
                        print(f"Good! Letter '{user_in}' is in the answer.")
                    else:
                        print(f"Sorry, '{user_in}' is not in the answer. Lives left: {game.lives}")
                else:
                    ok = game.guess_full(user_in)
                    if ok:
                        print("Congratulations! You guessed the answer!")
                    else:
                        print(f"Wrong full guess. Lives left: {game.lives}")

            if game.is_won():
                print("\nYOU WIN! Answer:", game.answer)
                return
            if game.is_lost():
                print("\nGAME OVER. Answer:", game.answer)
                return


def _cli_main():
    cli = HangmanCLI()
    try:
        cli.play()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye.")


if __name__ == "__main__":
    _cli_main()
