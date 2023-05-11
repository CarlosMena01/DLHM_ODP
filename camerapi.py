# Librería para procesamiento de imágenes con Picamera
from picamera import PiCamera
from io import BytesIO
from PIL import Image
import numpy as np
# Clase para abstraer el uso de la cámara
class Camera:
    def __init__(self, source=0, width=3008, height=3008, exposure_time=50, max_width = 4056, max_height = 3040):
        self.source = source
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.camera = None
        self.max_width = max_width
        self.max_height = max_height

    def open(self):
        self.camera = PiCamera()
        # Configuramos la resolución y el ROI
        self.camera.resolution = (self.width, self.height)
        self.camera.zoom = (0,0,float(self.width/self.max_width),float(self.height/self.max_height))
        self.camera.exposure_mode = 'off'
        self.camera.shutter_speed = self.exposure_time
        self.camera.start_preview()
        self.image = np.empty((self.height, self.width, 3), dtype = np.uint8)
        self.camera.capture(self.image, "bgr")

    def close(self):
        self.camera.close()

    def read(self):
        self.image = np.empty((self.height, self.width, 3), dtype = np.uint8)
        self.camera.capture(self.image, "bgr")
        image = self.image
        return True, image

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
            # Se configura el tamaño de la cámara
            self.set_height(cameraConfig["height"])
            self.set_width(cameraConfig["width"])

            # Se configura el tiempo de exposición
            self.set_exposure_time(cameraConfig["exposure"])

            # Evitamos que se vuelva a configurar cada que se entre
            cameraConfig["flag"] = False
            return True
        return False
