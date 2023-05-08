import numpy as np

cameraConfig = {"exposure": 50, "gain": 1, "width": 640, "height": 480, "flag": True} # Configuración de la cámara
state = {"circle": False, "fourier": False, "reconstruction": False, "grid": False } # Estado de la imagen transmitida
angleX, angleY = (0,0) # Angúlos de la onda plana de compensación 
reference = np.zeros((cameraConfig["height"], cameraConfig["width"]), dtype=np.complex128)
radio,x,y = (0,0,0) # Circulo para la reconstrucción
reconstructionMode = "intensity" # Modo de la transformación de reconstrucción
# Variables para la descarga y referencia
download = True
saveReference = False
resourcesPath = "./resources"

cameraType = "picamera" # picamera or cv2