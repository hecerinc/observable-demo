---
toc: false
theme: dashboard
---


## Air Monitor Map

```js
const div = display(document.createElement("div"));
div.style = "height: 400px;";

const center = { lat: 30.27, lng: -97.74 };
const map = L.map(div)
  .setView([center.lat, center.lng], 13);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})
  .addTo(map);
```
