# Librerias para procesamiento de imagenes
import numpy as np
from scipy.fftpack import fft2, fftshift, ifft2
import cv2
import optics
import config

#---------------------Decoradores-----------------------------
# Revisa la condición determinada dentro de "state" y si se encuentra desactivada, retorna el input
def validation_transform(condition):
    def validate_function(transform):
        def new_function(image):
            if config.state[condition]:
                return transform(image)
            else:
                return image
        return new_function
    return validate_function

#-----------------------Funciones----------------------------
#-------------------- Data storage-----------------------
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
def image_interpol(image):
    # Calcula los valores mínimo y máximo de la matriz
    min_val = np.min(image)
    max_val = np.max(image)

    # Interpola los valores de la matriz en un rango de 0 a 255
    interpolated_matrix = ((image - min_val) / (max_val - min_val)) * 255

    # Convierte los valores de la matriz a enteros de 8 bits sin signo
    interpolated_matrix = interpolated_matrix.astype(np.uint8)

    result = cv2.cvtColor(cv2.convertScaleAbs(interpolated_matrix), cv2.COLOR_GRAY2RGB)

    return result

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
    magnitude_spectrum = np.log(np.abs(fshift))
    
    # Convertimos la imagen de escala de grises en una imagen RGB
    magnitude_spectrum_rgb = image_interpol(magnitude_spectrum)
    
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

# Reconstruye el holograma 
# INPUT:
# image: imagen del microscopio sin transformaciones
# OUPUT:
# Reconstrucción del holograma en formato de imagen de cv2
@validation_transform("reconstruction")
def apply_DHM_reconstruction(img):
    result = optics.DHM_reconstruction(img, config.x, config.y, config.radio, config.angleX, config.angleY, config.reference)
    # ---------- En caso de ser solictado guardamos la nueva referencia ----------
    if config.saveReference:
        save_matrix(config.resourcesPath, result)
        config.reference = result
        config.saveReference = False

    # Convertir a imagen RGB según el modo que corresponda
    if (config.reconstructionMode =='intensity'):
        result = np.abs(result)**2

    elif (config.reconstructionMode =='phase'):
        result=np.angle(result)

    elif (config.reconstructionMode =='amplitude'):
        result=np.abs(result)
    
    result = image_interpol(result)

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