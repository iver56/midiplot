import argparse
import math
import os
from collections import Counter
from pathlib import Path
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import mido

NOTE_NAMES_PC = [
    "C",
    "C♯/D♭",
    "D",
    "D♯/E♭",
    "E",
    "F",
    "F♯/G♭",
    "G",
    "G♯/A♭",
    "A",
    "A♯/B♭",
    "B",
]

# Voice part ranges expressed in MIDI numbers (inclusive)
VOICE_RANGES = {
    "Soprano": {"lower": (55, 61), "green": (62, 77), "upper": (78, 81)},
    "Soprano 1": {"lower": (60, 61), "green": (62, 79), "upper": (80, 81)},
    "Soprano 2": {"lower": (55, 57), "green": (58, 77), "upper": (78, 79)},
    "Mezzo-soprano": {"lower": (55, 57), "green": (58, 77), "upper": (78, 81)},
    "Alto": {"lower": (52, 56), "green": (57, 74), "upper": (75, 79)},
    "Alto 1": {"lower": (55, 56), "green": (57, 76), "upper": (77, 79)},
    "Alto 2": {"lower": (52, 53), "green": (54, 74), "upper": (75, 77)},
    "Tenor": {"lower": (45, 48), "green": (49, 66), "upper": (67, 72)},
    "Tenor 1": {"lower": (47, 48), "green": (49, 67), "upper": (68, 72)},
    "Tenor 2": {"lower": (45, 47), "green": (48, 66), "upper": (67, 69)},
    "Baritone": {"lower": (41, 44), "green": (45, 64), "upper": (65, 67)},
    "Bass": {"lower": (36, 44), "green": (45, 60), "upper": (61, 67)},
    "Bass 1": {"lower": (41, 44), "green": (45, 64), "upper": (65, 67)},
    "Bass 2": {"lower": (36, 39), "green": (40, 60), "upper": (61, 64)},
}

ALIAS_TO_PART = {
    "alt": "Alto",
    "alt 1": "Alto 1",
    "alt 2": "Alto 2",
    "bariton": "Baritone",
    "sopran": "Soprano",
    "sopran 1": "Soprano 1",
    "sopran 2": "Soprano 2",
}


def note_number_to_name(n: int) -> str:
    octave = n // 12 - 1
    pc = NOTE_NAMES_PC[n % 12]
    return f"{pc}{octave}"


def extract_notes_from_track(track) -> List[int]:
    """Return a list of MIDI note numbers (0-127) for note_on events in a single track."""
    return [msg.note for msg in track if msg.type == "note_on" and msg.velocity > 0]


def get_voice_zones(name_identifier: str) -> Optional[dict]:
    """Find voice ranges based on a string (track name or filename)."""
    lower_name = name_identifier.lower()
    for part, zones in VOICE_RANGES.items():
        if part.lower() in lower_name:
            return zones
    for alias, canonical in ALIAS_TO_PART.items():
        if alias in lower_name:
            return VOICE_RANGES[canonical]
    return None


def collect_data_from_single_file(filepath: Path) -> List[Tuple[str, List[int]]]:
    """
    Standard mode: Open one MIDI file and treat every internal track as a separate entity.
    """
    midi = mido.MidiFile(filepath)
    tracks_with_notes = []

    for idx, track in enumerate(midi.tracks):
        notes = extract_notes_from_track(track)
        if notes:
            name = track.name.strip() or f"Track {idx}"
            tracks_with_notes.append((name, notes))

    return tracks_with_notes


