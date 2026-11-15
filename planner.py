import json
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types


SYSTEM_PROMPT = """Bạn là trợ lý chuyên lập kịch bản video hướng dẫn Excel ngắn gọn, trực quan bằng tiếng Việt.

Nhiệm vụ của bạn khi nhận yêu cầu từ người dùng:
1. Kiểm tra xem yêu cầu ĐÃ RÕ để dựng video hướng dẫn chưa.
   - Yêu cầu được coi là CHƯA RÕ nếu quá chung chung, ví dụ: "hướng dẫn tôi vẽ biểu đồ", "chỉ tôi dùng hàm", "làm bảng tính" mà chưa rõ loại biểu đồ/hàm cụ thể hoặc chủ đề dữ liệu.
   - Nếu CHƯA RÕ: trả về JSON với "status": "need_clarification" và "clarification_question" chứa 2-3 câu hỏi ngắn gọn để làm rõ (ví dụ: loại biểu đồ cột/tròn/đường? dữ liệu mẫu về doanh thu hay chi tiêu?).
   - Nếu ĐÃ RÕ (người dùng đã nói rõ loại biểu đồ/hàm/tính năng hoặc đã trả lời câu hỏi làm rõ): trả về JSON với "status": "ready" và đầy đủ "plan".

2. Cấu trúc "plan" khi status == "ready":
   - "title": Tiêu đề video ngắn gọn.
   - "sheet_name": Tên sheet Excel (không dấu, không khoảng trắng, ví dụ "DoanhThu").
   - "headers": Danh sách tên cột (tối đa 4 cột cho gọn đẹp), ví dụ ["Tháng", "Doanh thu", "Chi phí"].
   - "rows": Dữ liệu 4-6 dòng (số liệu thực tế, dễ hiểu).
   - "chart": (Nếu là bài hướng dẫn vẽ biểu đồ, ngược lại để null)
     {
       "type": "bar" | "line" | "pie",
       "title": "Tiêu đề biểu đồ",
       "x_col": 0,
       "y_col": 1
     }
   - "steps": Danh sách 4-7 bước thao tác tuần tự. Mỗi bước có:
     - "id": số thứ tự (1, 2, 3...)
     - "action": Một trong các giá trị:
       * "select_range": Bôi đen vùng dữ liệu (target là "A1:B6" hoặc tương ứng).
       * "click_tab": Bấm vào tab trên thanh công cụ (target là "Home", "Insert", "Formulas", hoặc "Data").
       * "click_button": Bấm nút chức năng trên Ribbon (target là tên nút, ví dụ "Column Chart", "Pie Chart", "Line Chart", "AutoSum", "Filter", "Format").
       * "type_formula": Gõ công thức vào 1 ô (target là ô đích ví dụ "C2", "formula" là công thức ví dụ "=B2*10%", "result_value" là kết quả hiển thị ví dụ "15").
       * "show_chart": Hiển thị và hoàn thiện biểu đồ trên màn hình (target là tiêu đề biểu đồ).
       * "highlight_cells": Nhấn mạnh vùng kết quả (target là vùng ô ví dụ "C2:C6").
       * "finish": Tổng kết ngắn gọn (target là "").
     - "target": Chuỗi mục tiêu của hành động.
     - "formula": Chuỗi công thức (chỉ dùng khi action == "type_formula", còn lại để "").
     - "result_value": Giá trị hiển thị sau khi Enter (chỉ dùng khi action == "type_formula", còn lại để "").
     - "narration": Câu thoại tiếng Việt tự nhiên, rõ ràng để đọc TTS khớp đúng với hành động đang hiển thị trên màn hình (khoảng 8-18 từ mỗi bước).
     - "subtitle": Phụ đề ngắn gọn hiển thị ở cuối video.

LUÔN trả về đúng định dạng JSON hợp lệ, không kèm markdown ```json.
"""


def analyze_request(
    api_key: str,
    chat_history: List[Dict[str, str]],
    user_message: str,
) -> Dict[str, Any]:
    """Call Gemini to either ask clarifying questions or return a structured video plan."""
    client = genai.Client(api_key=api_key.strip())

    contents: List[types.Content] = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json\n", "", 1).strip()
    return json.loads(text)


