# 🚇 TerminalYatra: Delhi Metro Pathfinder

A Python CLI for the Delhi Metro network. Find optimal routes by distance or interchanges, calculate fares, and visualize the entire network or a specific journey.

---

## ✨ Features

### Dual Pathfinding:
* **Shortest Path (km):** Finds the route with the absolute minimum distance using Dijkstra's.
* **Easiest Path (Interchanges):** Finds the route with the fewest line changes.

### Dynamic Visualization:
* **Full Network Map:** Generates and saves a high-resolution, color-coded PNG of the entire network.
* **Journey Highlight:** Instantly displays a pop-up map highlighting your last-calculated path on a faded-out background.

### Practical Info:
* **Fare Calculation:** Automatically calculates the fare for your route's distance.
* **Step-by-Step Directions:** Provides clear text directions for your trip.

### Polished CLI:
* **Rich Interface:** A clean, colorful, and user-friendly UI powered by Rich and Colorama.
* **Flexible Input:** Select stations by their full name or their index number from a list.

---

## 🛠️ Tech Stack

* **Python:** The core programming language.
* **NetworkX:** For all graph modeling, manipulation, and pathfinding algorithms.
* **Matplotlib:** For generating both the static network map and the dynamic journey plots.
* **Rich & Colorama:** For creating the beautified command-line interface.

---

## 🧠 How It Works: The Dual-Graph Model

This project uses two different graph models to answer two different questions.

### 1. Shortest Path (by Distance)
This is a simple, weighted graph:
* **Nodes:** `station_name`
* **Edges:** A track connecting two stations.
* **Weight:** The distance in km (e.g., `2.1`).

Dijkstra's algorithm finds the path with the minimum sum of weights.

### 2. Easiest Path (by Interchanges)
This is a more complex graph built to "trick" Dijkstra's into finding the path with the fewest changes:
* **Nodes:** `(station_name, line_color)`
* **Travel Edge:** `('Saket', 'yellow')` to `('Malviya Nagar', 'yellow')`. **Cost = 1**.
* **Interchange Edge:** `('Kashmere Gate', 'red')` to `('Kashmere Gate', 'yellow')`. **Cost = 100** (the `INTERCHANGE_PENALTY`).

By finding the path with the lowest total "cost," the algorithm naturally avoids the 100-point penalty, giving you the path with the minimum number of interchanges.

---

## 📂 The Data: `delhi_metro_edges.csv`

The entire network is built from a single CSV file. The program's accuracy depends entirely on the naming convention in this file:

* **Regular Station:** `saket_yellow`
* **Interchange Station:** `rajiv chowk_(interchange yellow blue)`

The code parses these names to automatically build the graphs.

---




 ## Credit
 #### - Vikas Kushwaha
 #### - connect with me on linkedln www.linkedin.com/in/vikaskushwaha5424


