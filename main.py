#-----------------------Librerías----------------------------
# Librerias para streaming
from flask import Flask, render_template, Response, request
from threading import Thread

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
    
    # Aplicamos la transformada de Fourier a la imagen en escala de grises
    f = fft2(gray)
    fshift = fftshift(f)
    magnitude_spectrum = 20*np.log(np.abs(fshift))
    
    # Convertimos la imagen de escala de grises en una imagen RGB
    magnitude_spectrum_rgb = cv2.cvtColor(cv2.convertScaleAbs(magnitude_spectrum), cv2.COLOR_GRAY2RGB)
    
    return magnitude_spectrum_rgb

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
def generate(*transforms):
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
        
        # Aplicamos las transformaciones pertinentes
        final_frame = frame
        for transform in transforms:
            final_frame = transform(final_frame)

        yield codeImage(final_frame)

# Reconstruye el holograma 
# INPUT:
# image: imagen del microscopio sin transformaciones
# OUPUT:
# Reconstrucción del holograma en formato de imagen de cv2
def apply_DLHM_reconstruction(img):
    global x,y, radio
    #-------------Aplicar FFT-----------------
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Pasamos a escala de grises
    f = fft2(gray)
    fshift = fftshift(f)

    #-------------Aplicar máscara circular----------
    mask = np.zeros(fshift.shape)
    mask = cv2.circle(mask,(x,y), radio, (1,1,1), -1)
    # Desplazar espectro
    # Invertir FFT
    # Convertir a imagen RGB
    # magnitude_spectrum_rgb = cv2.cvtColor(cv2.convertScaleAbs(magnitude_spectrum), cv2.COLOR_GRAY2RGB)

    return gray*mask
# -----NO ES FUNCIÓN PURA, USA VARIABLES GLOBALES ----------
# Dibuja un circulo si las variables globales lo permiten 
# INPUT:
# image: imagen a dibujar
# OUPUT:
# Imagen con el circulo dibujado según las variables globales
def draw_circle(img):
    global radio,x,y, drawCircle

    result = img
    if drawCircle:
        result = cv2.circle(img, (x,y), radio, (0,0,255), thickness = 2)
    return result

#-----------------------Hilos----------------------------
#Creamos un hilo que se encargue del procesamiento del video

# Crear una instancia de Thread para la función generate()
thread = Thread(target=generate)
thread.daemon = True
thread.start()

#-----------------------Variables globales----------------------------
radio,x,y, drawCircle = (0,0,0, False)

#-----------------------Flask enrutado----------------------------
app = Flask(__name__)

@app.route("/")
def index():
     return render_template("index.html")

@app.route("/reconstruction")
def reconstruction():
     return render_template("reconstruction.html")

@app.route("/add_circle")
def add_circle():
    global radio,x,y, drawCircle
    drawCircle = True
    radio = int(request.args.get('radio', 0))
    x = int(request.args.get('x', 0))
    y = int(request.args.get('y', 0))
    return Response('OK')

@app.route("/video_feed/<string:type>")
def video_feed(type):
    if type == "config":
        return Response(generate( apply_fourier_transform, draw_circle ,add_coordinate_axes), mimetype='multipart/x-mixed-replace; boundary=frame')
    elif type == "reconstruction":
        return Response(generate( apply_DLHM_reconstruction), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
#-----------------------Corremos el servidor----------------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')