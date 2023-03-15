function watchCircle() {
  const x = document.getElementById("CX").value;
  const y = document.getElementById("CY").value;
  const radio = document.getElementById("Radio").value;

  const url = new URL("http://localhost:5000/add_circle");
  url.searchParams.set("radio", radio);
  url.searchParams.set("x", x);
  url.searchParams.set("y", y);

  fetch(url)
    .then((response) => {})
    .catch((error) => {});
}

function openReconstruction() {
  window.location.href = "http://localhost:5000/reconstruction";
}
