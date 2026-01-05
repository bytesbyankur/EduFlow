import cv2
import time

print("OpenCV version:", cv2.__version__)

for backend_name, backend in [
    ("ANY", cv2.CAP_ANY),
    ("MSMF", cv2.CAP_MSMF),
    ("DSHOW", cv2.CAP_DSHOW),
]:
    print(f"\nTesting backend: {backend_name}")
    cap = cv2.VideoCapture(1, backend)
    time.sleep(1)

    print("Opened:", cap.isOpened())
    if cap.isOpened():
        ret, frame = cap.read()
        print("Read frame:", ret)
        if ret:
            cv2.imshow(f"Camera Test ({backend_name})", frame)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()
        cap.release()
