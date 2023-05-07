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
radio,x,y = (0,0,0) # Circulo para la reconstrucción
state = {"circle": False, "fourier": False, "reconstruction": False, "grid": False } # Estado de la imagen transmitida
reconstructionMode = "intensity" # Modo de la transformación de reconstrucción
cameraConfig = {"exposure": 50, "gain": 1, "width": 640, "height": 480, "flag": True} # Configuración de la cámara
angleX, angleY = (0,0) # Angúlos de la onda plana de compensación 
# Variables para la descarga y referencia
download = True
saveReference = False
resourcesPath = "./resources"

reference = np.zeros((cameraConfig["height"], cameraConfig["width"]), dtype=np.complex128)

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

#-----------------------Clases------------------------------
# Clase para abstraer el uso de la cámara
class Camera:
    def __init__(self, source=0, width=640, height=480, exposure_time = 50):
        self.source = source
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.capture = None

    def open(self):
        self.capture = cv2.VideoCapture(self.source)
        # Verificar si la cámara se ha abierto correctamente
        if not self.capture.isOpened():
            print("Error al abrir la cámara")
            exit()
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75) # Se desactiva el modo automatico
        self.capture.set(cv2.CAP_PROP_EXPOSURE, self.exposure_time)

    def close(self):
        self.capture.release()

    def read(self):
        succes, image = self.capture.read()
        return (succes, image)

    def set_width(self, width):
        self.width = width
        if self.capture is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

    def set_height(self, height):
        self.height = height
        if self.capture is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time
        if self.capture is not None:
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75) # Se desactiva el modo automatico
            self.capture.set(cv2.CAP_PROP_EXPOSURE, self.exposure_time)

    def set_source(self, source):
        self.source = source
        if self.capture is not None:
            self.capture.open(self.source)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
    
    def config(self, cameraConfig):
        if(cameraConfig["flag"]):
            # Se configura el tamaño de la cámara
            self.set_height(cameraConfig["height"])
            self.set_width(cameraConfig["width"])

            # Se configura el tiempo de exposición
            self.set_exposure_time(cameraConfig["exposure"])
            
            # Evitamos que se vuelva a configurar cada que se entre
            cameraConfig["flag"] = False
            return True
        return False


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
    (flag, encodedImage) = cv2.imencode(".jpg", cv2.resize(image, (640,480)))
    if not flag:
        return None
    return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
        bytearray(encodedImage) + b'\r\n')

