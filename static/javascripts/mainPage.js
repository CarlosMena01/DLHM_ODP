/*---------------------Botón de reconstrucción------------*/
// Obtenemos los elementos que necesitamos
function configReconstruction(mode) {
  reconstructionMode(mode);
  // Añadimos la clase Active
  const botonPresionado = document.activeElement;
  botonPresionado.classList.toggle("active");
  // Obtener todos los botones y eliminar la clase "active" de los demás
  const botones = document.getElementsByClassName("option-btn");
  for (let i = 0; i < botones.length; i++) {
    if (botones[i] !== botonPresionado) {
      botones[i].classList.remove("active");
    }
  }
  // Hacemos un toggle de la reconstrucción, pero solo si ningún botón
  // Tiene la clase "active" permitimos que se apague
  state.reconstruction = document.getElementsByClassName("active").length === 0;
  /*  Si no hay elementos con clase active state.fourier vale true, y al togglear vale false*/
  toggleReconstruction();
}

/*-----------------------Sliders reading------------*/

function config_slider(slider, value, path, param) {
  value.value = slider.value;

  slider.oninput = function () {
    value.value = this.value;
    const url = new URL(state.root + path);
    url.searchParams.set(param, this.value);
    fetch(url);
  };

  value.oninput = function () {
    slider.value = this.value;
    const url = new URL(state.root + path);
    url.searchParams.set(param, this.value);
    fetch(url);
  };
}

// Tiempo de exposición
const sliderTime = document.getElementById("time");
const timeValue = document.getElementById("time-value");

config_slider(sliderTime, timeValue, "/config_camera", "exposure");

// Angulos
const sliderAngleX = document.getElementById("angleX");
const valueAngleX = document.getElementById("angleX-value");

config_slider(sliderAngleX, valueAngleX, "/compensation", "angleX");

const sliderAngleY = document.getElementById("angleY");
const valueAngleY = document.getElementById("angleY-value");

config_slider(sliderAngleY, valueAngleY, "/compensation", "angleY");

/*----------------------CANVAS READING-------------- */
const canvas = document.getElementById("mainCanvas");
const ctx = canvas.getContext("2d");

let isDrawing = false;
let centerX;
let centerY;
let radius;
// Utiliza la función getCanvasPosition para obtener la posición absoluta del canvas
let canvasPosition = getCanvasPosition(canvas);

function getCanvasPosition(canvas) {
  var left = 0;
  var top = 0;
  var element = canvas;

  while (element) {
    left += element.offsetLeft;
    top += element.offsetTop;
    element = element.offsetParent;
  }

  return { x: left, y: top };
}

canvas.addEventListener("mousedown", function (event) {
  isDrawing = true;

  // Corrige la posición del mouse para tener en cuenta la posición absoluta del canvas
  centerX = event.clientX - canvasPosition.x;
  centerY = event.clientY - canvasPosition.y;
});

canvas.addEventListener("mousemove", function (event) {
  if (isDrawing) {
    console.log(centerX);
    const radiusX = Math.abs(event.clientX - canvasPosition.x - centerX);
    const radiusY = Math.abs(event.clientY - canvasPosition.y - centerY);
    radius = Math.sqrt(radiusX ** 2 + radiusY ** 2);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawCircle(centerX, centerY, radius);
  }
});

canvas.addEventListener("mouseup", function (event) {
  isDrawing = false;
  submitCoords(); // Enviamos los datos al servidor
});

function drawCircle(centerX, centerY, radius) {
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
  ctx.lineWidth = 6;
  ctx.strokeStyle = "orange";
  ctx.stroke();
}

/* ----------------------API INTERACTION------------ */
// Estado de la aplicación
const state = {
  circle: false,
  fourier: false,
  reconstruction: false,
  grid: false,
  root: "http://localhost:5000", // Raíz de la URL de la API
};

// Función auxiliar para crear objetos URL y establecer los parámetros de búsqueda
function createURL(pathname) {
  const url = new URL(state.root + pathname);
  // Recorre el objeto state y establece los parámetros de búsqueda
  Object.entries(state).forEach(([key, value]) => {
    if (key !== "root") {
      // No incluir la propiedad "root" en los parámetros de búsqueda
      url.searchParams.set(key, value.toString());
    }
  });
  return url;
}

// Actualiza el estado de la aplicación en el servidor
async function updateState() {
  const url = createURL("/config_state");
  await fetch(url);
}
// Actualiza el modo para la reconstrucción
async function reconstructionMode(modeReconstruction) {
  const url = new URL(state.root + "/config_reconstruction");
  url.searchParams.set("mode", modeReconstruction);
  await fetch(url);
}

// Maneja la acción de enviar las coordenadas de un círculo al servidor
async function submitCoords() {
  // Construir la URL
  const url = createURL("/add_circle");
  url.searchParams.set("radio", parseInt(radius));
  url.searchParams.set("x", parseInt(centerX));
  url.searchParams.set("y", parseInt(centerY));

  await fetch(url);
}

// Maneja la acción de mostrar u ocultar la cuadrícula
async function toggleGrid() {
  state.grid = state.grid ? false : true;
  document.getElementById("grid-button").textContent =
    (state.grid ? "Hide" : "Show") + " grid";
  await updateState();
}

// Maneja la acción de mostrar u ocultar la transformada de Fourier
async function toggleFFT() {
  state.reconstruction = false;
  state.fourier = state.fourier ? false : true;
  document.getElementById("fft-button").textContent =
    (state.fourier ? "No apply" : "Apply") + " FFT";
  await updateState();
}

// Maneja la acción de iniciar la reconstrucción
async function toggleReconstruction() {
  // Limpiar el canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  state.circle = false;
  state.fourier = false;
  state.grid = false;
  state.reconstruction = state.reconstruction ? false : true;
  await updateState();
}

async function downloadImage() {
  var source = state.root + "/download_feed";

  var a = document.createElement("a");

  a.download = true;
  a.target = "_blank";
  a.href = source;

  a.click();
}

async function saveReference() {
  const url = new URL(state.root + "/save_reference");
  await fetch(url);
}
