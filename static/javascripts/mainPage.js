/*---------------------Botón de reconstrucción------------*/
// Obtenemos los elementos que necesitamos
const reconstructionBtn = document.getElementById("main-btn-reconstruction");
const phaseBtn = document.getElementById("phase-btn");
const amplitudeBtn = document.getElementById("amplitude-btn");
const intenistyBtn = document.getElementById("intenisty-btn");
const dropdown = document.querySelector(".dropdown");
const dropdownContent = document.querySelector(".dropdown-content");

// Variable global para el modo de la reconstrucción
var modeReconstruction = "instenisty";

// Añadimos eventos a los botones
phaseBtn.addEventListener("click", function () {
  modeReconstruction = "phase";
  reconstructionMode();
  reconstructionBtn.textContent = "Reconstruir fase";
  dropdownContent.classList.remove("show");
});

amplitudeBtn.addEventListener("click", function () {
  modeReconstruction = "amplitude";
  reconstructionMode();
  reconstructionBtn.textContent = "Reconstruir amplitud";
  dropdownContent.classList.remove("show");
});

intenistyBtn.addEventListener("click", function () {
  modeReconstruction = "intensity";
  reconstructionMode();
  reconstructionBtn.textContent = "Reconstruir intensidad";
  dropdownContent.classList.remove("show");
});

// Añadimos un evento al botón del menú desplegable para mostrar y ocultar el menú
dropdown.addEventListener("click", function () {
  dropdownContent.classList.toggle("show");
});

// Añadimos un evento al documento para cerrar el menú desplegable cuando se hace clic fuera de él
document.addEventListener("click", function (event) {
  if (!event.target.closest(".dropdown")) {
    dropdownContent.classList.remove("show");
  }
});

/*-----------------------Sliders reading------------*/

// Tiempo de exposición
const sliderTime = document.getElementById("time");
const timeValue = document.getElementById("time-value");

timeValue.value = sliderTime.value;

sliderTime.oninput = function () {
  timeValue.value = this.value;
  const url = new URL(state.root + "/config_camera");
  url.searchParams.set("exposure", this.value);
  fetch(url);
};

timeValue.oninput = function () {
  sliderTime.value = this.value;
  const url = new URL(state.root + "/config_camera");
  url.searchParams.set("exposure", this.value);
  fetch(url);
};

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
async function reconstructionMode() {
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
  await updateState();
}

// Maneja la acción de mostrar u ocultar la transformada de Fourier
async function toggleFFT() {
  state.reconstruction = false;
  state.fourier = state.fourier ? false : true;
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
