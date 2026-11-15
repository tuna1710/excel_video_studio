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
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+5%", proxy=proxy)
    await communicate.save(out_path)


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
