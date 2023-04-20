#-----------------------Librerías----------------------------
# Librerias para streaming
from flask import Flask, render_template, Response, request, send_file
from threading import Thread

# Librerias para procesamiento de imagenes
import numpy as np
from scipy.fftpack import fft2, fftshift, ifft2
import cv2

# Librerías de manejo de tiempo
import time

#-----------------------Variables globales----------------------------
radio,x,y = (0,0,0)
state = {"circle": False, "fourier": False, "reconstruction": False, "grid": False }
reconstructionMode = "intensity"
cameraConfig = {"exposure": 50, "gain": 1, "width": 640, "height": 480, "flag": True}
download = True
downloadPath = "./resources/DHM.jpg"

#---------------------Decoradores-----------------------------
# Revisa la condición determinada dentro de "state" y si se encuentra desactivada, retorna el input
def validation_transform(condition):
    def validate_function(transform):
        global state
        def new_function(image):
            if state[condition]:
                return transform(image)
            else:
                return image
        return new_function
    return validate_function

#-----------------------Funciones----------------------------
# Aplica FFT
# INPUT
# frame: Imagen a la cual se le aplica su transformada 
# OUTPUT: Otra imagen en escala de grises con la magnitud de la FFT
@validation_transform("fourier")
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
@validation_transform("grid")
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

# Configura la cámara según los parámetros establecidos
# INPUT 
# cap: instancia de la cámara a configurar
# OUTPUT Void
def configCamera(cap):
    global cameraConfig
    if(cameraConfig["flag"]):
        # Se configura el tamaño de la cámara
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cameraConfig["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cameraConfig["height"])

        # Se configura el tiempo de exposición
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75) # Se desactiva el modo automatico
        cap.set(cv2.CAP_PROP_EXPOSURE, cameraConfig["exposure"])
        
        # Evitamos que se vuelva a configurar cada que se entre
        cameraConfig["flag"] = False

