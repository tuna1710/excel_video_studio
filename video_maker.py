import os
import subprocess
from typing import Any, Dict, List


def build_final_mp4(
    raw_video_path: str,
    steps_with_audio: List[Dict[str, Any]],
    step_start_times: List[float],
    out_mp4_path: str,
) -> str:
    """Mux raw video with precisely delayed step MP3 audios into an H.264 MP4."""
    os.makedirs(os.path.dirname(out_mp4_path), exist_ok=True)

    cmd: List[str] = ["ffmpeg", "-y", "-i", raw_video_path]
    filter_parts: List[str] = []
    mix_inputs: List[str] = []

    for idx, (step, start_sec) in enumerate(zip(steps_with_audio, step_start_times)):
        cmd.extend(["-i", step["audio_path"]])
        input_idx = idx + 1  # 0 is raw_video_path
        delay_ms = max(int((start_sec + 0.4) * 1000), 0)
        label = f"a{idx}"
        filter_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[{label}]")
        mix_inputs.append(f"[{label}]")

    if len(mix_inputs) == 1:
        filter_complex = f"{filter_parts[0]};[a0]anull[aout]"
    else:
        joined = "".join(mix_inputs)
        filter_complex = (
            ";".join(filter_parts)
            + f";{joined}amix=inputs={len(mix_inputs)}:duration=longest:dropout_transition=0:normalize=0[aout]"
        )

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_mp4_path,
    ])

    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_mp4_path
