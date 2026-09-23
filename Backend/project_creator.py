import os
import sys
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QFrame,
    QHBoxLayout, QVBoxLayout
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QBrush, QFont, QMovie
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


# ======================================================
# PATH SETUP
# ======================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data", "img-data")


def get_image_path(name: str):
    name = name.lower().strip()
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        p = os.path.join(DATA_DIR, name + ext)
        if os.path.exists(p):
            return p
    return None


# ======================================================
# SHADOW SKETCH GUI
# ======================================================
class ShadowSketchUI(QWidget):
    def __init__(self, image_name: str):
        super().__init__()

        # ---------------- WINDOW ----------------
        self.setWindowTitle("A.S.T.R.A. Ai – Sketch Mode")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet("background-color: black;")

        # ---------------- LOAD IMAGE ----------------
        self.image_path = get_image_path(image_name)
        if not self.image_path:
            sys.exit("❌ Image not found in Data/img-data")

        original = cv2.imread(self.image_path)
        self.gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

        self.image_name = os.path.basename(self.image_path)
        self.original_pixmap = QPixmap(self.image_path)

        # ---------------- SKETCH PROCESS ----------------
        inv = 255 - self.gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        pencil = cv2.divide(self.gray, 255 - blur, scale=256)

        thresh = cv2.adaptiveThreshold(
            pencil, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        self.contours = [c for c in contours if len(c) > 5]
        self.contours.sort(key=lambda c: cv2.boundingRect(c)[1])

        self.canvas = np.ones_like(self.gray) * 255
        self.index = 0
        self.cursor_pos = QPoint(0, 0)

        # ---------------- MAIN LAYOUT ----------------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # TOP GIF
        gif_frame = QFrame()
        gif_frame.setFixedHeight(100)
        gif_frame.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
        gif_layout = QHBoxLayout(gif_frame)
        gif_layout.setContentsMargins(20, 5, 20, 5)
        
        self.gif_label = QLabel(alignment=Qt.AlignCenter)
        self.gif_movie = QMovie(os.path.join(BASE_DIR, "Frontend/static/sound.gif"))
        self.gif_movie.setScaledSize(QSize(1400, 100))
        self.gif_label.setMovie(self.gif_movie)
        self.gif_movie.start()
        
        gif_layout.addWidget(self.gif_label)
        main_layout.addWidget(gif_frame)

        # PANELS
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(10)

        # LEFT PANEL
        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)

        # Title
        title_label = QLabel("A.S.T.R.A AI")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00eaff; font-size: 32px; font-weight: bold;")
        title_label.setFont(QFont("Arial", 28, QFont.Bold))
        left_layout.addWidget(title_label)

        # Original Image
        self.original_label = QLabel(alignment=Qt.AlignCenter)
        self.original_label.setMinimumSize(300, 300)
        self.original_label.setStyleSheet("background-color: #111; border: 1px solid #333; border-radius: 10px;")
        left_layout.addWidget(self.original_label, stretch=1)

        # Image Name
        self.image_name_label = QLabel(self.image_name)
        self.image_name_label.setAlignment(Qt.AlignCenter)
        self.image_name_label.setStyleSheet("color: #00eaff; font-size: 20px; font-weight: bold; padding: 10px;")
        self.image_name_label.setFont(QFont("Arial", 18, QFont.Bold))
        left_layout.addWidget(self.image_name_label)

        # RIGHT PANEL (UNCHANGED)
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)

        sketch_frame = QFrame()
        sketch_layout = QVBoxLayout(sketch_frame)

        self.sketch_label = QLabel(alignment=Qt.AlignCenter)
        self.sketch_label.setStyleSheet("background-color: white; border-radius: 5px;")
        sketch_layout.addWidget(self.sketch_label)

        right_layout.addWidget(sketch_frame, stretch=1)

        panels_layout.addWidget(left_panel, stretch=1)
        panels_layout.addWidget(right_panel, stretch=2)
        main_layout.addLayout(panels_layout)

        self.update_original_image()

        # TIMER
        self.media_player = QMediaPlayer()
        pencil_sound_path = os.path.join(BASE_DIR, "Frontend/static/pencil-sound.mp3")
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(pencil_sound_path)))
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.draw_step)
        self.timer.start(25)

    def draw_step(self):
        if self.index >= len(self.contours):
            self.timer.stop()
            self.media_player.stop()
            return

        cnt = self.contours[self.index]
        cv2.drawContours(self.canvas, [cnt], -1, (0,), 1)

        self.media_player.play()  # Play pencil sound non-blocking

        last = cnt[-1][0]
        self.cursor_pos = QPoint(last[0], last[1])

        self.index += 1
        self.render_frame()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_original_image()
        self.render_frame()

    def update_original_image(self):
        if hasattr(self, 'original_pixmap') and self.original_label:
            scaled_pix = self.original_pixmap.scaled(
                self.original_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.original_label.setPixmap(scaled_pix)

    def mouseMoveEvent(self, event):
        if self.sketch_label.geometry().contains(event.pos()):
            self.cursor_pos = event.pos()
            self.render_frame()

    def render_frame(self):
        h, w = self.canvas.shape
        qimg = QImage(
            self.canvas.data, w, h, w,
            QImage.Format_Grayscale8
        ).convertToFormat(QImage.Format_RGB32)

        painter = QPainter(qimg)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.cursor_pos, 4, 4)
        painter.end()

        pix = QPixmap.fromImage(qimg).scaled(
            self.sketch_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.sketch_label.setPixmap(pix)


# ======================================================
# EXTERNAL CALL (app.py use)
# ======================================================
def draw_sketch(subject: str):
    app = QApplication(sys.argv)
    ui = ShadowSketchUI(subject)
    ui.show()
    sys.exit(app.exec_())


# ======================================================
# DIRECT TEST
# ======================================================
if __name__ == "__main__":
    draw_sketch("hanumanji")
