# Librería para procesamiento de imágenes con Picamera2
from picamera2 import Picamera2, Preview
import numpy as np
import threading
import time
# Clase para abstraer el uso de la cámara
class Camera:
    def __start_config(self):
        self.camera.stop_preview()
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
        self.image_captured = False

    def generate_frame(self):
        while True:
            self.image = np.asarray(self.camera.capture_array("main"))
            self.image_captured = True
            if self.stop:
                break

    def open(self):
        self.camera = Picamera2()
        self.camera.start_preview(Preview.QTGL)
        # Configuramos la resolución
        print( self.camera.configure(self.camera.create_preview_configuration(lores={"size": (self.width, self.height)}, display="lores")))
        print("--------------------------------------------------------")
        self.camera.set_controls({"ExposureTime": self.exposure_time, "AnalogueGain": 1.0})
        self.camera.start()
        # Iniciamos el hilo de cáptura
        time.sleep(2)
        self.thread = threading.Thread(target=self.generate_frame)
        self.thread.start()

    def close(self):
        self.camera.stop_preview()
        self.camera.close()

    def read(self):
        while( not (self.image_captured)):
            time.sleep(0.001)
        self.image_captured = False
        return True, self.image

    def set_width(self, width):
        self.camera.stop_preview()
        self.width = width
        self.camera.configure(self.camera.create_preview_configuration(lores={"size": (self.width, self.height)}, display="lores"))
        self.camera.start_preview(True)

    def set_height(self, height):
        self.camera.stop_preview()
        self.height = height
        self.camera.configure(self.camera.create_preview_configuration(lores={"size": (self.width, self.height)}, display="lores"))
        self.camera.start_preview(True)

    def set_exposure_time(self, exposure_time):
        self.exposure_time = exposure_time
        if self.camera is not None:
            self.camera.stop_preview()
            self.camera.controls.ExposureTime = self.exposure_time
            self.camera.start_preview(True)

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
