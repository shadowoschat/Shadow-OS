import cv2
import time

# Optional: psutil might fail on some systems
try:
    import psutil
except Exception:
    psutil = None

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Blink control
blink_interval = 0.5
last_blink = time.time()
rec_visible = True

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    color = (0, 255, 0)  # Neon green
    thickness = 2
    corner_len = 40

    # ---- Frame Corners ----
    # Top-left
    cv2.line(frame, (20, 20), (20 + corner_len, 20), color, thickness)
    cv2.line(frame, (20, 20), (20, 20 + corner_len), color, thickness)

    # Top-right
    cv2.line(frame, (w - 20, 20), (w - 20 - corner_len, 20), color, thickness)
    cv2.line(frame, (w - 20, 20), (w - 20, 20 + corner_len), color, thickness)

    # Bottom-left
    cv2.line(frame, (20, h - 20), (20 + corner_len, h - 20), color, thickness)
    cv2.line(frame, (20, h - 20), (20, h - 20 - corner_len), color, thickness)

    # Bottom-right
    cv2.line(frame, (w - 20, h - 20), (w - 20 - corner_len, h - 20), color, thickness)
    cv2.line(frame, (w - 20, h - 20), (w - 20, h - 20 - corner_len), color, thickness)

    # ---- Center Crosshair ----
    cx, cy = w // 2, h // 2
    cv2.line(frame, (cx - 15, cy), (cx + 15, cy), color, 1)
    cv2.line(frame, (cx, cy - 15), (cx, cy + 15), color, 1)

    # ---- REC Indicator (Blinking) ----
    if time.time() - last_blink > blink_interval:
        rec_visible = not rec_visible
        last_blink = time.time()

    if rec_visible:
        cv2.circle(frame, (40, 50), 6, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (55, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow("Visual Frame UI", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
