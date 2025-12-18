
"""
Few-shot examples for Math/STEM prompting.
Each example includes a question and a 5-step detailed solution.
"""

MATH_EXAMPLES = [
    {
        "type": "math",
        "question": "Giải phương trình $x^2 - 5x + 6 = 0$.",
        "answer": r"""Bước 1: IDENTIFY (Xác định)
- Phương trình bậc hai dạng $ax^2 + bx + c = 0$
- Hệ số: $a=1, b=-5, c=6$
- Yêu cầu: Tìm nghiệm $x$

Bước 2: ANALYZE (Phân tích)
- Sử dụng công thức nghiệm (biệt thức $\Delta$) hoặc phân tích thành nhân tử.
- Công thức $\Delta = b^2 - 4ac$.
- Nếu $\Delta > 0 \Rightarrow$ 2 nghiệm phân biệt.

Bước 3: SOLVE (Giải từng bước)
- Tính $\Delta = (-5)^2 - 4(1)(6) = 25 - 24 = 1$
- Vì $\Delta = 1 > 0$, phương trình có 2 nghiệm:
  $x_1 = \\frac{-b + \\sqrt{\\Delta}}{2a} = \\frac{5 + 1}{2} = 3$
  $x_2 = \\frac{-b - \\sqrt{\\Delta}}{2a} = \\frac{5 - 1}{2} = 2$

Bước 4: VERIFY (Kiểm tra)
- $x=3: 3^2 - 5(3) + 6 = 9 - 15 + 6 = 0$ (Đúng)
- $x=2: 2^2 - 5(2) + 6 = 4 - 10 + 6 = 0$ (Đúng)

Bước 5: CONCLUDE (Kết luận)
{"answer": "x = 2, x = 3"}"""
    },
    {
        "type": "math",
        "question": "Tìm nguyên hàm của hàm số $f(x) = 3x^2 + \\sin(x)$.",
        "answer": r"""Bước 1: IDENTIFY (Xác định)
- Hàm số: $f(x) = 3x^2 + \\sin(x)$
- Yêu cầu: Tìm họ nguyên hàm $\\int f(x) dx$

Bước 2: ANALYZE (Phân tích)
- Tính chất nguyên hàm của tổng: $\\int (u+v) = \\int u + \\int v$
- Công thức cơ bản: $\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$
- Công thức lượng giác: $\\int \\sin(x) dx = -\\cos(x) + C$

Bước 3: SOLVE (Giải từng bước)
- $\\int 3x^2 dx = 3 \\cdot \\frac{x^3}{3} = x^3$
- $\\int \\sin(x) dx = -\\cos(x)$
- Kết hợp lại: $\\int (3x^2 + \\sin(x)) dx = x^3 - \\cos(x) + C$

Bước 4: VERIFY (Kiểm tra)
- Đạo hàm kết quả: $(x^3 - \\cos(x))' = 3x^2 - (-\\sin(x)) = 3x^2 + \\sin(x)$
- Khớp với hàm ban đầu.

Bước 5: CONCLUDE (Kết luận)
{"answer": "x^3 - \\\\cos(x) + C"}"""
    }
]

PHYSICS_EXAMPLES = [
    {
        "type": "physics",
        "question": "Một vật rơi tự do từ độ cao $h=20m$. Tính thời gian chạm đất. Lấy $g=10m/s^2$.",
        "answer": r"""Bước 1: IDENTIFY (Xác định)
- Chuyển động: Rơi tự do (vận tốc đầu $v_0 = 0$)
- Độ cao $h = 20m$
- Gia tốc trọng trường $g = 10m/s^2$
- Yêu cầu: Tính thời gian $t$

Bước 2: ANALYZE (Phân tích)
- Công thức đường đi rơi tự do: $h = \\frac{1}{2}gt^2$
- Suy ra công thức tính $t$: $t = \\sqrt{\\frac{2h}{g}}$

Bước 3: SOLVE (Giải từng bước)
- Thay số vào công thức:
  $t = \\sqrt{\\frac{2 \\cdot 20}{10}}$
  $t = \\sqrt{\\frac{40}{10}} = \\sqrt{4}$
  $t = 2$ (giây)

Bước 4: VERIFY (Kiểm tra)
- Nếu $t=2s$, quãng đường đi được: $0.5 \\cdot 10 \\cdot 2^2 = 5 \\cdot 4 = 20m$ (Khớp đề bài)
- Đơn vị thời gian là giây (s).

Bước 5: CONCLUDE (Kết luận)
{"answer": "2 s"}"""
    }
]

CHEMISTRY_EXAMPLES = [
    {
        "type": "chemistry",
        "question": "Đốt cháy hoàn toàn 0,1 mol CH4 cần bao nhiêu lít O2 (đktc)?",
        "answer": r"""Bước 1: IDENTIFY (Xác định)
- Chất phản ứng: Methane ($CH_4$), Oxy ($O_2$)
- Số mol $CH_4$: $n = 0.1$ mol
- Yêu cầu: Tính thể tích $O_2$ (đktc)

Bước 2: ANALYZE (Phân tích)
- Viết phương trình phản ứng cháy.
- Tính tỉ lệ mol giữa $CH_4$ và $O_2$.
- Tính thể tích khí đktc: $V = n \\cdot 22.4$

Bước 3: SOLVE (Giải từng bước)
- Phương trình: $CH_4 + 2O_2 \\rightarrow CO_2 + 2H_2O$
- Tỉ lệ: 1 mol $CH_4$ cần 2 mol $O_2$
- Số mol $O_2$ cần dùng: $n_{O_2} = 2 \\cdot n_{CH_4} = 2 \\cdot 0.1 = 0.2$ mol
- Thể tích $O_2$: $V = 0.2 \\cdot 22.4 = 4.48$ lít

Bước 4: VERIFY (Kiểm tra)
- Cân bằng phương trình: 1C, 4H, 4O (Đúng)
- Tính toán: $0.2 \\times 22.4 = 4.48$ (Đúng)

Bước 5: CONCLUDE (Kết luận)
{"answer": "4.48 lít"}"""
    }
]

# Map problem types to examples
EXAMPLE_MAP = {
    "math": MATH_EXAMPLES,
    "calculus": MATH_EXAMPLES,
    "statistics": MATH_EXAMPLES,
    "physics": PHYSICS_EXAMPLES,
    "chemistry": CHEMISTRY_EXAMPLES,
}
