#-----------------------Librerías----------------------------
# Librerias para streaming
from flask import Flask, render_template, Response

# Librerias para procesamiento de imagenes
import numpy as np
from scipy.fftpack import fft2, fftshift
import cv2

#-----------------------Funciones----------------------------
# Aplica FFT
# INPUT
# frame: Imagen a la cual se le aplica su transformada 
# OUTPUT: Otra imagen en escala de grises con la magnitud de la FFT

def apply_fourier_transform(frame):
    # Convertimos la imagen a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Aplicamos la transformada de Fourier
    f = fft2(gray)
    fshift = fftshift(f)
    magnitude_spectrum = 20*np.log(np.abs(fshift))
    
    return magnitude_spectrum

# Abre la cámara del equipo y regresa su imagen
# INPUT None
# OUTPUT Una imagen de cv2 
def getCamImage():
    cap = cv2.VideoCapture(0)
    # Verificar si la cámara se ha abierto correctamente
    if not cap.isOpened():
        print("Error al abrir la cámara")
        exit()

    succes, frame = cap.read()
    while not succes:
        print("La cámará no se pudo abrir, re intentado ...")
        cap = cv2.VideoCapture(0)
        succes, frame = cap.read()
    return frame

# Genera continuamente una respuesta basada en la imagen de la cámara y aplica 
# una determinada transformación a la imagen
# INPUT
# transform: Función que modifica la imagen según las necesidades 
# OUTPUT: String de respuesta con la imagen codificada
def generate(transform = lambda x:x):
    while True:
        frame = getCamImage()
        final_frame = transform(frame)

        (flag, encodedImage) = cv2.imencode(".jpg", final_frame)
        if not flag:
            continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encodedImage) + b'\r\n')

#-----------------------Flask enrutado----------------------------
app = Flask(__name__)

@app.route("/")
def index():
     return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')