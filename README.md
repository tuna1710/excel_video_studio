# 📊 Excel Video Studio

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tuna1710/excel_video_studio/blob/main/code.ipynb)

Công cụ tự động tạo **video hướng dẫn Excel** có **quay màn hình thao tác chuột + giọng đọc tiếng Việt (Edge-TTS) + phụ đề + file Excel mẫu (`.xlsx`)**, chạy trực tiếp trên **Google Colab** với giao diện **Gradio**.

## Cấu trúc dự án
- `app.py` — Giao diện Web Gradio.
- `planner.py` — Kết nối Gemini API để hỏi lại nếu yêu cầu chưa rõ, hoặc sinh kịch bản JSON từng bước.
- `tts_engine.py` — Tạo giọng đọc tiếng Việt (`edge-tts`) và đo thời lượng từng câu bằng `ffprobe`.
- `excel_scene.py` — Dựng giao diện Excel mô phỏng (HTML5) và quay màn hình tự động bằng `Playwright`.
- `video_maker.py` — Ghép video và âm thanh khớp từng mili-giây bằng `FFmpeg`.
- `excel_file_gen.py` — Xuất file `.xlsx` mẫu đi kèm bằng `openpyxl`.
- `code.ipynb` — Notebook chạy trên Google Colab.

## Cách chạy trên Google Colab
1. Bấm vào nút **Open in Colab** ở trên (hoặc mở link: `https://colab.research.google.com/github/tuna1710/excel_video_studio/blob/main/code.ipynb`).
2. Bấm **Runtime → Run all**, đợi ~1–2 phút cài đặt, rồi bấm vào link `https://xxxx.gradio.live` hiện ra ở Bước 3 để sử dụng!
