---
theme: dashboard
title: 'Data'
toc: false
---

## 2024 Air Quality Index Data Plotter


```js
import * as Inputs from "npm:@observablehq/inputs";
const collection = [
	{key: "", text: "Select site"},
	{key: "aqi_0.csv", text: "Monitor 1 - Glenlake"},
	{key: "aqi_1.csv", text: "Monitor 2 - Barton Creek"},
	{key: "aqi_2.csv", text: "Monitor 3 - UT Austin"},
	{key: "aqi_3.csv", text: "Monitor 4 - South Congress"},
	{key: "aqi_4.csv", text: "Monitor 5 - Mueller"},
	{key: "aqi_5.csv", text: "Monitor 6 - East Austin"},
	{key: "aqi_6.csv", text: "Monitory 7 - Dogs Head"},
	{key: "aqi_7.csv", text: "Monitor 8 - Riverside"},
	{key: "aqi_8.csv", text: "Monitor 9 - Garden Valley"},
	{key: "aqi_9.csv", text: "Monitor 10 - Montopolis"}
]
const options = {
  format: (t) => t.text,
  label: 'Select monitor:'
};
const monitor = view(Inputs.select(collection, options));
```

```js
const pollutantOpts = [
	{key: "pm25", text: "PM2.5"},
	{key: "pm10", text: "PM10"},
	{key: "co", text: "CO"},
	{key: "no2", text: "NO2"},
	{key: "o3", text: "O3"},
]
const options = {
  format: (t) => t.text,
  label: 'Choose pollutant:'
};
const pollutant = view(Inputs.select(pollutantOpts, options));
```

```js
const startDate = view(Inputs.date({label: "Start date:", value: null}));
const endDate = view(Inputs.date({label: "End date:", value: null}));
```

```js
let aqi = FileAttachment("./data/aqi_0.csv").csv({typed: true});
```

```js
aqi.forEach(a => {
  a.timestamp = new Date(a.timestamp);
});
```




```js
let filteredData = view(Inputs.button("Click me", {value: [], reduce: () => {
  if(startDate == null || endDate == null) {
    return [];
  }
   return aqi.filter(t => t.timestamp < endDate && t.timestamp >= startDate);
  }}));
```


```js
  filteredData.length !== 0 && display(resize(width => Plot.plot({
      title: "Hourly temperature forecast",
      width,
      x: {type: "utc", ticks: "day", label: null},
      y: {grid: true, inset: 10, label: "Air Quality Index"},
      marks: [
        Plot.dot(filteredData, {x: "timestamp", y: "pm25", stroke: "rgba(75, 190, 190, 1)", fill: 'rgba(75, 190, 190, 0.4)'})
      ]
    })
  ));
```