def collect_data_from_directory(dirpath: Path) -> List[Tuple[str, List[int]]]:
    """
    Folder mode: Find all MIDI files. Treat each FILE as a separate entity
    (merging all internal tracks of that file).
    """
    files = sorted(list(dirpath.glob("*.mid")) + list(dirpath.glob("*.midi")))
    tracks_with_notes = []

    if not files:
        print(f"No .mid or .midi files found in {dirpath}")
        return []

    for f in files:
        try:
            midi = mido.MidiFile(f)
            # Merge all tracks in this file into one list of notes
            all_file_notes = []
            for track in midi.tracks:
                all_file_notes.extend(extract_notes_from_track(track))

            if all_file_notes:
                # Use last part of filename stem as the name
                tracks_with_notes.append((f.stem.split("-")[-1], all_file_notes))
        except Exception as e:
            print(f"Error reading {f}: {e}")

    return tracks_with_notes


def generate_plots(data_list: List[Tuple[str, List[int]]], source_title: str) -> None:
    """
    Generic plotting function.
    data_list: List of tuples (Name, [NoteInts])
    source_title: String title for the entire figure
    """
    if not data_list:
        print("No notes found to plot.")
        return

    # Print summary to console
    total_notes = 0
    for name, notes in data_list:
        count = len(notes)
        print(f"{name}: {count}")
        total_notes += count
    print(f"Total: {total_notes}")

    n = len(data_list)
    cols = 2
    rows = math.ceil(n / cols)

    # Adjust figure size dynamically based on rows
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)
    ax_list = axes.flatten()

    # Hide unused subplots
    for ax in ax_list[n:]:
        ax.set_visible(False)

    for ax, (name, notes) in zip(ax_list, data_list):
        counts = Counter(notes)
        if not counts:
            continue

        xs, ys = zip(*sorted(counts.items()))

        zones = get_voice_zones(name)

        # Determine X-Axis Limits
        if zones:
            # Ensure the view covers at least the defined lower/upper range OR the actual notes
            min_note = min(min(xs), zones["lower"][0])
            max_note = max(max(xs), zones["upper"][1])
        else:
            min_note, max_note = min(xs), max(xs)

        ax.set_xlim(min_note - 2, max_note + 2)

        xtick_positions = [p for p in range(min_note, max_note + 1) if p % 12 == 0]
        if not xtick_positions:
            xtick_positions = [min_note, max_note]

        ax.bar(xs, ys, width=0.8, align="edge")
        ax.set_xticks(xtick_positions)
        ax.set_xticklabels(
            [note_number_to_name(p) for p in xtick_positions],
            rotation=45,
            ha="right",
            fontsize=8,
        )

        # Draw Range Zones
        if zones:
            # Lower (Warning/Extension)
            ax.axvspan(
                zones["lower"][0],
                zones["lower"][1] + 1,
                color="orange",
                alpha=0.2,
                zorder=0,
            )
            # Green (Comfortable)
            ax.axvspan(
                zones["green"][0],
                zones["green"][1] + 1,
                color="green",
                alpha=0.2,
                zorder=0,
            )
            # Upper (Warning/Extension)
            ax.axvspan(
                zones["upper"][0],
                zones["upper"][1] + 1,
                color="orange",
                alpha=0.2,
                zorder=0,
            )

        ax.set_xlabel("Pitch")
        ax.set_ylabel("Occurrences")
        ax.set_title(name)

    fig.suptitle(
        f"Note Occurrence Histograms for '{source_title}'", fontsize=14, y=0.98
    )
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot note histograms. Accepts a single MIDI file with one or more tracks OR a folder of MIDI files (single track per MIDI file)."
    )
    parser.add_argument(
        "input_path", help="Path to a .mid file OR a folder containing .mid files"
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)

    if not input_path.exists():
        print(f"Error: Path '{input_path}' does not exist.")
        return

    data = []
    title = ""

    if input_path.is_dir():
        print(f"Processing folder: {input_path}")
        data = collect_data_from_directory(input_path)
        title = input_path.name + " (Folder)"
    elif input_path.is_file():
        print(f"Processing file: {input_path}")
        data = collect_data_from_single_file(input_path)
        title = input_path.name
    else:
        print("Invalid input.")
        return

    generate_plots(data, title)


if __name__ == "__main__":
    main()
