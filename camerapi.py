# Librería para procesamiento de imágenes con Picamera
from picamera import PiCamera
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
    def __init__(self, source=0, width=3008, height=3008, exposure_time=50, max_width = 4056, max_height = 3040):
        self.source = source
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.camera = None
        self.max_width = max_width
        self.max_height = max_height
        self.image = np.empty((self.height, self.width, 3), dtype = np.uint8)
        self.stop = False
        self.capture = False

    def generate_frame(self):
        for image in self.camera.capture_continuous(self.image, "bgr"):
            self.image = image
            self.capture = True
            if self.stop:
                break

    def open(self):
        self.camera = PiCamera()
        self.camera.framerate = 30
        # Configuramos la resolución y el ROI
        self.camera.resolution = (self.width, self.height)
        self.camera.zoom = (0,0,float(self.width/self.max_width),float(self.height/self.max_height))
        # Configuramos el tiempo de exposición y la ganacia
        self.camera.exposure_mode = 'off'
        self.camera.shutter_speed = self.exposure_time
        self.camera.iso = 100
        # Iniciamos el hilo de cáptura
        self.camera.start_preview()
        time.sleep(2)
        self.thread = threading.Thread(target=self.generate_frame)
        self.thread.start()

    def close(self):
        self.camera.close()

    def read(self):
        while( not (self.capture)):
            time.sleep(0.001)
        self.capture = False
        return True, self.image

    def set_width(self, width):
        self.width = width
        self.camera.resolution = (self.width, self.height)

    def set_height(self, height):
        self.height = height
        self.camera.resolution = (self.width, self.height)

    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time
        if self.camera is not None:
            self.camera.shutter_speed = self.exposure_time

    def set_source(self, source):
        self.source = source

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
