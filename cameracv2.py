# Librerias para procesamiento de imagenes
import cv2
import numpy as np
import threading
import time
# Clase para abstraer el uso de la cámara
class Camera:
    def __start_config(self):
        self.stop = True
        time.sleep(1)
    def __end_config(self):
        self.stop = False
        self.thread = threading.Thread(target=self.generate_frame)
        self.thread.start()
    def __init__(self, source=0, width=640, height=480, exposure_time = 50):
        self.source = source
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.capture = None
        self.image = np.zeros((self.height, self.width, 3), dtype = np.uint8)
        self.stop = False
        self.image_captured = False
        self.succes = True

    def generate_frame(self):
        while True:
            self.succes, self.image = self.capture.read()
            self.image_captured = True
            if self.stop:
                break
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
        self.succes, self.image = self.capture.read()
        time.sleep(2)
        self.thread = threading.Thread(target=self.generate_frame)
        self.thread.start()
        time.sleep(2)

    def close(self):
        self.capture.release()

    def read(self):
        while( not (self.image_captured)):
            time.sleep(0.001)
        self.image_captured = False
        return self.succes, self.image

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
            self.__start_config()
            # Se configura el tamaño de la cámara
            self.set_height(cameraConfig["height"])
            self.set_width(cameraConfig["width"])

            # Se configura el tiempo de exposición
            self.set_exposure_time(cameraConfig["exposure"])
            
            # Evitamos que se vuelva a configurar cada que se entre
            cameraConfig["flag"] = False
            self.__end_config()
            return True
        return False
