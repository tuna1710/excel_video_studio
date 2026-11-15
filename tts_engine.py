import asyncio
import concurrent.futures
import os
import subprocess
from typing import Dict, List
import edge_tts


VOICES = {
    "Nữ miền Nam (Hoài My)": "vi-VN-HoaiMyNeural",
    "Nam miền Bắc (Nam Minh)": "vi-VN-NamMinhNeural",
}


def get_audio_duration(audio_path: str) -> float:
    """Measure exact audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


async def _synthesize_one(text: str, voice: str, out_path: str) -> None:
    clean_text = " ".join((text or "").split()).strip()
    if not clean_text:
        clean_text = "Bước tiếp theo."

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    alt_voice = "vi-VN-NamMinhNeural" if voice != "vi-VN-NamMinhNeural" else "vi-VN-HoaiMyNeural"
    candidates = [voice, alt_voice]

    last_err = None
    for candidate_voice in candidates:
        for attempt in range(2):
            try:
                communicate = edge_tts.Communicate(
                    text=clean_text,
                    voice=candidate_voice,
                    rate="+5%",
                    proxy=proxy,
                )
                await communicate.save(out_path)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    return
            except Exception as exc:
                last_err = exc
                await asyncio.sleep(0.5 * (attempt + 1))

    # Fallback to gTTS if Edge-TTS fails (e.g., NoAudioReceived or rate-limited IP)
    try:
        from gtts import gTTS

        tts = gTTS(text=clean_text, lang="vi", slow=False)
        tts.save(out_path)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return
    except Exception as gtts_exc:
        last_err = gtts_exc

    # Last-resort silent audio so the pipeline never crashes
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", "2.0", "-q:a", "9", "-acodec", "libmp3lame", out_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    except Exception:
        pass

    raise RuntimeError(f"TTS failed: {last_err}")


async def _synthesize_all(steps: List[Dict], voice: str, out_dir: str) -> List[Dict]:
    os.makedirs(out_dir, exist_ok=True)
    enriched = []
    for step in steps:
        audio_path = os.path.join(out_dir, f"step_{step['id']:02d}.mp3")
        await _synthesize_one(step["narration"], voice, audio_path)
        dur = get_audio_duration(audio_path)
        item = dict(step)
        item["audio_path"] = audio_path
        item["duration"] = max(dur + 0.35, 1.5)  # Add 0.35s breathing room between steps
        enriched.append(item)
    return enriched


def generate_step_audios(steps: List[Dict], voice_label: str, out_dir: str) -> List[Dict]:
    """Generate MP3 for each step safely from any sync/async context (Gradio/Colab)."""
    voice = VOICES.get(voice_label, "vi-VN-HoaiMyNeural")

    def _runner():
        return asyncio.run(_synthesize_all(steps, voice, out_dir))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_runner)
        return future.result()
