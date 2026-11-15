import json
import os
import tempfile
import time
import gradio as gr

from planner import analyze_request, get_demo_plan
from tts_engine import VOICES, generate_step_audios
from excel_scene import record_excel_video
from excel_file_gen import build_sample_xlsx
from video_maker import build_final_mp4


OUTPUT_BASE = os.path.join(os.getcwd(), "outputs")
os.makedirs(OUTPUT_BASE, exist_ok=True)


def run_video_pipeline(
    plan: dict,
    aspect_ratio: str,
    voice_label: str,
    show_subtitles: bool,
):
    """Execute TTS -> Playwright Screen Recording -> FFmpeg Mux -> Sample XLSX."""
    job_dir = os.path.join(OUTPUT_BASE, f"job_{int(time.time())}")
    os.makedirs(job_dir, exist_ok=True)

    steps = plan.get("steps", [])
    steps_with_audio = generate_step_audios(steps, voice_label, os.path.join(job_dir, "audio"))

    raw_video, start_times = record_excel_video(
        plan=plan,
        steps_with_audio=steps_with_audio,
        aspect_ratio=aspect_ratio,
        show_subtitles=show_subtitles,
        out_dir=os.path.join(job_dir, "scene"),
    )

    out_mp4 = os.path.join(job_dir, "huong_dan_excel.mp4")
    build_final_mp4(raw_video, steps_with_audio, start_times, out_mp4)

    out_xlsx = os.path.join(job_dir, f"{plan.get('sheet_name', 'Mau_Excel')}.xlsx")
    build_sample_xlsx(plan, out_xlsx)

    plan_pretty = json.dumps(plan, ensure_ascii=False, indent=2)
    return out_mp4, out_xlsx, plan_pretty


def handle_chat_and_generate(
    user_msg: str,
    api_key: str,
    aspect_ratio: str,
    voice_label: str,
    show_subtitles: bool,
    chat_display: list,
    api_history: list,
):
    if not user_msg or not user_msg.strip():
        return chat_display, api_history, "", None, None, None, "⚠️ Vui lòng nhập yêu cầu."

    if not api_key or not api_key.strip():
        bot_reply = (
            "⚠️ Bạn chưa nhập **Gemini API Key**. "
            "Hãy dán API Key vào ô phía trên, hoặc bấm nút **Chạy thử mẫu (không cần API Key)** ở bên dưới nhé!"
        )
        chat_display = (chat_display or []) + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": bot_reply},
        ]
        return chat_display, api_history, "", None, None, None, "⚠️ Thiếu Gemini API Key."

    try:
        res = analyze_request(api_key, api_history, user_msg)
    except Exception as e:
        err_msg = f"❌ Lỗi gọi Gemini API: {e}"
        chat_display = (chat_display or []) + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": err_msg},
        ]
        return chat_display, api_history, "", None, None, None, err_msg

    if res.get("status") == "need_clarification":
        question = res.get("clarification_question", "Bạn có thể nói rõ hơn loại biểu đồ/hàm và dữ liệu mẫu muốn dùng không?")
        chat_display = (chat_display or []) + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": question},
        ]
        api_history = api_history + [
            {"role": "user", "content": user_msg},
            {"role": "model", "content": question},
        ]
        return chat_display, api_history, "", None, None, None, "💬 AI đang hỏi thêm để làm rõ yêu cầu..."

    plan = res.get("plan", {})
    title = plan.get("title", "Video hướng dẫn Excel")
    steps_summary = "\n".join(f"- Bước {s['id']}: {s['narration']}" for s in plan.get("steps", []))
    bot_reply = f"✅ Đã rõ yêu cầu! Đang tạo video: **{title}**\n\n**Kịch bản:**\n{steps_summary}"

    chat_display = (chat_display or []) + [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": bot_reply},
    ]
    api_history = api_history + [
        {"role": "user", "content": user_msg},
        {"role": "model", "content": bot_reply},
    ]

    try:
        out_mp4, out_xlsx, plan_pretty = run_video_pipeline(
            plan, aspect_ratio, voice_label, show_subtitles
        )
        status = f"🎉 Hoàn thành! Video **{title}** đã sẵn sàng để tải về."
        return chat_display, api_history, "", out_mp4, out_xlsx, plan_pretty, status
    except Exception as e:
        err_msg = f"❌ Lỗi khi dựng video: {e}"
        return chat_display, api_history, "", None, None, None, err_msg


