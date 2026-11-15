import os
from typing import Any, Dict
import openpyxl
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


def build_sample_xlsx(plan: Dict[str, Any], out_path: str) -> str:
    """Create a clean, formatted Excel file matching the video tutorial plan."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (plan.get("sheet_name") or "Sheet1")[:31]

    headers = plan.get("headers", [])
    rows = plan.get("rows", [])

    header_fill = PatternFill(start_color="217346", end_color="217346", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=11)
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Write headers
    for c_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=c_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    ws.row_dimensions[1].height = 24

    # Write rows
    for r_idx, row in enumerate(rows, start=2):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = body_font
            cell.border = border
            if isinstance(val, (int, float)):
                cell.number_format = "#,##0"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[r_idx].height = 20

    # Apply any type_formula step
    for step in plan.get("steps", []):
        if step.get("action") == "type_formula" and step.get("target") and step.get("formula"):
            target = step["target"].split(":")[0]
            ws[target] = step["formula"]
            ws[target].font = Font(name="Calibri", size=11, bold=True, color="1F4E78")

    # Auto-fit column widths
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = max(max_len + 5, 14)

    # Add chart if specified
    chart_cfg = plan.get("chart")
    if chart_cfg and rows:
        ctype = chart_cfg.get("type", "bar")
        if ctype == "line":
            chart = LineChart()
        elif ctype == "pie":
            chart = PieChart()
        else:
            chart = BarChart()
            chart.type = "col"

        chart.title = chart_cfg.get("title", plan.get("title", "Chart"))
        chart.style = 10
        y_col = int(chart_cfg.get("y_col", 1)) + 1
        x_col = int(chart_cfg.get("x_col", 0)) + 1
        max_row = len(rows) + 1

        data = Reference(ws, min_col=y_col, min_row=1, max_row=max_row)
        cats = Reference(ws, min_col=x_col, min_row=2, max_row=max_row)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.width = 16
        chart.height = 10
        ws.add_chart(chart, f"{openpyxl.utils.get_column_letter(len(headers) + 2)}2")

    wb.save(out_path)
    return out_path
