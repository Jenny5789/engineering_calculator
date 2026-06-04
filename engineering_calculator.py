import flet as ft
import math
import re

# ── 계산 로직 ────────────────────────────────────────────

SAFE_FUNCTIONS = {
    'sin':       lambda x: math.sin(math.radians(x)),
    'cos':       lambda x: math.cos(math.radians(x)),
    'tan':       lambda x: math.tan(math.radians(x)),
    'asin':      lambda x: math.degrees(math.asin(x)),
    'acos':      lambda x: math.degrees(math.acos(x)),
    'atan':      lambda x: math.degrees(math.atan(x)),
    'sinh':      math.sinh,
    'cosh':      math.cosh,
    'tanh':      math.tanh,
    'log':       math.log10,
    'ln':        math.log,
    'sqrt':      math.sqrt,
    'factorial': math.factorial,
    'abs':       abs,
    'pi':        math.pi,
    'e':         math.e,
}

def preprocess(expr: str) -> str:
    expr = expr.replace("^", "**")
    expr = expr.replace("π", "pi")
    expr = expr.replace("×", "*")
    expr = expr.replace("÷", "/")
    expr = re.sub(r'(\d+)!', r'factorial(\1)', expr)
    expr = re.sub(r'(\d+(\.\d+)?)%', r'(\1/100)', expr)       
    return expr

def check_brackets(expr: str) -> str:
    """괄호 균형 검사 — 문제 없으면 None, 있으면 오류 메시지 반환"""
    count = 0
    for ch in expr:
        if ch == "(":
            count += 1
        elif ch == ")":
            count -= 1
        if count < 0:
            return "Error: 닫는 괄호가 너무 많음"
    if count > 0:
        return "Error: 여는 괄호가 닫히지 않음"
    return None

def calculate(expr: str) -> str:
    try:
        # 괄호 검사 먼저
        bracket_error = check_brackets(expr)
        if bracket_error:
            return bracket_error

        processed = preprocess(expr)
        result = eval(processed, {"__builtins__": {}}, SAFE_FUNCTIONS)
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 10))
    except ZeroDivisionError:
        return "Error: 0으로 나눌 수 없음"
    except ValueError:
        return "Error: 정의되지 않은 값"
    except SyntaxError:
        return "Error: 수식 오류"
    except Exception as ex:
        return f"Error: {str(ex)}"

