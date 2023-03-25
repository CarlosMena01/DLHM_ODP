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

// Maneja la acción de enviar las coordenadas de un círculo al servidor
async function submitCoords() {
  const x = document.getElementById("x").value;
  const y = document.getElementById("y").value;
  const radio = document.getElementById("radius").value;

  const url = createURL("/add_circle");
  url.searchParams.set("radio", radio);
  url.searchParams.set("x", x);
  url.searchParams.set("y", y);

  await fetch(url);

  // Actualiza el estado de la aplicación
  state.reconstruction = false;
  state.circle = state.circle ? false : true;
  await updateState();
}

// Maneja la acción de mostrar u ocultar la cuadrícula
async function toggleGrid() {
  state.reconstruction = false;
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
async function reconstructionStart() {
  state.circle = false;
  state.fourier = false;
  state.grid = false;
  state.reconstruction = true;
  await updateState();
}