# Genera continuamente una respuesta basada en la imagen de la cámara y aplica 
# determinadas transformaciones a la imagen
# INPUT
# *transforms: Función que modifica la imagen según las necesidades y debe retornar imagen rgb 
# OUTPUT: String de respuesta con la imagen codificada
def generate(*transforms):
    global download, downloadPath
    cap = cv2.VideoCapture(0)
    try:
        # Verificar si la cámara se ha abierto correctamente
        if not cap.isOpened():
            print("Error al abrir la cámara")
            exit()

        while True:
            # Configuramos la cámara
            configCamera(cap)
            # Definimos el tiempo de inicio
            start_time = time.time()
            # Capturamos la imagen de la cámara
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

            # Si se solicitó una descarga, se guarda en un archivo la imagen
            if download:
                cv2.imwrite(downloadPath , final_frame)
                download = False

            # Escribimos los FPS sobre la imagen
            fps = int(1.0 / (time.time() - start_time))
            cv2.putText(final_frame, "FPS: {:n}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            yield codeImage(final_frame)
    finally:
        cap.release()

# Reconstruye el holograma 
# INPUT:
# image: imagen del microscopio sin transformaciones
# OUPUT:
# Reconstrucción del holograma en formato de imagen de cv2
@validation_transform("reconstruction")
def apply_DHM_reconstruction(img):
    global x,y, radio, reconstructionMode
    #-------------Aplicar FFT-----------------
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Pasamos a escala de grises
    f = fft2(gray)
    fshift = fftshift(f)

    #-------------Aplicar máscara circular----------
    mask = np.zeros(fshift.shape)
    mask = cv2.circle(mask,(x,y), radio, (1,1,1), -1)

    img_filter = fshift*mask

    # ----------Desplazar espectro----------
    img_filter = img_filter.astype(np.complex128) # Aseguramos el tipo de la imagen

    # Obtener dimensiones de la imagen
    alto, ancho = img_filter.shape[:2]

    # Definir matriz de transformación
    M = np.float32([[1, 0, ancho//2 - x], [0, 1, alto//2 - y]]) # Desplazamos a la mitad de la imagen

    # Dividir imagen en sus partes real e imaginaria
    real = np.real(img_filter)
    imag = np.imag(img_filter)

    # Aplicar transformación a partes real e imaginaria
    real_desplazada = cv2.warpAffine(real, M, (ancho, alto))
    imag_desplazada = cv2.warpAffine(imag, M, (ancho, alto))

    # Combinar partes real e imaginaria en una imagen compleja
    result = real_desplazada + 1j*imag_desplazada
    # Invertir FFT
    result = ifft2(result)

    # Convertir a imagen RGB según el modo que corresponda
    if (reconstructionMode =='intensity'):
        result = result/255
        result = np.abs(result)**2
        result = result*255
    elif (reconstructionMode =='phase'):
        result=np.angle(result)
        # Reescalamos entre 0 y 255
        result = ((result + np.pi)/(2*np.pi))*255
    elif (reconstructionMode =='amplitude'):
        result=np.abs(result)
        
    result = cv2.cvtColor(cv2.convertScaleAbs(result), cv2.COLOR_GRAY2RGB)

    return result

# -----NO ES FUNCIÓN PURA, USA VARIABLES GLOBALES ----------
# Dibuja un circulo si las variables globales lo permiten 
# INPUT:
# image: imagen a dibujar
# OUPUT:
# Imagen con el circulo dibujado según las variables globales
@validation_transform("circle")
def draw_circle(img):
    global radio,x,y
    result = cv2.circle(img, (x,y), radio, (0,0,255), thickness = 2)
    return result

# Toma un string y si tiene el valor "True" retorna verdadero
# Input: str: string con el valor a evaluar
# Output: booleano con la comparación
def str2bool(str):
    if str.lower() == "true":
        return True
    return False    
#-----------------------Hilos----------------------------
#Creamos un hilo que se encargue del procesamiento del video

# Crear una instancia de Thread para la función generate()
thread = Thread(target=generate)
thread.daemon = True
thread.start()

#-----------------------Flask enrutado----------------------------
app = Flask(__name__)

@app.route("/")
def index():
     return render_template("index.html")

@app.route("/add_circle")
def add_circle():
    global radio,x,y
    radio = int(request.args.get('radio', 0))
    x = int(request.args.get('x', 0))
    y = int(request.args.get('y', 0))
    return Response('OK')

@app.route("/config_camera")
def config_camera():
    global cameraConfig
    cameraConfig["exposure"]  = int(request.args.get("exposure", cameraConfig["exposure"]))
    cameraConfig["gain"]  = int(request.args.get("gain", cameraConfig["gain"]))
    cameraConfig["height"]  = int(request.args.get("height", cameraConfig["height"]))
    cameraConfig["width"]  = int(request.args.get("width", cameraConfig["width"]))

    cameraConfig["flag"] = True  # Permitimos que se ejecute la configuración establecida
    return Response('OK')

@app.route("/config_reconstruction")
def config_reconstruction():
    global reconstructionMode
    mode = request.args.get('mode', "") # Variable temporal
    if (mode.lower() == 'intensity'):
        reconstructionMode = 'intensity'
    elif (mode.lower() == 'phase'):
        reconstructionMode = 'phase'
    elif (mode.lower() == 'amplitude'):
        reconstructionMode = 'amplitude'
    else:
        return Response('NO WORK')
    return Response('OK')

@app.route("/config_state")
def config_state():
    global state
    state["circle"]          = str2bool(request.args.get('circle', False))
    state["fourier"]         = str2bool(request.args.get('fourier', False))
    state["reconstruction"]  = str2bool(request.args.get('reconstruction', False))
    state["grid"]            = str2bool(request.args.get('grid', False))

    return Response('OK')

@app.route("/video_feed")
def video_feed():
    return Response(generate(apply_fourier_transform, draw_circle, apply_DHM_reconstruction, add_coordinate_axes), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/download_feed")
def download_feed():
    global downloadPath,download
    download = True
    return send_file(downloadPath, mimetype='image/jpg')
#-----------------------Corremos el servidor----------------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')