# 손글씨 숫자/기호(+, -, *, /, x, X, ÷, =) 인식해서
# 마지막에 '=' 를 그리면 자동 계산하는 간단 예제
# 필요 라이브러리: pillow, scikit-learn, numpy
# pip install pillow scikit-learn numpy

import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.neighbors import KNeighborsClassifier

CANVAS_SIZE = 200       # 그리는 영역 크기
IMG_SIZE = 28           # 인식용 축소 크기

# ----------------- 글자 인식용 간단 KNN 모델 생성 -----------------

def generate_training_data():
    """
    폰트로 숫자/기호 이미지를 여러 번 그려서 KNN 학습 데이터 생성
    glyph : 실제 화면에 그릴 문자
    label : 인식 결과로 쓸 문자
      - 'x', 'X' -> '*' 로 인식
      - '÷'      -> '/' 로 인식
    """
    # (glyph, label) 쌍
    pairs = []
    for d in range(10):
        pairs.append((str(d), str(d)))
    pairs += [
        ('+', '+'),
        ('-', '-'),
        ('*', '*'),
        ('/', '/'),
        ('x', '*'),
        ('X', '*'),
        ('÷', '/'),
        ('=', '='),
    ]

    X = []
    y = []

    # 사용할 폰트 (없으면 기본폰트로)
    try:
        # 시스템에 따라 없는 경우도 있으니 예외 처리
        font_paths = [
            "arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ]
        fonts = []
        for p in font_paths:
            try:
                fonts.append(ImageFont.truetype(p, 28))
            except:
                pass
        if not fonts:
            fonts = [ImageFont.load_default()]
    except:
        fonts = [ImageFont.load_default()]

    # 여러 폰트, 여러 크기로 데이터 생성
    for glyph, label in pairs:
        for font in fonts:
            for size in [24, 28, 32]:
                try:
                    f = ImageFont.truetype(font.path, size) if hasattr(font, "path") else font
                except:
                    f = font

                img = Image.new("L", (IMG_SIZE, IMG_SIZE), color=255)  # 흰 배경
                draw = ImageDraw.Draw(img)

                w, h = draw.textsize(glyph, font=f)
                x = (IMG_SIZE - w) // 2
                y = (IMG_SIZE - h) // 2
                draw.text((x, y), glyph, font=f, fill=0)  # 검은색 글자

                arr = np.array(img, dtype=np.float32).reshape(-1)
                X.append(arr)
                y.append(label)

    X = np.array(X)
    y = np.array(y)
    return X, y

def create_classifier():
    X, y = generate_training_data()
    clf = KNeighborsClassifier(n_neighbors=3)
    clf.fit(X, y)
    return clf

clf = create_classifier()

# ----------------- Tkinter UI 및 그리기 로직 -----------------

class HandCalcApp:
    def __init__(self, root):
        self.root = root
        self.root.title("손글씨 사칙연산 계산기")

        self.canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
        self.canvas.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_paint)

        # 그리는 내용을 같이 저장할 PIL 이미지
        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), color=255)
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None

        self.btn_recognize = tk.Button(root, text="인식 / 추가", command=self.recognize_and_append)
        self.btn_recognize.grid(row=1, column=0, padx=5, pady=5)

        self.btn_clear = tk.Button(root, text="지우기", command=self.clear_canvas)
        self.btn_clear.grid(row=1, column=1, padx=5, pady=5)

        self.btn_reset_expr = tk.Button(root, text="식 초기화", command=self.reset_expression)
        self.btn_reset_expr.grid(row=1, column=2, padx=5, pady=5)

        self.expr = ""  # 인식된 식
        self.lbl_expr = tk.Label(root, text="식: ", font=("Arial", 14))
        self.lbl_expr.grid(row=2, column=0, columnspan=3, sticky="w", padx=10)

        self.lbl_result = tk.Label(root, text="결과: ", font=("Arial", 14))
        self.lbl_result.grid(row=3, column=0, columnspan=3, sticky="w", padx=10)

        self.lbl_hint = tk.Label(
            root,
            text="한 글자씩 그린 뒤 '인식 / 추가'를 누르세요.\n"
                 "곱셈: *, x, X / 나눗셈: /, ÷ 가능\n"
                 "마지막에 '=' 를 그리면 자동 계산.",
            justify="left"
        )
        self.lbl_hint.grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=5)

    def on_button_press(self, event):
        self.last_x, self.last_y = event.x, event.y

    def on_paint(self, event):
        x, y = event.x, event.y
        if self.last_x is not None and self.last_y is not None:
            # Tkinter 캔버스에 선 그리기
            self.canvas.create_line(self.last_x, self.last_y, x, y, width=12, fill="black", capstyle="round")
            # PIL 이미지에도 동일하게 선 그리기
            self.draw.line((self.last_x, self.last_y, x, y), fill=0, width=12)
        self.last_x, self.last_y = x, y

    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), color=255)
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None

    def reset_expression(self):
        self.expr = ""
        self.lbl_expr.config(text="식: ")
        self.lbl_result.config(text="결과: ")
        self.clear_canvas()

    def preprocess_image(self):
        """
        현재 PIL 이미지(self.image)를 28x28로 줄이고 flatten
        """
        # 이미지를 약간 여백 포함해서 줄이기
        img = self.image

        # 완전히 빈 이미지인지 체크
        if np.all(np.array(img) == 255):
            return None

        # 28x28로 축소
        img = img.resize((IMG_SIZE, IMG_SIZE), Image.ANTIALIAS)

        # numpy 배열로 변환
        arr = np.array(img, dtype=np.float32).reshape(-1)
        return arr

    def recognize_char(self):
        arr = self.preprocess_image()
        if arr is None:
            return None
        pred = clf.predict([arr])[0]  # label 문자 하나
        # 안전하게 문자열로
        ch = str(pred)

        # 혹시라도 'x','X' 등이 label로 들어오는 경우 처리 (현재 학습은 '*'로 라벨링했지만 안전용)
        if ch in ['x', 'X']:
            ch = '*'
        if ch == '÷':
            ch = '/'

        return ch

    def recognize_and_append(self):
        ch = self.recognize_char()
        if ch is None:
            messagebox.showinfo("알림", "그려진 내용이 없습니다.")
            return

        # 인식된 문자 식에 추가
        if ch == '=':
            # '=' 이 나오면 앞의 식을 계산
            expr_to_eval = self.expr  # '=' 전까지 식
            if not expr_to_eval:
                messagebox.showinfo("알림", "계산할 식이 없습니다.")
                self.clear_canvas()
                return

            # 숫자와 + - * / 만 허용
            import re
            if not re.fullmatch(r"[0-9+\-*/ ]+", expr_to_eval):
                messagebox.showerror("오류", "허용되지 않은 문자가 포함된 식입니다.")
                self.clear_canvas()
                return

            try:
                result = eval(expr_to_eval)
                self.lbl_expr.config(text=f"식: {expr_to_eval} = {result}")
                self.lbl_result.config(text=f"결과: {result}")
                self.expr = ""  # 새 식을 위해 초기화
            except Exception as e:
                messagebox.showerror("오류", f"식 계산 실패: {e}")
            finally:
                self.clear_canvas()
        else:
            self.expr += ch
            self.lbl_expr.config(text=f"식: {self.expr}")
            self.clear_canvas()


if __name__ == "__main__":
    root = tk.Tk()
    app = HandCalcApp(root)
    root.mainloop()
