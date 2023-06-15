# Librerias para procesamiento de imagenes
import numpy as np
from scipy.fftpack import fft2, fftshift, ifft2
import cv2

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

def DHM_reconstruction(img, x,y, radio, angleX, angleY, reference):
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
    wave = plane_wave(rows, cols, angleX, angleY, 1, 1, 1)
    result = wave*result 
    
    # ---------- Restamos la referencia -----------------------------
    result = result/reference

    return result
