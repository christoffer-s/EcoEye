from picamera2 import Picamera2, Preview
import cv2
import time
from flask import Flask, Response, render_template, request
from ultralytics import YOLO
import gpiozero
from gpiozero import OutputDevice
from gpiozero.pins.mock import MockFactory

# Sett opp pinne-fabrikk for gpiozero
gpiozero.Device.pin_factory = MockFactory()

# Sett opp Flask
app = Flask(__name__)

# Definer GPIO-pinnene for motorene
motors = {
    'right': OutputDevice(17),
    'left': OutputDevice(27),
    'up': OutputDevice(22),
    'down': OutputDevice(23)
}
# Konfigurer Picamera2
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(camera_config)
picam2.start()

# Last inn YOLO-modellen
model = YOLO("yolov8n_ncnn_model")

def activate_motor(direction):
    """Aktiverer motoren for valgt retning i et kort intervall."""
    motor = motors.get(direction)
    if motor:
        motor.on()
        time.sleep(0.5)  # Aktiverer i 0,5 sekunder
        motor.off()

def generate():
    """Genererer videostrøm med YOLO-detektering."""
    while True:
        # Hent ett enkelt ramme fra kameraet
        frame = picam2.capture_array()
        
        # Kjør YOLO-modellen på rammen for å få deteksjoner
        results = model(frame)
        annotated_frame = results[0].plot()

        # Konverter rammen til JPEG for strømming
        _, jpeg = cv2.imencode('.jpg', annotated_frame)
        annotated_frame = jpeg.tobytes()
        
        # Send rammen som HTTP-strøm
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + annotated_frame + b'\r\n')

# Rute for hovedsiden
@app.route('/')
def index():
    return render_template('index3.html')

# Rute for videostrøm
@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Rute for motorstyring
@app.route('/move', methods=['POST'])
def move():
    direction = request.form.get('direction')
    activate_motor(direction)
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
