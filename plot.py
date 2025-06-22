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

VOICE_RANGES = [
    (["mezzo soprano", "mezzo"], (57, 77)),
    (["soprano"], (60, 81)),
    (["alto"], (53, 74)),
    (["tenor"], (47, 67)),
    (["baritone"], (43, 64)),
    (["bass"], (40, 60)),
]


def note_number_to_name(n: int) -> str:
    octave = n // 12 - 1
    pc = NOTE_NAMES_PC[n % 12]
    return f"{pc}{octave}"


def extract_notes(track):
    """Return a list of MIDI note numbers (0-127) for note_on events."""
    return [msg.note for msg in track if msg.type == "note_on" and msg.velocity > 0]


def track_voice_range(track_name: str):
    lower_name = track_name.lower()
    for keywords, rng in VOICE_RANGES:
        for kw in keywords:
            if kw in lower_name:
                return rng
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

        voice_rng = track_voice_range(name)
        if voice_rng:
            min_note = min(min(xs), voice_rng[0])
            max_note = max(max(xs), voice_rng[1])
        else:
            min_note, max_note = min(xs), max(xs)

        ax.set_xlim(min_note - 2, max_note + 2)

        xtick_positions = [p for p in range(min_note, max_note + 1) if p % 12 == 0]
        if not xtick_positions:
            xtick_positions = [min_note, max_note]

        ax.bar(xs, ys, width=0.8, align="center")
        ax.set_xticks(xtick_positions)
        ax.set_xticklabels(
            [note_number_to_name(p) for p in xtick_positions],
            rotation=45,
            ha="right",
            fontsize=8,
        )

        if voice_rng:
            ax.axvspan(
                voice_rng[0],
                voice_rng[1],
                color="green",
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
