"""Compose Boomy's splash music (src/assets/splash-music.mp3), an original 6 s cue.

Synthesized from scratch, so the track is Boomy's own and can be regenerated. It follows the
splash's opening (features/onboarding/splash.tsx): a warm pad swells with the glow while a
rising arpeggio carries the mascot up (0 to 3.2 s); as its eyes open, a soft low "boom" and a
sparkle chord bloom (3.2 s), echoing the three sparks of the mascot; then everything rings out.

Run from app/: uv run --no-project --with numpy python scripts/compose-splash-music.py
Needs ffmpeg on PATH for the MP3.
"""

import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

RATE = 44_100
LENGTH = 6.0
BLOOM = 3.2  # seconds: when the mascot arrives and opens its eyes
OUT = Path(__file__).resolve().parent.parent / "src/assets/splash-music.mp3"

rng = np.random.default_rng(7)  # fixed, so every run renders the same track
t = np.arange(int(RATE * LENGTH)) / RATE


def hz(note: str) -> float:
    """A note name like "F#4" as a frequency (A4 = 440 Hz)."""
    names = {
        "C": 0,
        "C#": 1,
        "D": 2,
        "D#": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "G": 7,
        "G#": 8,
        "A": 9,
        "A#": 10,
        "B": 11,
    }
    name, octave = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[name] + 12 * (octave + 1) - 69) / 12)


def window(start: float, attack: float, decay: float) -> np.ndarray:
    """An envelope: silent before `start`, a sine-shaped rise over `attack`, then an exponential decay."""
    x = t - start
    rise = np.clip(x / attack, 0, 1)
    env = np.sin(rise * np.pi / 2) ** 2
    return np.where(x < 0, 0, env * np.exp(-np.maximum(x - attack, 0) / decay))


def bell(note: str, start: float, gain: float, decay: float = 1.4) -> np.ndarray:
    """A soft FM bell: a sine carrier with a decaying 3.5:1 modulator, for the glassy attack."""
    f = hz(note)
    x = np.maximum(t - start, 0)
    index = 1.6 * np.exp(-x / 0.25)
    tone = np.sin(2 * np.pi * f * x + index * np.sin(2 * np.pi * f * 3.5 * x))
    return gain * tone * window(start, 0.008, decay)


def pad(
    notes: list[str], start: float, rise: float, hold: float, gain: float
) -> np.ndarray:
    """A warm pad: three slightly detuned sines per note, swelling in and fading out."""
    out = np.zeros_like(t)
    for note in notes:
        for cents in (-7, 0, 6):
            f = hz(note) * 2 ** (cents / 1200)
            out += np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    x = t - start
    env = np.clip(x / rise, 0, 1) ** 2 * np.clip(
        (start + rise + hold + 1.6 - t) / 1.6, 0, 1
    )
    return gain * out / (3 * len(notes)) * np.where(x < 0, 0, env)


def boom(start: float, gain: float) -> np.ndarray:
    """A soft low thump: a sine gliding from 90 Hz down to 48 Hz, with a quick swell."""
    x = np.maximum(t - start, 0)
    freq = 48 + 42 * np.exp(-x / 0.12)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    return gain * np.sin(phase) * window(start, 0.02, 0.3)


def shimmer(start: float, gain: float) -> np.ndarray:
    """A breath of high, filtered noise rising into the bloom, like the glow catching light."""
    noise = rng.standard_normal(t.size)
    kernel = np.hanning(9)
    airy = noise - np.convolve(
        noise, kernel / kernel.sum(), mode="same"
    )  # keep the highs
    x = t - (start - 0.9)
    env = np.where((x > 0) & (x < 0.9), (x / 0.9) ** 3, 0) + window(start, 0.001, 0.18)
    return gain * airy * env


def reverb(
    dry: np.ndarray, seconds: float = 2.2, mix: float = 0.32, seed: int = 0
) -> np.ndarray:
    """A plain hall: convolution with exponentially decaying, lightly smoothed noise."""
    n = int(RATE * seconds)
    tail = np.random.default_rng(seed).standard_normal(n) * np.exp(
        -np.arange(n) / (RATE * seconds / 6)
    )
    tail = np.convolve(tail, np.ones(6) / 6, mode="same")
    tail /= np.sqrt(np.sum(tail**2))
    wet = np.fft.irfft(
        np.fft.rfft(dry, dry.size + n) * np.fft.rfft(tail, dry.size + n)
    )[: dry.size]
    return (1 - mix) * dry + mix * wet


def compose() -> np.ndarray:
    # The rise, in D major: a Dmaj9 pad under an arpeggio climbing with the mascot.
    left = pad(["D3", "A3", "E4", "F#4"], 0.0, 2.6, 1.6, 0.30)
    right = pad(["D3", "A3", "E4", "C#5"], 0.0, 2.6, 1.6, 0.30)
    climb = ["A3", "D4", "E4", "F#4", "A4", "D5"]
    for i, note in enumerate(climb):
        at = 0.35 + i * 0.47
        pan = 0.35 + 0.3 * (i % 2)  # alternate a little left and right
        b = bell(note, at, 0.16 + 0.02 * i, decay=1.1)
        left += b * (1 - pan)
        right += b * pan

    # The bloom: the boom and three sparkle notes, one per spark, then a Gmaj7 colour under it.
    for side in (left, right):
        side += boom(BLOOM, 0.28)
        side += shimmer(BLOOM, 0.05)
    for note, delay, pan in (("F#5", 0.0, 0.3), ("A5", 0.07, 0.7), ("E6", 0.15, 0.5)):
        b = bell(note, BLOOM + delay, 0.20, decay=1.8)
        left += b * (1 - pan)
        right += b * pan
    bloom_pad = pad(["G3", "B3", "D4", "F#4"], BLOOM - 0.1, 0.5, 0.9, 0.22)
    left += bloom_pad
    right += bloom_pad

    stereo = np.stack([reverb(left, seed=1), reverb(right, seed=2)])
    fade = np.clip((LENGTH - t) / 1.4, 0, 1) ** 1.5  # ring out to silence by the end
    stereo *= fade
    return stereo / np.max(np.abs(stereo)) * 0.89


def main() -> None:
    audio = compose()
    pcm = (audio.T * 32767).astype("<i2")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "splash.wav"
        with wave.open(str(wav), "wb") as f:
            f.setnchannels(2)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(pcm.tobytes())
        # Quiet under the splash, as the original was (about -34 LUFS), with headroom.
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(wav),
                "-af",
                "loudnorm=I=-34:TP=-3:LRA=11",
                "-ar",
                str(RATE),
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                "-map_metadata",
                "-1",
                str(OUT),
            ],
            check=True,
        )
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
