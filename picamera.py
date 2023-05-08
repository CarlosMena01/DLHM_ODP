# Librería para procesamiento de imágenes con Picamera
from picamera.array import PiRGBArray
from picamera import PiCamera

# Clase para abstraer el uso de la cámara
class Camera:
    def __init__(self, source=0, width=640, height=480, exposure_time=50):
        self.source = source
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.camera = None

    def open(self):
        self.camera = PiCamera(resolution=(self.width, self.height), framerate=30)
        self.camera.iso = 100
        self.camera.exposure_mode = 'off'
        self.camera.shutter_speed = self.exposure_time
        self.raw_capture = PiRGBArray(self.camera, size=(self.width, self.height))
        self.stream = self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True)

    def close(self):
        self.camera.close()

    def read(self):
        raw_frame = next(self.stream)
        image = raw_frame.array
        self.raw_capture.truncate(0)
        return True, image

    def set_width(self, width):
        self.width = width
        if self.camera is not None:
            self.camera.resolution = (self.width, self.height)

    def set_height(self, height):
        self.height = height
        if self.camera is not None:
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
