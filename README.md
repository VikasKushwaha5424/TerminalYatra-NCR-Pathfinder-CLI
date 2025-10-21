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

##  Highlights
#### Start
#### option 1 - Find Shortest Path & Directions (by Distance)
<img width="866" height="936" alt="Screenshot 2025-10-21 141615" src="https://github.com/user-attachments/assets/3cb53f1c-82fa-4863-ab4a-c158e6853278" />


#### option 2 - Find Path with Minimum Interchanges
<img width="889" height="944" alt="Screenshot 2025-10-21 141650" src="https://github.com/user-attachments/assets/af6670c4-26f5-4302-98f6-e995a45de416" />


#### option 3 - Show All Stations (with numbers) - totall 260 stations 
<img width="1022" height="937" alt="Screenshot 2025-10-21 141721" src="https://github.com/user-attachments/assets/c6cd72d6-ef4d-454a-b10b-8378c49f8eee" />


#### option 4 -  Show Fare Slabs
<img width="882" height="939" alt="Screenshot 2025-10-21 141805" src="https://github.com/user-attachments/assets/0635b871-f747-449e-a754-49b9a3a9c890" />


#### option 5 -   Visualize Metro Map (Save as PNG)
<img width="865" height="859" alt="Screenshot 2025-10-21 142028" src="https://github.com/user-attachments/assets/03f503ab-c797-4495-9034-0e2605d67962" />


#### option 6 -   Visualize Last Journey
####  overall map with path highlighted
<img width="1918" height="1019" alt="Screenshot 2025-10-21 141900" src="https://github.com/user-attachments/assets/821e68b8-e49c-4e79-a556-e242347b90ca" />

####  zoomed in
<img width="1150" height="592" alt="Screenshot 2025-10-21 141923" src="https://github.com/user-attachments/assets/851956f4-50c4-46be-9055-a36ce00941ad" />




 ## Credit
 #### - Vikas Kushwaha
 #### - connect with me on linkedln www.linkedin.com/in/vikaskushwaha5424