# Genera continuamente una respuesta basada en la imagen de la cámara y aplica 
# determinadas transformaciones a la imagen
# INPUT
# *transforms: Función que modifica la imagen según las necesidades y debe retornar imagen rgb 
# OUTPUT: String de respuesta con la imagen codificada
def generate(*transforms):
    global download, resourcesPath, cameraConfig
    cap = Camera()
    cap.open()
    try:
        while True:
            # Configuramos la cámara
            cap.config(cameraConfig)
            # Definimos el tiempo de inicio
            start_time = time.time()
            # Capturamos la imagen de la cámara
            succes, frame = cap.read()
            # Re intentamos obtener la imagen en caso de fallar
            while not succes:
                print("La cámará no se pudo abrir, re intentado ...")
                cap.open()
                succes, frame = cap.read()
            
            # Aplicamos las transformaciones pertinentes
            final_frame = frame
            for transform in transforms:
                final_frame = transform(final_frame)

            # Si se solicitó una descarga, se guarda en un archivo la imagen
            if download:
                cv2.imwrite(resourcesPath + "/DHM.jpg" , final_frame)
                download = False

            # Escribimos los FPS sobre la imagen
            fps = int(1.0 / (time.time() - start_time))
            cv2.putText(final_frame, "FPS: {:n}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            yield codeImage(final_frame)
    finally:
        cap.close()
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
    img_filter = img_filter.astype(np.complex128) # Aseguramos el tipo de la imagen
    
    # ----------Desplazar espectro----------
    # Recortamos la imagen filtrada en un cuadrado que limita con el circulo
    ymin, ymax = (max(0,y - radio),max(0,y + radio)) # Evitamos errores de recorte
    xmin, xmax = (max(0,x - radio),max(0,x + radio)) # Evitamos errores de recorte

    cropped_image = img_filter[ymin:ymax,xmin:xmax]

    # Creamos un Padding para que el recorte quede centrado
    rows, cols = img_filter.shape[:2]
    width, heigh = cropped_image.shape[:2]
    
    # Agrega ceros alrededor de la matriz de la imagen
    result = np.zeros((rows, cols), dtype=np.complex128)
    result[(rows - width)//2: (rows + width)//2, (cols - heigh)//2: (cols + heigh)//2] = cropped_image
    # ----------Invertir FFT----------
    result = fftshift(result)
    result = ifft2(result)
    
    # ----------Compensar reconstrucción----------
    global angleX, angleY  # @TODO optimizar para guardar la onda en memoria
    wave = plane_wave(rows, cols, angleX, angleY, 1, 1, 1)
    result = wave*result 

    # ---------- En caso de ser solictado guardamos la nueva referencia ----------
    global saveReference, resourcesPath, reference
    if saveReference:
        save_matrix(resourcesPath, result)
        reference = load_matrix(resourcesPath)
        saveReference = False
    
    # ---------- Restamos la referencia -----------------------------
    result -= reference

    # Convertir a imagen RGB según el modo que corresponda
    if (reconstructionMode =='intensity'):
        result = np.abs(result)**2

    elif (reconstructionMode =='phase'):
        result=np.angle(result)

    elif (reconstructionMode =='amplitude'):
        result=np.abs(result)
    
    result = interpol(result)
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

# Toma una matriz y la almacena en un texto plano
# Input: path (str): Dirección donde se va a almacenar la matrix
#        matrix: matriz a almacenar
#        name: nombre del archivo
# Output: void
def save_matrix(path, matrix, name="data.txt"):
    with open(path + "/" + name, 'w') as f:
        for row in matrix:
            for num in row:
                if num.imag >= 0:
                    f.write(f"{num.real}+{num.imag}j ")
                else:
                    f.write(f"{num.real}{num.imag}j ")
            f.write("\n")

# Toma una matriz en un archivo de texto y la carga como una matriz compleja de numpy
# Input: path (str): Dirección del archivo a cargar
# Output: matrix (numpy array): matriz compleja cargada desde el archivo
def load_matrix(path, name="data.txt"):
    # Leer el archivo de texto
    with open(path + "/" + name, 'r') as f:
        content = f.readlines()

    # Crear una matriz compleja de numpy
    matrix = np.zeros((len(content), len(content[0].split(" ")) -1), dtype=np.complex128)
    # Función para validar si un string es númerico
    def isNumeric(s):
        try:
            complex(s)
            return True
        except ValueError:
            return False
    # Llenar la matriz con los números complejos del archivo
    for i, line in enumerate(content):
        for j, num in enumerate(line.split(" ")):
            if isNumeric(num):
                matrix[i][j] = complex(num)
                
    return matrix

# Toma una matriz de valores reales y los reescala al intervalo 0-255
# Input: image: imagen a reescalar
# Output: Imagen reescalada
def interpol(image):
    # Calcula los valores mínimo y máximo de la matriz
    min_val = np.min(image)
    max_val = np.max(image)

    # Interpola los valores de la matriz en un rango de 0 a 255
    interpolated_matrix = ((image - min_val) / (max_val - min_val)) * 255

    # Convierte los valores de la matriz a enteros de 8 bits sin signo
    interpolated_matrix = interpolated_matrix.astype(np.uint8)

    return interpolated_matrix

# Crea una onda plana
# Inputs:
# M, N: Tamaño de la matriz
# angleX, angleY: Ángulos de la onda
# dx, dy, w_length: tamaños de pixel y longitud de onda
def plane_wave(M,N,angleX,angleY,dx,dy,w_length):
    Mcenter = M//2
    Ncenter = N//2
    
    x = np.arange(-Ncenter, Ncenter + N%2)
    y = np.arange(-Mcenter, Mcenter + M%2)
    
    X, Y = np.meshgrid(x,y)
    
    k = 2*np.pi/w_length
    
    Ax = np.sin(angleX)
    Ay = np.sin(angleY)
    
    wave = np.exp(1j*k*(Ax*X*dx+Ay*Y*dy))
    
    return wave

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

@app.route("/compensation")
def compensation():
    global angleX, angleY
    angleX = float(request.args.get('angleY', angleX))
    angleY = float(request.args.get('angleX', angleY))
    return Response('OK')

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
    global resourcesPath,download
    download = True
    return send_file(resourcesPath + "/DHM.jpg", mimetype='image/jpg')

@app.route("/save_reference")
def save_reference():
    global saveReference
    saveReference = True
    return Response('OK')
#-----------------------Corremos el servidor----------------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
    