def get_demo_plan(topic: str = "chart") -> Dict[str, Any]:
    """Return a built-in demo plan (works without any API key)."""
    if topic == "formula":
        return {
            "status": "ready",
            "plan": {
                "title": "Cách dùng hàm SUM tính tổng doanh thu trong Excel",
                "sheet_name": "DoanhThu",
                "headers": ["Sản phẩm", "Số lượng", "Doanh thu (Tr)"],
                "rows": [
                    ["Áo thun", 45, 12],
                    ["Quần jean", 30, 18],
                    ["Giày thể thao", 25, 25],
                    ["Túi xách", 18, 15],
                    ["Tổng cộng", "", ""],
                ],
                "chart": None,
                "steps": [
                    {
                        "id": 1,
                        "action": "highlight_cells",
                        "target": "A1:C5",
                        "formula": "",
                        "result_value": "",
                        "narration": "Hôm nay mình sẽ hướng dẫn bạn dùng hàm SUM để tính tổng doanh thu cực nhanh.",
                        "subtitle": "Hướng dẫn dùng hàm SUM trong Excel",
                    },
                    {
                        "id": 2,
                        "action": "select_range",
                        "target": "C6",
                        "formula": "",
                        "result_value": "",
                        "narration": "Đầu tiên, bạn bấm chọn vào ô C6 nơi cần hiển thị kết quả tổng.",
                        "subtitle": "Bước 1: Chọn ô kết quả C6",
                    },
                    {
                        "id": 3,
                        "action": "click_tab",
                        "target": "Home",
                        "formula": "",
                        "result_value": "",
                        "narration": "Ở thẻ Home trên thanh công cụ, bạn nhìn sang góc phải.",
                        "subtitle": "Bước 2: Vào tab Home",
                    },
                    {
                        "id": 4,
                        "action": "type_formula",
                        "target": "C6",
                        "formula": "=SUM(C2:C5)",
                        "result_value": "70",
                        "narration": "Gõ công thức bằng S U M mở ngoặc C2 hai chấm C5 đóng ngoặc rồi bấm Enter.",
                        "subtitle": "Bước 3: Nhập =SUM(C2:C5) và Enter",
                    },
                    {
                        "id": 5,
                        "action": "highlight_cells",
                        "target": "C6",
                        "formula": "",
                        "result_value": "",
                        "narration": "Vậy là tổng doanh thu 70 triệu đã được tính tự động chỉ trong vài giây!",
                        "subtitle": "Hoàn thành! Kết quả tự động: 70",
                    },
                ],
            },
        }

    # Default: Bar/Column chart demo
    return {
        "status": "ready",
        "plan": {
            "title": "Cách vẽ biểu đồ cột doanh thu 6 tháng trong Excel",
            "sheet_name": "DoanhThu",
            "headers": ["Tháng", "Doanh thu (Tr)"],
            "rows": [
                ["Tháng 1", 120],
                ["Tháng 2", 145],
                ["Tháng 3", 130],
                ["Tháng 4", 180],
                ["Tháng 5", 210],
                ["Tháng 6", 240],
            ],
            "chart": {
                "type": "bar",
                "title": "Doanh thu 6 tháng đầu năm",
                "x_col": 0,
                "y_col": 1,
            },
            "steps": [
                {
                    "id": 1,
                    "action": "select_range",
                    "target": "A1:B7",
                    "formula": "",
                    "result_value": "",
                    "narration": "Đầu tiên, bạn bôi đen toàn bộ bảng dữ liệu từ ô A1 đến B7.",
                    "subtitle": "Bước 1: Bôi đen vùng dữ liệu A1:B7",
                },
                {
                    "id": 2,
                    "action": "click_tab",
                    "target": "Insert",
                    "formula": "",
                    "result_value": "",
                    "narration": "Tiếp theo, chọn tab Insert trên thanh công cụ phía trên.",
                    "subtitle": "Bước 2: Chọn tab Insert",
                },
                {
                    "id": 3,
                    "action": "click_button",
                    "target": "Column Chart",
                    "formula": "",
                    "result_value": "",
                    "narration": "Trong mục Charts, bạn bấm chọn biểu tượng biểu đồ cột.",
                    "subtitle": "Bước 3: Chọn mục Column Chart",
                },
                {
                    "id": 4,
                    "action": "show_chart",
                    "target": "Doanh thu 6 tháng đầu năm",
                    "formula": "",
                    "result_value": "",
                    "narration": "Ngay lập tức biểu đồ cột doanh thu 6 tháng sẽ hiện ra trực quan và đẹp mắt.",
                    "subtitle": "Bước 4: Biểu đồ hoàn chỉnh",
                },
                {
                    "id": 5,
                    "action": "finish",
                    "target": "",
                    "formula": "",
                    "result_value": "",
                    "narration": "Chúc bạn áp dụng thành công, nhớ theo dõi kênh để xem thêm nhiều mẹo Excel hay nhé!",
                    "subtitle": "Theo dõi kênh để học thêm mẹo Excel!",
                },
            ],
        },
    }
