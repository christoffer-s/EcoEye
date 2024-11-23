from picamera2 import Picamera2, Preview
import cv2
import time
from flask import Flask, Response, render_template
from ultralytics import YOLO
import GOPTEST

app = Flask(__name__)

def generate():
    # Sett opp kameraet
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (1280, 1280)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()

    # Last inn YOLOv8-modellen
    model = YOLO("last_ncnn_model")

    try:
        while True:
            frame = picam2.capture_array()
            # Kjører YOLO-modellen på bildet og tegner detekterte objekter
            results = model(frame)
            annotated_frame = results[0].plot()

            # Beregn FPS (frame per sekund)
            inference_time = results[0].speed['inference']  # Tidsbruk for inferens i ms
            fps = 1000 / inference_time if inference_time > 0 else 0

            # Tegn FPS på bildet
            font = cv2.FONT_HERSHEY_SIMPLEX
            text = f'FPS: {fps:.1f}'
            text_size = cv2.getTextSize(text, font, 1, 2)[0]
            text_x = annotated_frame.shape[1] - text_size[0] - 10
            text_y = text_size[1] + 10
            cv2.putText(annotated_frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # Konverter til JPEG-format for å kunne sende via HTTP
            _, jpeg = cv2.imencode('.jpg', annotated_frame)
            annotated_frame = jpeg.tobytes()

            # Send bildet til nettleseren
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + annotated_frame + b'\r\n')
    finally:
        picam2.stop()

# Rute for hovedsiden
@app.route('/')
def index():
    return render_template('index.html')

# Rute for videostrømmen
@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/kart_feed')
def kart_feed():
    return Response(GOPTEST.kart(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
