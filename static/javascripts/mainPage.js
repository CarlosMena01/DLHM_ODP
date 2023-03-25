// Parámetros globales
var root = "http://localhost:5000";

var circle = "False";
var fourier = "False";
var reconstruction = "False";
var grid = "False";

function updateState() {
  const url = new URL(root + "/config_state");
  url.searchParams.set("circle", circle);
  url.searchParams.set("fourier", fourier);
  url.searchParams.set("reconstruction", reconstruction);
  url.searchParams.set("grid", grid);
  fetch(url);
}

function submitCoords() {
  const x = document.getElementById("x").value;
  const y = document.getElementById("y").value;
  const radio = document.getElementById("radius").value;

  const url = new URL(root + "/add_circle");
  url.searchParams.set("radio", radio);
  url.searchParams.set("x", x);
  url.searchParams.set("y", y);

  fetch(url);

  // Watch circle
  reconstruction = "False";
  if (circle === "False") {
    circle = "True";
  } else {
    circle = "False";
  }
  updateState();
}

function toggleGrid() {
  reconstruction = "False";
  if (grid === "False") {
    grid = "True";
  } else {
    grid = "False";
  }
  updateState();
}

function toggleFFT() {
  reconstruction = "False";
  if (fourier === "False") {
    fourier = "True";
  } else {
    fourier = "False";
  }
  updateState();
}

function reconstructionStart() {
  circle = "False";
  fourier = "False";
  grid = "False";
  reconstruction = "True";
  updateState();
}
