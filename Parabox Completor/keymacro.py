#!/usr/bin/env python3
"""
keymacro.py - turn a sequence of letters into key presses.

Setup (Windows, recommended for games):
    pip install pydirectinput pyautogui
Setup (macOS / Linux):
    pip install pyautogui

Usage:
    python keymacro.py --file sequence.txt --map mapping.json --delay 0.2 --hold 0.08

Mapping file values can be a key name ("a", "space", "enter"), a combo
("ctrl+c"), or a pause ("wait:1.5"). Unmapped characters are pressed as
themselves (lowercased).

Abort: move the mouse to the top-left corner of the screen, or Ctrl+C.
"""
import argparse
import json
import sys
import time


def get_backend(name):
    if name in ("auto", "pydirectinput"):
        try:
            import pydirectinput as b
            b.FAILSAFE = True
            b.PAUSE = 0
            return b, "pydirectinput"
        except ImportError:
            if name == "pydirectinput":
                sys.exit("pydirectinput not installed: pip install pydirectinput")
    try:
        import pyautogui as b
    except ImportError:
        sys.exit("No backend installed: pip install pyautogui (or pydirectinput on Windows)")
    b.FAILSAFE = True
    b.PAUSE = 0
    return b, "pyautogui"


def parse_action(token):
    if token.startswith("wait:"):
        return ("wait", float(token.split(":", 1)[1]))
    if "+" in token and len(token) > 1:
        return ("hotkey", token.lower().split("+"))
    return ("key", [token.lower()])


def build_actions(sequence, keymap):
    actions = []
    for ch in sequence:
        if ch.isspace():
            continue
        actions.append((ch, parse_action(keymap.get(ch, ch))))
    return actions


def valid_keys(backend):
    keys = getattr(backend, "KEYBOARD_KEYS", None) or getattr(backend, "KEYBOARD_MAPPING", None)
    return set(keys) if keys else None


def validate(actions, backend):
    known = valid_keys(backend)
    if known is None:
        return
    bad = set()
    for _, (kind, value) in actions:
        if kind in ("key", "hotkey"):
            bad |= {k for k in value if k not in known}
    if bad:
        sys.exit(f"Unknown key name(s) for this backend: {sorted(bad)}")


def run(actions, backend, delay, hold, verbose):
    for i, (ch, (kind, value)) in enumerate(actions, 1):
        if kind == "wait":
            time.sleep(value)
            continue
        for k in value:
            backend.keyDown(k)
        time.sleep(hold)
        for k in reversed(value):
            backend.keyUp(k)
        if verbose:
            print(f"{i}/{len(actions)}: {ch} -> {'+'.join(value)}")
        time.sleep(delay)


def main():
    p = argparse.ArgumentParser(description="Press keys from a sequence of letters.")
    p.add_argument("sequence", nargs="?", help="the letter sequence")
    p.add_argument("--file", help="read the sequence from a text file")
    p.add_argument("--map", help="JSON mapping file")
    p.add_argument("--delay", type=float, default=0.15, help="seconds between presses")
    p.add_argument("--hold", type=float, default=0.05, help="seconds each key is held down")
    p.add_argument("--start-delay", type=float, default=3.0)
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--backend", choices=["auto", "pydirectinput", "pyautogui"], default="auto")
    p.add_argument("--quiet", action="store_true", help="don't print each key press")
    args = p.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            sequence = f.read()
    elif args.sequence:
        sequence = args.sequence
    else:
        p.error("provide a sequence or --file")

    keymap = {}
    if args.map:
        with open(args.map, "r", encoding="utf-8") as f:
            keymap = json.load(f)

    backend, backend_name = get_backend(args.backend)
    actions = build_actions(sequence, keymap)
    validate(actions, backend)

    print(f"Backend: {backend_name} | {len(actions)} steps")
    print(f"Starting in {args.start_delay}s - click the window you want to control...")
    time.sleep(args.start_delay)

    for _ in range(args.repeat):
        run(actions, backend, args.delay, args.hold, not args.quiet)
    print("Done.")


if __name__ == "__main__":
    main()
