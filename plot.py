import argparse
import math
from collections import Counter

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
    "alt 1": "Alto 1",
    "alt 2": "Alto 2",
    "sopran 1": "Soprano 1",
    "sopran 2": "Soprano 2",
}


def note_number_to_name(n: int) -> str:
    octave = n // 12 - 1
    pc = NOTE_NAMES_PC[n % 12]
    return f"{pc}{octave}"


def extract_notes(track):
    """Return a list of MIDI note numbers (0-127) for note_on events."""
    return [msg.note for msg in track if msg.type == "note_on" and msg.velocity > 0]


def track_voice_zones(track_name: str):
    lower_name = track_name.lower()
    for part, zones in VOICE_RANGES.items():
        if part.lower() in lower_name:
            return zones
    for alias, canonical in ALIAS_TO_PART.items():
        if alias in lower_name:
            return VOICE_RANGES[canonical]
    return None


def plot_histograms(midifile_path: str) -> None:
    midi = mido.MidiFile(midifile_path)
    tracks_with_notes = []

    for idx, track in enumerate(midi.tracks):
        notes = extract_notes(track)
        if notes:
            name = track.name or f"Track {idx}"
            tracks_with_notes.append((name, notes))

    if not tracks_with_notes:
        print("No note-on events found.")
        return

    n = len(tracks_with_notes)
    cols = 2
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4), squeeze=False)
    ax_list = axes.flatten()

    for ax in ax_list[n:]:
        ax.set_visible(False)

    for ax, (name, notes) in zip(ax_list, tracks_with_notes):
        counts = Counter(notes)
        xs, ys = zip(*sorted(counts.items()))

        zones = track_voice_zones(name)
        if zones:
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

        if zones:
            ax.axvspan(
                zones["lower"][0],
                zones["lower"][1] + 1,
                color="orange",
                alpha=0.2,
                zorder=0,
            )
            ax.axvspan(
                zones["green"][0],
                zones["green"][1] + 1,
                color="green",
                alpha=0.2,
                zorder=0,
            )
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
        f"Note Occurrence Histograms for '{midifile_path}'", fontsize=14, y=0.98
    )
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot note histograms for each track in a MIDI file."
    )
    parser.add_argument("midifile", help="Path to a .mid/.midi file")
    args = parser.parse_args()

    plot_histograms(args.midifile)
