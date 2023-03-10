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

# Agrega ejes coordenados a la imagen
# INPUT:
# img: Imagen a la cual se le agregan los ejes
# OUTPUT: Otra imagen con los ejes superpuestos
def add_coordinate_axes(img):
    # Obtener las dimensiones de la imagen
    height, width, channels = img.shape

    # Crear una imagen en blanco para la cuadrícula
    grid = np.zeros((height, width, channels), np.uint8)

    # Definir el tamaño de la cuadrícula (cada cuadro mide 50 píxeles)
    cell_size = 50

    # Dibujar las líneas verticales de la cuadrícula
    for x in range(0, width, cell_size):
        cv2.line(grid, (x, 0), (x, height), (255, 255, 255), 1)
        cv2.putText(grid, str(x), (x+5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Dibujar las líneas horizontales de la cuadrícula
    for y in range(0, height, cell_size):
        cv2.line(grid, (0, y), (width, y), (255, 255, 255), 1)
        cv2.putText(grid, str(y), (5, y+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Combinar la imagen original y la cuadrícula
    result = cv2.addWeighted(img, 0.7, grid, 0.3, 0)

    return result


# Codifica una imagen y se envía en forma de string para el navegador
# INPUT image: imagen que se desea codificar
# OUTPUT String que puede ser recibido por el cliente
def codeImage(image):
    (flag, encodedImage) = cv2.imencode(".jpg", image)
    if not flag:
        return None
    return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
        bytearray(encodedImage) + b'\r\n')

# Genera continuamente una respuesta basada en la imagen de la cámara y aplica 
# una determinada transformación a la imagen
# INPUT
# transform: Función que modifica la imagen según las necesidades 
# OUTPUT: String de respuesta con la imagen codificada
def generate(transform = lambda x:x):
    cap = cv2.VideoCapture(0)
    # Verificar si la cámara se ha abierto correctamente
    if not cap.isOpened():
        print("Error al abrir la cámara")
        exit()

    while True:
        succes, frame = cap.read()
        # Re intentamos obtener la imagen en caso de fallar
        while not succes:
            print("La cámará no se pudo abrir, re intentado ...")
            cap = cv2.VideoCapture(0)
            succes, frame = cap.read()
        
        final_frame = transform(frame)

        yield codeImage(final_frame)

        

#-----------------------Flask enrutado----------------------------
app = Flask(__name__)

@app.route("/")
def index():
     return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate(add_coordinate_axes), mimetype='multipart/x-mixed-replace; boundary=frame')

#-----------------------Corremos el servidor----------------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')