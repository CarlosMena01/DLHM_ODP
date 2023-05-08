#-----------------------Librerías----------------------------
# Librerias para streaming
from flask import Flask, render_template, Response, request, send_file
from threading import Thread
# Librerías de manejo de tiempo
import time
from filters import *
import config

# Importamos la cámara según la librería solicitada
if config.cameraType == "cv2":
    from .camera import *
else:
    from .picamera import *

# Genera continuamente una respuesta basada en la imagen de la cámara y aplica 
# determinadas transformaciones a la imagen
# INPUT
# *transforms: Función que modifica la imagen según las necesidades y debe retornar imagen rgb 
# OUTPUT: String de respuesta con la imagen codificada
def generate(*transforms):
    cap = Camera()
    cap.open()
    try:
        while True:
            # Configuramos la cámara
            cap.config(config.cameraConfig)
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
            if config.download:
                cv2.imwrite(config.resourcesPath + "/DHM.jpg" , final_frame)
                config.download = False

            # Escribimos los FPS sobre la imagen
            fps = int(1.0 / (time.time() - start_time))
            cv2.putText(final_frame, "FPS: {:n}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            yield codeImage(final_frame)
    finally:
        cap.close()

# Codifica una imagen y se envía en forma de string para el navegador
# INPUT image: imagen que se desea codificar
# OUTPUT String que puede ser recibido por el cliente
def codeImage(image):
    (flag, encodedImage) = cv2.imencode(".jpg", cv2.resize(image, (640,480)))
    if not flag:
        return None
    return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
        bytearray(encodedImage) + b'\r\n')

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

@app.route("/compensation")
def compensation():
    config.angleX = float(request.args.get('angleY', config.angleX))
    config.angleY = float(request.args.get('angleX', config.angleY))
    return Response('OK')

@app.route("/add_circle")
def add_circle():
    config.radio = int(request.args.get('radio', 0))
    config.x = int(request.args.get('x', 0))
    config.y = int(request.args.get('y', 0))
    return Response('OK')

@app.route("/config_camera")
def config_camera():
    config.cameraConfig["exposure"]  = int(request.args.get("exposure", config.cameraConfig["exposure"]))
    config.cameraConfig["gain"]  = int(request.args.get("gain", config.cameraConfig["gain"]))
    config.cameraConfig["height"]  = int(request.args.get("height", config.cameraConfig["height"]))
    config.cameraConfig["width"]  = int(request.args.get("width", config.cameraConfig["width"]))

    config.cameraConfig["flag"] = True  # Permitimos que se ejecute la configuración establecida
    return Response('OK')

@app.route("/config_reconstruction")
def config_reconstruction():
    mode = request.args.get('mode', "") # Variable temporal
    if (mode.lower() == 'intensity'):
        config.reconstructionMode = 'intensity'
    elif (mode.lower() == 'phase'):
        config.reconstructionMode = 'phase'
    elif (mode.lower() == 'amplitude'):
        config.reconstructionMode = 'amplitude'
    else:
        return Response('NO WORK')
    return Response('OK')

@app.route("/config_state")
def config_state():
    config.state["circle"]          = str2bool(request.args.get('circle', False))
    config.state["fourier"]         = str2bool(request.args.get('fourier', False))
    config.state["reconstruction"]  = str2bool(request.args.get('reconstruction', False))
    config.state["grid"]            = str2bool(request.args.get('grid', False))

    return Response('OK')

@app.route("/video_feed")
def video_feed():
    return Response(generate(apply_fourier_transform, draw_circle, apply_DHM_reconstruction, add_coordinate_axes), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/download_feed")
def download_feed():
    config.download = True
    return send_file(config.resourcesPath + "/DHM.jpg", mimetype='image/jpg')

@app.route("/save_reference")
def save_reference():
    config.saveReference = True
    return Response('OK')