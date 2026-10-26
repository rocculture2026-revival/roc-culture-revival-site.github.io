"""產生 Reels 用的原創配樂：五聲音階、撥弦（Karplus-Strong 合成），近似古箏音色。
全部由程式合成、旋律為原創，沒有版權問題。用法：python3 music.py → assets/bgm-pentatonic.wav"""
import os, wave
import numpy as np

SR = 44100
BEAT = 0.75  # 每拍秒數（80 BPM）
NOTE = {"A2": 110.0, "D3": 146.83, "A3": 220.0, "D4": 293.66, "E4": 329.63, "F#4": 369.99,
        "A4": 440.0, "B4": 493.88, "D5": 587.33, "E5": 659.26}

# 原創旋律（D 宮調五聲音階），(音, 拍數)
MELODY = [
    ("A4", 1), ("B4", .5), ("A4", .5), ("F#4", 1), ("E4", 1), ("D4", 2), ("A3", 2),
    ("D4", 1), ("E4", 1), ("F#4", 1), ("A4", 1), ("B4", 1.5), ("A4", .5), ("A4", 2),
    ("D5", 1), ("B4", .5), ("A4", .5), ("B4", 1), ("A4", 1), ("F#4", 1), ("E4", 1), ("F#4", 2),
    ("E4", 1), ("F#4", 1), ("A4", 1), ("F#4", .5), ("E4", .5), ("D4", 4),
]
BASS = [("D3", 4), ("A2", 4)] * 4


def pluck(freq, dur, bright=0.5, decay=0.9985):
    """Karplus-Strong 撥弦。"""
    n = int(SR * dur)
    p = int(SR / freq)
    rng = np.random.default_rng(int(freq * 100))
    buf = rng.uniform(-1, 1, p)
    buf = np.convolve(buf, np.ones(3) / 3, mode="same") * (1 - bright) + buf * bright
    out = np.empty(n + p)
    out[:p] = buf
    i = p
    while i < n + p:
        prev = out[i - p:i]
        blk = decay * 0.5 * (prev + np.roll(prev, 1))
        m = min(p, n + p - i)
        out[i:i + m] = blk[:m]
        i += m
    return out[p:]


def track(seq, gain, ring=3.0):
    total = sum(b for _, b in seq) * BEAT + ring
    y = np.zeros(int(SR * total))
    t = 0.0
    for name, beats in seq:
        s = pluck(NOTE[name], beats * BEAT + ring)
        a = int(t * SR)
        y[a:a + len(s)] += s[:len(y) - a] * gain
        t += beats * BEAT
    return y


def reverb(x, secs=1.8, mix=0.25):
    rng = np.random.default_rng(7)
    n = int(SR * secs)
    ir = rng.normal(0, 1, n) * np.exp(-np.linspace(0, 6, n))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    wet /= np.max(np.abs(wet)) + 1e-9
    return x * (1 - mix) + wet * np.max(np.abs(x)) * mix


if __name__ == "__main__":
    mel, bass = track(MELODY, 1.0), track(BASS, 0.45)
    n = max(len(mel), len(bass))
    mix = np.pad(mel, (0, n - len(mel))) + np.pad(bass, (0, n - len(bass)))
    mix = reverb(mix)
    mix = mix / np.max(np.abs(mix)) * 0.7
    pcm = (np.repeat(mix[:, None], 2, axis=1) * 32767).astype(np.int16)
    os.makedirs("assets", exist_ok=True)
    with wave.open("assets/bgm-pentatonic.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(f"assets/bgm-pentatonic.wav {n / SR:.1f} 秒")
