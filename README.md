# 📊 Excel Video Studio

Công cụ tự động tạo **video hướng dẫn Excel** có **quay màn hình thao tác chuột + giọng đọc tiếng Việt (Edge-TTS) + phụ đề + file Excel mẫu (`.xlsx`)**, chạy trực tiếp trên **Google Colab** với giao diện **Gradio**.

## Cấu trúc dự án
- `app.py` — Giao diện Web Gradio.
- `planner.py` — Kết nối Gemini API để hỏi lại nếu yêu cầu chưa rõ, hoặc sinh kịch bản JSON từng bước.
- `tts_engine.py` — Tạo giọng đọc tiếng Việt (`edge-tts`) và đo thời lượng từng câu bằng `ffprobe`.
- `excel_scene.py` — Dựng giao diện Excel mô phỏng (HTML5) và quay màn hình tự động bằng `Playwright`.
- `video_maker.py` — Ghép video và âm thanh khớp từng mili-giây bằng `FFmpeg`.
- `excel_file_gen.py` — Xuất file `.xlsx` mẫu đi kèm bằng `openpyxl`.
- `code.ipynb` — Notebook chạy trên Google Colab.

## Cách đưa lên GitHub & chạy trên Google Colab
1. Tạo 1 repository mới trên GitHub (ví dụ `excel_video_studio`) và upload toàn bộ các file trong thư mục này lên.
2. Mở `code.ipynb` bằng Google Colab (qua link `https://colab.research.google.com/github/TEN_CUA_BAN/excel_video_studio/blob/main/code.ipynb`).
3. Bỏ dấu `#` ở 2 dòng `git clone` và `%cd` trong Ô 1 (nếu mở trực tiếp từ GitHub).
4. Bấm **Runtime → Run all**, đợi ~1–2 phút cài đặt, rồi bấm vào link `https://xxxx.gradio.live` hiện ra ở Ô 3 để sử dụng!
