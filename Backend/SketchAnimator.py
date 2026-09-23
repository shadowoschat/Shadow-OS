import os
import sys
import cv2
import numpy as np
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QFrame,
    QHBoxLayout, QVBoxLayout, QScrollArea
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QBrush, QFont, QMovie, QPolygon
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
# SHADOWSKETCH GUI
# ======================================================
class AstraSketchUI(QWidget):
    def __init__(self, image_name: str):
        super().__init__()

        # Zoom Scale Initial State
        self.zoom_factor = 1.0

        # ---------------- WINDOW ----------------
        self.setWindowTitle("A.S.T.R.A. Ai – Sketch Mode")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet("background-color: black;")

        # ---------------- LOAD IMAGE ----------------
        self.image_path = get_image_path(image_name)
        if not self.image_path:
            sys.exit("❌ Image not found in Data/img-data")

        original = cv2.imread(self.image_path)
        
        # 1. Background clean karne ke liye Bilateral Filter (Leaves smoothing + sharp faces)
        filtered = cv2.bilateralFilter(original, d=9, sigmaColor=75, sigmaSpace=75)
        self.gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)

        self.image_name = os.path.basename(self.image_path)
        self.original_pixmap = QPixmap(self.image_path)

        # ---------------- HD PORTRAIT SKETCH LOGIC ----------------
        inv_gray = 255 - self.gray
        blurred = cv2.GaussianBlur(inv_gray, (25, 25), 0)
        
        # Color Dodge blend mix
        sketch = cv2.divide(self.gray, 255 - blurred, scale=256)
        
        # Gamma Curve adjustment to clear the dust/leaves noise and make borders clean
        xp = [0, 50, 120, 200, 255]
        fp = [0, 20, 90, 200, 255]
        x = np.arange(256)
        table = np.interp(x, xp, fp).astype('uint8')
        self.target_sketch = cv2.LUT(sketch, table)
        
        # Animation variables
        self.h, self.w = self.target_sketch.shape
        self.canvas = np.ones_like(self.gray) * 255
        
        self.current_progress_line = 0
        self.step_size = max(2, self.h // 120)  
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

        # RIGHT PANEL (WITH ZOOM SCROLLAREA)
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # ScrollArea allows smooth moving when zoomed inside
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #111; border: none;")
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.sketch_label = QLabel(alignment=Qt.AlignCenter)
        self.sketch_label.setStyleSheet("background-color: white; border-radius: 5px;")
        self.scroll_area.setWidget(self.sketch_label)
        
        right_layout.addWidget(self.scroll_area)

        panels_layout.addWidget(left_panel, stretch=1)
        panels_layout.addWidget(right_panel, stretch=2)
        main_layout.addLayout(panels_layout)

        self.update_original_image()

        # TIMER & MEDIA
        self.media_player = QMediaPlayer()
        pencil_sound_path = os.path.join(BASE_DIR, "Frontend/static/pencil-sound.mp3")
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(pencil_sound_path)))
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.draw_step)
        self.timer.start(20)

    def draw_step(self):
        if self.current_progress_line >= self.h:
            self.timer.stop()
            self.media_player.stop()
            return

        next_line = min(self.current_progress_line + self.step_size, self.h)
        for r in range(self.current_progress_line, next_line):
            self.canvas[r, :] = self.target_sketch[r, :]

        self.media_player.play()

        # Track cursor dynamically along the active sharp lines
        last_row = next_line - 1
        dark_pixels = np.where(self.canvas[last_row, :] < 160)[0]
        if len(dark_pixels) > 0:
            self.cursor_pos = QPoint(dark_pixels[-1], last_row)
        else:
            self.cursor_pos = QPoint(self.w // 2, last_row)

        self.current_progress_line = next_line
        self.render_frame()

    # ZOOM-IN ZOOM-OUT OVERRIDE METHOD
    def wheelEvent(self, event):
        # Checking if mouse wheel scrolled inside sketch frame
        if self.scroll_area.geometry().contains(event.pos()):
            modifiers = QApplication.keyboardModifiers()
            # Zoom triggers via Ctrl + Mouse Scroll Wheel
            if modifiers == Qt.ControlModifier:
                angle = event.angleDelta().y()
                if angle > 0:
                    self.zoom_factor = min(self.zoom_factor + 0.1, 3.0)  # Max zoom 300%
                else:
                    self.zoom_factor = max(self.zoom_factor - 0.1, 0.5)  # Min zoom 50%
                self.render_frame()
                event.accept()
                return
        super().wheelEvent(event)

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

    def render_frame(self):
        qimg = QImage(
            self.canvas.data, self.w, self.h, self.w,
            QImage.Format_Grayscale8
        ).convertToFormat(QImage.Format_RGB32)

        # ---------------- DRAW PENCIL CURSOR ----------------
        painter = QPainter(qimg)
        painter.setRenderHint(QPainter.Antialiasing)
        
        tip = self.cursor_pos
        p1 = QPoint(tip.x() + 8, tip.y() - 20)
        p2 = QPoint(tip.x() + 18, tip.y() - 14)
        p3 = QPoint(tip.x() + 40, tip.y() - 50)
        p4 = QPoint(tip.x() + 50, tip.y() - 44)
        
        # Pencil Graphite Tip
        lead_poly = QPolygon([tip, QPoint(tip.x() + 3, tip.y() - 8), QPoint(tip.x() + 8, tip.y() - 3)])
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(lead_poly)
        
        # Wooden cone body
        wood_poly = QPolygon([QPoint(tip.x() + 3, tip.y() - 8), QPoint(tip.x() + 8, tip.y() - 3), p2, p1])
        painter.setBrush(QBrush(QColor(230, 197, 145)))
        painter.drawPolygon(wood_poly)
        
        # Red Pencil Shaft
        body_poly = QPolygon([p1, p2, p4, p3])
        painter.setBrush(QBrush(QColor(210, 40, 40)))
        painter.drawPolygon(body_poly)
        
        painter.end()

        # Calculate final size incorporating the active zoom factor scale
        base_size = self.scroll_area.size()
        target_w = int(base_size.width() * self.zoom_factor)
        target_h = int(base_size.height() * self.zoom_factor)

        pix = QPixmap.fromImage(qimg).scaled(
            QSize(target_w, target_h),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.sketch_label.setPixmap(pix)


# ======================================================
# EXTERNAL CALL
# ======================================================
def draw_sketch(subject: str):
    app = QApplication(sys.argv)
    ui = AstraSketchUI(subject)
    ui.show()
    sys.exit(app.exec_())


# ======================================================
# DIRECT TEST
# ======================================================
if __name__ == "__main__":
    draw_sketch("krishna")