# ── UI ───────────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "공학용 계산기"
    page.bgcolor = "#111111"
    page.padding  = 20
    page.window.width  = 420
    page.window.height = 750
    page.window.resizable = False
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    expression  = ""
    last_answer = "0"
    cursor_pos  = 0
    history     = []
    history_idx = [-1]
    memory      = 0       # M+ 메모리 저장값
    shift_on    = [False] # SHIFT 상태
    hyp_on      = [False] # hyp 상태

    # ── 디스플레이 ──
    display_line1  = ft.Text("", size=18, color="#aaaaaa",
                              text_align=ft.TextAlign.RIGHT,
                              overflow=ft.TextOverflow.CLIP)
    display_line2  = ft.Text("", size=18, color="#aaaaaa",
                              text_align=ft.TextAlign.RIGHT,
                              overflow=ft.TextOverflow.CLIP)
    display_result = ft.Text("0", size=20, color="#FF8C00",
                              text_align=ft.TextAlign.RIGHT,
                              weight=ft.FontWeight.BOLD)
    # SHIFT/hyp 상태 표시
    status_text = ft.Text("", size=11, color="#00ff99",
                           text_align=ft.TextAlign.LEFT)

    # ── 버튼 생성 ──
    TOTAL_W = 344
    BTN_W   = 64
    BTN_H   = 44
    GAP     = 6


    display_box = ft.Container(
        content=ft.Column(
            controls=[
                status_text,
                ft.Container(content=display_line1, expand=True,
                             alignment=ft.Alignment(1, 0)),
                ft.Container(content=display_line2, expand=True,
                             alignment=ft.Alignment(1, 0)),
                ft.Container(content=display_result, expand=True,
                             alignment=ft.Alignment(1, 0)),
            ],
            spacing=2,
            expand=True,
        ),
        bgcolor="#050510",
        border_radius=8,
        border=ft.Border.all(1, "#444444"),
        padding=ft.Padding(12, 10, 12, 10),
        height=150,
        width=TOTAL_W+70,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )



    def make_btn(label, bgcolor="#2a2a2a", color="#ffffff",
                 width=BTN_W, height=BTN_H):
        return ft.FilledButton(
            content=ft.Text(label, size=12, color=color,
                            text_align=ft.TextAlign.CENTER),
            width=width,
            height=height,
            style=ft.ButtonStyle(
                bgcolor=bgcolor,
                shape=ft.RoundedRectangleBorder(radius=5),
                padding=ft.Padding(0, 0, 0, 0),
                side=ft.BorderSide(width=1, color="#444444"),
            ),
            on_click=btn_click,
        )

    # SHIFT 상태에 따른 버튼 텍스트 매핑
    SHIFT_MAP = {
        "sin": "asin", "cos": "acos", "tan": "atan",
        "√":  "x²",   "ln":  "e^",
        "x²":  "√",    "Abs": "n!",
    }
    # hyp 상태에 따른 버튼 텍스트 매핑
    HYP_MAP = {
        "sin": "sinh", "cos": "cosh", "tan": "tanh",
        "asin": "asinh", "acos": "acosh", "atan": "atanh",
    }

    # 버튼 참조 저장 (SHIFT/hyp 로 텍스트 바꾸기 위해)
    btn_refs = {}

    def make_btn_ref(label, bgcolor="#2a2a2a", color="#ffffff",
                     width=BTN_W, height=BTN_H):
        btn = make_btn(label, bgcolor, color, width, height)
        btn_refs[label] = btn
        return btn

    # ── 클릭 처리 ──
    def btn_click(e):
        nonlocal expression, last_answer, cursor_pos, memory

        label = e.control.content.value

        if label == "AC":
            expression  = ""
            cursor_pos  = 0
            display_line1.value  = ""
            display_line2.value  = ""
            display_result.value = "0"
            shift_on[0] = False
            hyp_on[0]   = False
            update_status()

        elif label == "DEL":
            if cursor_pos > 0:
                expression = expression[:cursor_pos-1] + expression[cursor_pos:]
                cursor_pos -= 1
            update_display()

        elif label == "=":
            result = calculate(expression)
            if result != "Error":
                last_answer = result
                history.append(expression)
                history_idx[0] = len(history)
            display_result.value = result
            update_display()

        elif label == "Ans":
            insert = last_answer
            expression = expression[:cursor_pos] + insert + expression[cursor_pos:]
            cursor_pos += len(insert)
            update_display()

        elif label == "◀":
            if cursor_pos > 0:
                cursor_pos -= 1
            update_display()

        elif label == "▶":
            if cursor_pos < len(expression):
                cursor_pos += 1
            update_display()

        elif label == "▲":
            if history and history_idx[0] > 0:
                history_idx[0] -= 1
                expression = history[history_idx[0]]
                cursor_pos = len(expression)
            update_display()

        elif label == "▼":
            if history_idx[0] < len(history) - 1:
                history_idx[0] += 1
                expression = history[history_idx[0]]
                cursor_pos = len(expression)
            update_display()

        elif label == "ON/OFF":
            import sys
            sys.exit()

        elif label == "SHIFT":
            shift_on[0] = not shift_on[0]
            if shift_on[0]:
                hyp_on[0] = False  # SHIFT 켜면 hyp 끄기
            update_btn_labels()
            update_status()

        elif label == "hyp":
            hyp_on[0] = not hyp_on[0]
            if hyp_on[0]:
                shift_on[0] = False  # hyp 켜면 SHIFT 끄기
            update_btn_labels()
            update_status()

        elif label == "RCL":
            # 메모리 불러오기
            insert = str(memory)
            expression = expression[:cursor_pos] + insert + expression[cursor_pos:]
            cursor_pos += len(insert)
            update_display()

        elif label == "M+":
            # 현재 결과를 메모리에 저장
            result = calculate(expression)
            if result != "Error" and not result.startswith("Error"):
                memory = float(result)
                display_result.value = f"M={memory}"
                update_status()
                page.update()
                return

        else:
            insert_map = {
                "sin":   "sin(",  "cos":   "cos(",  "tan":   "tan(",
                "asin":  "asin(", "acos":  "acos(", "atan":  "atan(",
                "sinh":  "sinh(", "cosh":  "cosh(", "tanh":  "tanh(",
                "asinh": "asinh(","acosh": "acosh(","atanh": "atanh(",
                "log":   "log(",  "ln":    "ln(",  
                "%":     "%",  "e^":    "e^(",
                "√":     "sqrt(", "x²":    "^2",
                "x³":    "^3",    "xⁿ":    "^",
                "x⁻¹":   "^(-1)", "x10ˣ":  "*10^",
                "Abs":   "abs(",  "n!":    "!",
                "(-)":   "(-",    "π":     "pi",
                "×":     "×",     "÷":     "÷",
            }
            insert = insert_map.get(label, label)
            expression = expression[:cursor_pos] + insert + expression[cursor_pos:]
            cursor_pos += len(insert)

            # SHIFT/hyp 사용 후 자동 해제
            if shift_on[0] or hyp_on[0]:
                shift_on[0] = False
                hyp_on[0]   = False
                update_btn_labels()
                update_status()

            update_display()

        page.update()

    def update_btn_labels():
        """SHIFT/hyp 상태에 따라 버튼 텍스트 변경"""
        targets = ["sin", "cos", "tan", "log", "√", "ln", "x²", "Abs"]
        for original in targets:
            if original not in btn_refs:
                continue
            btn = btn_refs[original]
            if shift_on[0] and original in SHIFT_MAP:
                btn.content.value = SHIFT_MAP[original]
            elif hyp_on[0]:
                current = btn.content.value
                if current in HYP_MAP:
                    btn.content.value = HYP_MAP[current]
                elif original in HYP_MAP:
                    btn.content.value = HYP_MAP[original]
            else:
                btn.content.value = original
        page.update()


    def update_status():
        """상태바 텍스트 업데이트"""
        parts = []
        if shift_on[0]:
            parts.append("SHIFT")
        if hyp_on[0]:
            parts.append("HYP")
        if memory != 0:
            parts.append(f"M={memory}")
        status_text.value = "  ".join(parts)

    def update_display():
        display_expr = expression[:cursor_pos] + "|" + expression[cursor_pos:]
        max_len = 30
        if len(display_expr) <= max_len:
            display_line1.value = display_expr
            display_line2.value = ""
        else:
            display_line1.value = display_expr[:max_len]
            display_line2.value = display_expr[max_len:max_len * 2]

    # ── 색상 ──
    C_GRAY  = "#2a2a2a"
    C_NUM   = "#3d3d3d"
    C_NAV   = "#2a4a3a"
    C_ON    = "#5a2a2a"
    C_DEL   = "#6b3a2a"
    C_EQ    = "#2a5a2a"

    NAV_W = (TOTAL_W - GAP * 4) // 5

    rows = [
        # 방향키 행
        [make_btn("◀",      C_NAV, width=NAV_W),
         make_btn("▲",      C_NAV, width=NAV_W),
         make_btn("▼",      C_NAV, width=NAV_W),
         make_btn("▶",      C_NAV, width=NAV_W),
         make_btn("ON/OFF", C_ON,  width=NAV_W)],
        # 함수 행1
        [make_btn("SHIFT", C_GRAY), make_btn("(", C_GRAY),
         make_btn(")",     C_GRAY), make_btn_ref("Abs"),
         make_btn("xⁿ",   C_GRAY)],
        # 함수 행2
        [make_btn_ref("x²"),  make_btn("x³",  C_GRAY),
         make_btn("x⁻¹", C_GRAY), make_btn_ref("√"),
         make_btn("(-)", C_GRAY)],
        # 함수 행3
        [make_btn_ref("log"),  make_btn_ref("ln"),
         make_btn("%", C_GRAY), make_btn("hyp", C_GRAY),
         make_btn("RCL",  C_GRAY)],
        # 함수 행4
        [make_btn_ref("sin"), make_btn_ref("cos"),
         make_btn_ref("tan"), make_btn("π",  C_GRAY),
         make_btn("M+",  C_GRAY)],
        # 숫자 행1
        [make_btn("7", C_NUM), make_btn("8",   C_NUM),
         make_btn("9", C_NUM), make_btn("DEL", C_DEL),
         make_btn("AC", C_DEL)],
        # 숫자 행2
        [make_btn("4", C_NUM), make_btn("5", C_NUM),
         make_btn("6", C_NUM), make_btn("×", C_GRAY),
         make_btn("÷", C_GRAY)],
        # 숫자 행3
        [make_btn("1", C_NUM), make_btn("2", C_NUM),
         make_btn("3", C_NUM), make_btn("+", C_GRAY),
         make_btn("-", C_GRAY)],
        # 숫자 행4
        [make_btn("0",    C_NUM), make_btn(".",    C_NUM),
         make_btn("x10ˣ", C_GRAY), make_btn("Ans",  C_GRAY),
         make_btn("=",    C_EQ)],
    ]

    button_grid = ft.Column(
        controls=[
            ft.Row(controls=r, spacing=GAP,
                   alignment=ft.MainAxisAlignment.CENTER)
            for r in rows
        ],
        spacing=GAP,
    )

    calculator_case = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("공학용 계산기", size=15, color="#888888",
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD),
                display_box,
                button_grid
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="#0d0d1a",
        border_radius=16,
        padding=ft.Padding(9, 14, 20, 14),
        border=ft.Border.all(2, "#444466"),
        width=TOTAL_W + 50,
    )

    page.add(
        ft.Column(
            controls=[calculator_case],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )
    update_display()
    page.update()

ft.run(main)