def handle_demo(topic: str, aspect_ratio: str, voice_label: str, show_subtitles: bool, chat_display: list):
    res = get_demo_plan(topic)
    plan = res["plan"]
    title = plan["title"]
    chat_display = (chat_display or []) + [
        {"role": "user", "content": f"[Chạy thử mẫu] {title}"},
        {"role": "assistant", "content": "✅ Đang dựng video mẫu tự động (không cần API Key)..."},
    ]
    try:
        out_mp4, out_xlsx, plan_pretty = run_video_pipeline(
            plan, aspect_ratio, voice_label, show_subtitles
        )
        status = f"🎉 Hoàn thành video mẫu: **{title}**"
        return chat_display, out_mp4, out_xlsx, plan_pretty, status
    except Exception as e:
        return chat_display, None, None, None, f"❌ Lỗi dựng video: {e}"


with gr.Blocks(title="Excel Video Studio", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 📊 Excel Video Studio (Auto Screen Record + TTS)
        Nhập yêu cầu (ví dụ: *"Hướng dẫn tôi vẽ biểu đồ cột doanh thu 6 tháng"*). Nếu chưa rõ, AI sẽ hỏi lại; nếu rõ rồi, hệ thống tự quay màn hình & lồng tiếng TTS xuất ra `.mp4` + file `.xlsx` mẫu!
        """
    )

    api_history_state = gr.State([])

    with gr.Row():
        with gr.Column(scale=5):
            api_key_box = gr.Textbox(
                label="🔑 Gemini API Key (bắt buộc cho yêu cầu tự do)",
                placeholder="Dán AIza... vào đây (có thể bỏ trống nếu dùng nút Chạy thử mẫu)",
                type="password",
            )
            chatbot = gr.Chatbot(label="💬 Hội thoại với AI", height=320)
            user_input = gr.Textbox(
                label="Nhập yêu cầu của bạn",
                placeholder="Ví dụ: Hướng dẫn tôi vẽ biểu đồ cột doanh thu 6 tháng",
                lines=2,
            )
            with gr.Row():
                aspect_dd = gr.Dropdown(
                    choices=["9:16 (TikTok / Shorts)", "16:9 (YouTube)"],
                    value="9:16 (TikTok / Shorts)",
                    label="📐 Khung hình",
                )
                voice_dd = gr.Dropdown(
                    choices=list(VOICES.keys()),
                    value=list(VOICES.keys())[0],
                    label="🎙️ Giọng đọc TTS",
                )
            sub_chk = gr.Checkbox(value=True, label="Hiển thị phụ đề trên video")

            send_btn = gr.Button("🎬 Gửi yêu cầu & Tạo Video", variant="primary")

            gr.Markdown("### ⚡ Chạy thử nhanh (Không cần API Key)")
            with gr.Row():
                demo_chart_btn = gr.Button("📊 Mẫu: Vẽ Biểu đồ Cột")
                demo_sum_btn = gr.Button("∑ Mẫu: Hàm SUM")

        with gr.Column(scale=5):
            status_md = gr.Markdown("⏳ Sẵn sàng.")
            video_out = gr.Video(label="🎥 Video kết quả (.mp4)")
            xlsx_out = gr.File(label="📁 File Excel mẫu đi kèm (.xlsx)")
            with gr.Accordion("📄 Xem kịch bản JSON chi tiết", open=False):
                json_out = gr.Code(language="json", label="Plan JSON")

    send_btn.click(
        fn=handle_chat_and_generate,
        inputs=[user_input, api_key_box, aspect_dd, voice_dd, sub_chk, chatbot, api_history_state],
        outputs=[chatbot, api_history_state, user_input, video_out, xlsx_out, json_out, status_md],
    )
    user_input.submit(
        fn=handle_chat_and_generate,
        inputs=[user_input, api_key_box, aspect_dd, voice_dd, sub_chk, chatbot, api_history_state],
        outputs=[chatbot, api_history_state, user_input, video_out, xlsx_out, json_out, status_md],
    )

    demo_chart_btn.click(
        fn=lambda ar, vl, sc, ch: handle_demo("chart", ar, vl, sc, ch),
        inputs=[aspect_dd, voice_dd, sub_chk, chatbot],
        outputs=[chatbot, video_out, xlsx_out, json_out, status_md],
    )
    demo_sum_btn.click(
        fn=lambda ar, vl, sc, ch: handle_demo("formula", ar, vl, sc, ch),
        inputs=[aspect_dd, voice_dd, sub_chk, chatbot],
        outputs=[chatbot, video_out, xlsx_out, json_out, status_md],
    )


if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")
