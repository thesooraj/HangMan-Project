import time
import pytest
from src.hangman import Game, Dictionary, HangmanCLI

def test_dictionary_returns_word_and_phrase():
    d = Dictionary(words_file="words/words_basic.txt", phrases_file="words/phrases.txt")
    w = d.get_random("basic")
    p = d.get_random("intermediate")
    assert isinstance(w, str) and len(w) > 0
    assert isinstance(p, str) and len(p) > 0
    assert w.strip() == w

def test_initial_state_shows_underscores_for_letters():
    g = Game("Cat")
    assert g.current_state() == "___"

def test_reveal_letter_all_positions():
    g = Game("banana")
    count = g.reveal_count("a")
    assert count == 3
    assert g.current_state() == "_a_a_a"

def test_correct_guess_does_not_reduce_life():
    g = Game("apple", lives=5)
    ok = g.guess_letter("a")
    assert ok is True
    assert g.lives == 5

def test_wrong_guess_reduces_life():
    g = Game("apple", lives=3)
    ok = g.guess_letter("z")
    assert ok is False
    assert g.lives == 2

def test_full_word_guess_correct_and_incorrect():
    g = Game("hello world", lives=4)
    ok = g.guess_full("hello world")
    assert ok is True
    assert g.is_won() is True

    g2 = Game("python", lives=3)
    ok2 = g2.guess_full("java")
    assert ok2 is False
    assert g2.lives == 2

def test_win_and_loss_conditions():
    g = Game("go")
    g.guess_letter("g")
    g.guess_letter("o")
    assert g.is_won() is True

    g2 = Game("hi", lives=1)
    g2.guess_letter("z")
    assert g2.is_lost() is True

def test_invalid_letter_guess_raises():
    g = Game("test")
    with pytest.raises(ValueError):
        g.guess_letter("ab")
    with pytest.raises(ValueError):
        g.reveal_count("1")

def test_input_with_timeout_returns_none_on_timeout(monkeypatch):
    def slow_input(prompt):
        time.sleep(0.1)  
        return "x"
    cli = HangmanCLI(timeout_seconds=0.02, input_func=slow_input)
    res = cli.input_with_timeout("prompt> ", timeout=0.02)
    assert res is None

def test_input_with_timeout_returns_value_when_immediate(monkeypatch):
    def immediate_input(prompt):
        return "a"
    cli = HangmanCLI(timeout_seconds=5, input_func=immediate_input)
    res = cli.input_with_timeout("prompt> ", timeout=0.5)
    assert res == "a"
