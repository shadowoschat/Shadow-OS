import importlib
import os
import sys

try:
    import cv2
except Exception:  # pragma: no cover - desktop-only dependency
    cv2 = None

try:
    import numpy as np
except Exception:  # pragma: no cover - desktop-only dependency
    np = None

QT_AVAILABLE = False


def _require_desktop_sketch_libs():
    """Load desktop-only sketch dependencies only for explicit local desktop mode."""
    missing = []
    if cv2 is None:
        missing.append("opencv-python")
    if np is None:
        missing.append("numpy")

    try:
        widgets_mod = importlib.import_module("PyQt5" + ".QtWidgets")
        gui_mod = importlib.import_module("PyQt5" + ".QtGui")
        core_mod = importlib.import_module("PyQt5" + ".QtCore")
        media_mod = importlib.import_module("PyQt5" + ".QtMultimedia")
        QApplication = getattr(widgets_mod, "QApplication")
        QWidget = getattr(widgets_mod, "QWidget")
        QLabel = getattr(widgets_mod, "QLabel")
        QFrame = getattr(widgets_mod, "QFrame")
        QHBoxLayout = getattr(widgets_mod, "QHBoxLayout")
        QVBoxLayout = getattr(widgets_mod, "QVBoxLayout")
        QScrollArea = getattr(widgets_mod, "QScrollArea")
        QImage = getattr(gui_mod, "QImage")
        QPixmap = getattr(gui_mod, "QPixmap")
        QPainter = getattr(gui_mod, "QPainter")
        QColor = getattr(gui_mod, "QColor")
        QBrush = getattr(gui_mod, "QBrush")
        QFont = getattr(gui_mod, "QFont")
        QMovie = getattr(gui_mod, "QMovie")
        QPolygon = getattr(gui_mod, "QPolygon")
        Qt = getattr(core_mod, "Qt")
        QTimer = getattr(core_mod, "QTimer")
        QPoint = getattr(core_mod, "QPoint")
        QSize = getattr(core_mod, "QSize")
        QUrl = getattr(core_mod, "QUrl")
        QMediaPlayer = getattr(media_mod, "QMediaPlayer")
        QMediaContent = getattr(media_mod, "QMediaContent")
    except Exception as exc:  # pragma: no cover - intentionally optional for server startup
        raise RuntimeError(
            "Desktop sketch mode is unavailable in this environment. "
            "Use the browser-based sketch workflow on Render."
        ) from exc

    if missing:
        raise RuntimeError(
            "Desktop sketch mode requires the following packages: " + ", ".join(sorted(missing))
        )

    return {
        "QApplication": QApplication,
        "QWidget": QWidget,
        "QLabel": QLabel,
        "QFrame": QFrame,
        "QHBoxLayout": QHBoxLayout,
        "QVBoxLayout": QVBoxLayout,
        "QScrollArea": QScrollArea,
        "QImage": QImage,
        "QPixmap": QPixmap,
        "QPainter": QPainter,
        "QColor": QColor,
        "QBrush": QBrush,
        "QFont": QFont,
        "QMovie": QMovie,
        "QPolygon": QPolygon,
        "Qt": Qt,
        "QTimer": QTimer,
        "QPoint": QPoint,
        "QSize": QSize,
        "QUrl": QUrl,
        "QMediaPlayer": QMediaPlayer,
        "QMediaContent": QMediaContent,
    }


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
def _create_desktop_sketch_ui_class():
    qt = _require_desktop_sketch_libs()
    QWidget = qt["QWidget"]
    QFrame = qt["QFrame"]
    QHBoxLayout = qt["QHBoxLayout"]
    QVBoxLayout = qt["QVBoxLayout"]
    QScrollArea = qt["QScrollArea"]
    QLabel = qt["QLabel"]
    QPixmap = qt["QPixmap"]
    QMovie = qt["QMovie"]
    QFont = qt["QFont"]
    Qt = qt["Qt"]
    QPolygon = qt["QPolygon"]
    QBrush = qt["QBrush"]
    QColor = qt["QColor"]
    QPainter = qt["QPainter"]
    QImage = qt["QImage"]
    QPoint = qt["QPoint"]
    QSize = qt["QSize"]
    QApplication = qt["QApplication"]
    QMediaPlayer = qt["QMediaPlayer"]
    QMediaContent = qt["QMediaContent"]
    QUrl = qt["QUrl"]

    class AstraSketchUI(QWidget):
        def __init__(self, image_name: str):
            super().__init__()
            self.zoom_factor = 1.0

            self.setWindowTitle("A.S.T.R.A. Ai – Sketch Mode")
            self.setMinimumSize(1100, 700)
            self.setStyleSheet("background-color: black;")

            self.image_path = get_image_path(image_name)
            if not self.image_path:
                raise FileNotFoundError("❌ Image not found in Data/img-data")

            original = cv2.imread(self.image_path)
            filtered = cv2.bilateralFilter(original, d=9, sigmaColor=75, sigmaSpace=75)
            self.gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)

            self.image_name = os.path.basename(self.image_path)
            self.original_pixmap = QPixmap(self.image_path)

            inv_gray = 255 - self.gray
            blurred = cv2.GaussianBlur(inv_gray, (25, 25), 0)
            sketch = cv2.divide(self.gray, 255 - blurred, scale=256)

            xp = [0, 50, 120, 200, 255]
            fp = [0, 20, 90, 200, 255]
            x = np.arange(256)
            table = np.interp(x, xp, fp).astype('uint8')
            self.target_sketch = cv2.LUT(sketch, table)

            self.h, self.w = self.target_sketch.shape
            self.canvas = np.ones_like(self.gray) * 255
            self.current_progress_line = 0
            self.step_size = max(2, self.h // 120)
            self.cursor_pos = QPoint(0, 0)

            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)

            gif_frame = QFrame()
            gif_frame.setFixedHeight(100)
            gif_frame.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
            gif_layout = QHBoxLayout(gif_frame)
            gif_layout.setContentsMargins(20, 5, 20, 5)

            self.gif_label = QLabel(alignment=Qt.AlignCenter)
            self.gif_movie = QMovie(os.path.join(BASE_DIR, "Frontend", "Static", "image", "sound.gif"))
            self.gif_movie.setScaledSize(QSize(1400, 100))
            self.gif_label.setMovie(self.gif_movie)
            self.gif_movie.start()

            gif_layout.addWidget(self.gif_label)
            main_layout.addWidget(gif_frame)

            panels_layout = QHBoxLayout()
            panels_layout.setSpacing(10)

            left_panel = QFrame()
            left_panel.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(20, 20, 20, 20)
            left_layout.setSpacing(20)

            title_label = QLabel("A.S.T.R.A AI")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("color: #00eaff; font-size: 32px; font-weight: bold;")
            title_label.setFont(QFont("Arial", 28, QFont.Bold))
            left_layout.addWidget(title_label)

            self.original_label = QLabel(alignment=Qt.AlignCenter)
            self.original_label.setMinimumSize(300, 300)
            self.original_label.setStyleSheet("background-color: #111; border: 1px solid #333; border-radius: 10px;")
            left_layout.addWidget(self.original_label, stretch=1)

            self.image_name_label = QLabel(self.image_name)
            self.image_name_label.setAlignment(Qt.AlignCenter)
            self.image_name_label.setStyleSheet("color: #00eaff; font-size: 20px; font-weight: bold; padding: 10px;")
            self.image_name_label.setFont(QFont("Arial", 18, QFont.Bold))
            left_layout.addWidget(self.image_name_label)

            right_panel = QFrame()
            right_panel.setStyleSheet("QFrame { border: 2px solid #00eaff; background: black; }")
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(10, 10, 10, 10)

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

            self.media_player = QMediaPlayer()
            pencil_sound_path = os.path.join(BASE_DIR, "Frontend", "Static", "image", "pencil-sound.mp3")
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

            last_row = next_line - 1
            dark_pixels = np.where(self.canvas[last_row, :] < 160)[0]
            if len(dark_pixels) > 0:
                self.cursor_pos = QPoint(dark_pixels[-1], last_row)
            else:
                self.cursor_pos = QPoint(self.w // 2, last_row)

            self.current_progress_line = next_line
            self.render_frame()

        def wheelEvent(self, event):
            if self.scroll_area.geometry().contains(event.pos()):
                modifiers = QApplication.keyboardModifiers()
                if modifiers == Qt.ControlModifier:
                    angle = event.angleDelta().y()
                    if angle > 0:
                        self.zoom_factor = min(self.zoom_factor + 0.1, 3.0)
                    else:
                        self.zoom_factor = max(self.zoom_factor - 0.1, 0.5)
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

            painter = QPainter(qimg)
            painter.setRenderHint(QPainter.Antialiasing)

            tip = self.cursor_pos
            p1 = QPoint(tip.x() + 8, tip.y() - 20)
            p2 = QPoint(tip.x() + 18, tip.y() - 14)
            p3 = QPoint(tip.x() + 40, tip.y() - 50)
            p4 = QPoint(tip.x() + 50, tip.y() - 44)

            lead_poly = QPolygon([tip, QPoint(tip.x() + 3, tip.y() - 8), QPoint(tip.x() + 8, tip.y() - 3)])
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(lead_poly)

            wood_poly = QPolygon([QPoint(tip.x() + 3, tip.y() - 8), QPoint(tip.x() + 8, tip.y() - 3), p2, p1])
            painter.setBrush(QBrush(QColor(230, 197, 145)))
            painter.drawPolygon(wood_poly)

            body_poly = QPolygon([p1, p2, p4, p3])
            painter.setBrush(QBrush(QColor(210, 40, 40)))
            painter.drawPolygon(body_poly)

            painter.end()

            base_size = self.scroll_area.size()
            target_w = int(base_size.width() * self.zoom_factor)
            target_h = int(base_size.height() * self.zoom_factor)

            pix = QPixmap.fromImage(qimg).scaled(
                QSize(target_w, target_h),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.sketch_label.setPixmap(pix)

    return AstraSketchUI, qt


# ======================================================
# EXTERNAL CALL
# ======================================================
def draw_sketch(subject: str, *, allow_desktop: bool = False):
    if not allow_desktop:
        raise RuntimeError(
            "Desktop sketch mode is disabled in the web app. Use the browser sketch workflow."
        )

    AstraSketchUI, qt = _create_desktop_sketch_ui_class()
    app = qt["QApplication"](sys.argv)
    ui = AstraSketchUI(subject)
    ui.show()
    return app.exec_()


# ======================================================
# DIRECT TEST
# ======================================================
if __name__ == "__main__":
    raise SystemExit(draw_sketch("krishna", allow_desktop=True))
