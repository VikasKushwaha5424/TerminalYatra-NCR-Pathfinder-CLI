import csv
import heapq
import sys
import re
import itertools
import os
import networkx as nx
import matplotlib.pyplot as plt

# Import libraries for a beautiful CLI
from colorama import Fore, Style, init
from rich.console import Console
from rich.table import Table

def clear_screen():
    """Clears the terminal screen for a cleaner interface."""
    os.system('cls' if os.name == 'nt' else 'clear')

class DelhiMetro:
    """
    A class to represent the Delhi Metro network, with multiple pathfinding algorithms.
    """
    LINE_ORDER = ['red', 'yellow', 'blue', 'green', 'violet', 'orange', 'magenta', 'pink', 'grey', 'aqua']
    INTERCHANGE_PENALTY = 100

    def __init__(self, file_path):
        self.file_path = file_path
        self.graph = {} # Original graph for raw connections
        self.nx_graph = nx.Graph() # NetworkX graph for optimized pathfinding
        self.station_map = {}
        self.station_index_map = {}
        self.index_station_map = {}
        self.fare_slabs = [(2, 11), (5, 20), (12, 30), (21, 43), (32, 54), (float('inf'), 64)]
        self._load_data()

    def _get_simple_name(self, full_name):
        """Creates a simplified, lowercase name from a full station name."""
        return full_name.split('_')[0].strip().lower()

    def _parse_station_lines(self, full_name):
        """Helper to get a set of a station's lines for accurate intersection."""
        if "_(interchange" in full_name:
            match = re.search(r'interchange ([\w\s]+)\)', full_name)
            return set(match.group(1).split(' ')) if match else set()
        else:
            return {full_name.split('_')[-1]}

    def _calculate_fare(self, distance):
        """Calculates fare based on distance using the predefined fare slabs."""
        if distance == 0: return 0
        for max_dist, fare in self.fare_slabs:
            if distance <= max_dist: return fare
        return self.fare_slabs[-1][1]

    def _load_data(self):
        """Loads metro data and builds BOTH the simple graph and the NetworkX graph."""
        try:
            with open(self.file_path, mode='r', encoding='utf-8') as data_file:
                reader = csv.reader(row for row in data_file if not row.strip().startswith('#'))
                next(reader) # Skip header
                for row in reader:
                    if len(row) != 3: continue
                    station_u, station_v, distance_str = row
                    try:
                        distance = float(distance_str)
                    except ValueError: continue
                    
                    # Populate simple name map and our basic graph
                    for station in [station_u, station_v]:
                        if station not in self.graph: self.graph[station] = []
                        simple_name = self._get_simple_name(station)
                        if simple_name not in self.station_map: self.station_map[simple_name] = station
                    
                    self.graph[station_u].append((station_v, distance))
                    self.graph[station_v].append((station_u, distance))
                    
                    # OPTIMIZATION: Build the NetworkX graph at the same time
                    simple_u, simple_v = self._get_simple_name(station_u), self._get_simple_name(station_v)
                    self.nx_graph.add_edge(simple_u, simple_v, weight=distance)

            self._build_station_indices()
            print(f"{Fore.GREEN}Metro data loaded successfully!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}An error occurred while loading data: {e}{Style.RESET_ALL}")
            self.graph = None

    def _build_station_indices(self):
        """Creates numerical and name-based mappings for all stations."""
        self.station_index_map.clear(); self.index_station_map.clear()
        for i, name in enumerate(sorted(self.station_map.keys()), 1):
            self.station_index_map[name] = i
            self.index_station_map[i] = name

    def show_fare_slabs(self):
        """Displays the current fare structure using a rich Table."""
        console = Console()
        table = Table(title="\nDelhi Metro Fare Slabs", show_header=True, header_style="bold magenta", border_style="dim")
        table.add_column("Distance (km)", style="cyan", no_wrap=True)
        table.add_column("Fare (Rs)", style="green", justify="right")
        last_dist = 0
        for max_dist, fare in self.fare_slabs:
            dist_range = f"> {last_dist}" if max_dist == float('inf') else f"Up to {max_dist}"
            table.add_row(dist_range, f"₹ {fare}")
            last_dist = max_dist
        console.print(table)

    def display_station_list(self):
        """Prints a numbered, alphabetized list of all stations in columns."""
        print("\n--- List of All Metro Stations ---")
        names = list(self.index_station_map.items())
        max_len = len(names)
        col_len = (max_len + 2) // 3
        for i in range(col_len):
            col1 = f"{Fore.YELLOW}{names[i][0]:>3}.{Style.RESET_ALL} {names[i][1].title()}" if i < max_len else ""
            col2 = f"{Fore.YELLOW}{names[i + col_len][0]:>3}.{Style.RESET_ALL} {names[i + col_len][1].title()}" if (i + col_len) < max_len else ""
            col3 = f"{Fore.YELLOW}{names[i + 2 * col_len][0]:>3}.{Style.RESET_ALL} {names[i + 2 * col_len][1].title()}" if (i + 2 * col_len) < max_len else ""
            print(f"{col1:<45}{col2:<45}{col3}")

    def find_shortest_path(self, start_station_simple, end_station_simple):
        """Finds the shortest path using the pre-built NetworkX graph."""
        try:
            # REFACTORED: Use networkx's optimized Dijkstra for distance and path
            distance = nx.dijkstra_path_length(self.nx_graph, start_station_simple, end_station_simple, weight='weight')
            path_simple = nx.dijkstra_path(self.nx_graph, start_station_simple, end_station_simple, weight='weight')
            
            # Convert simple path back to full names for the directions function
            path_full = [self.station_map[s] for s in path_simple]
            
            return {"distance": distance, "fare": self._calculate_fare(distance), "path": path_full}
        except nx.NetworkXNoPath:
            print(f"No path found between {start_station_simple} and {end_station_simple}")
            return None

    def find_path_min_interchanges(self, start_station_simple, end_station_simple):
        """Finds the path with the fewest line changes using a weighted graph."""
        g_interchange = nx.Graph()
        for u_full in self.graph:
            u_simple, u_lines = self._get_simple_name(u_full), self._parse_station_lines(u_full)
            if len(u_lines) > 1:
                for line1, line2 in itertools.combinations(u_lines, 2):
                    g_interchange.add_edge((u_simple, line1), (u_simple, line2), weight=self.INTERCHANGE_PENALTY)
        for u_full, connections in self.graph.items():
            for v_full, _ in connections:
                u_simple, v_simple = self._get_simple_name(u_full), self._get_simple_name(v_full)
                common_lines = self._parse_station_lines(u_full).intersection(self._parse_station_lines(v_full))
                for line in common_lines:
                    g_interchange.add_edge((u_simple, line), (v_simple, line), weight=1)

        best_path, min_cost = None, float('inf')
        for start_node in (node for node in g_interchange.nodes if node[0] == start_station_simple):
            for end_node in (node for node in g_interchange.nodes if node[0] == end_station_simple):
                try:
                    cost, path = nx.single_source_dijkstra(g_interchange, start_node, end_node)
                    if cost < min_cost:
                        min_cost, best_path = cost, path
                except nx.NetworkXNoPath: continue
        
        if not best_path:
            print(f"No path found between {start_station_simple} and {end_station_simple}"); return None

        total_distance = 0
        for i in range(len(best_path) - 1):
            if best_path[i][0] != best_path[i+1][0]:
                u_full, v_full = self.station_map[best_path[i][0]], self.station_map[best_path[i+1][0]]
                dist = next((d for n, d in self.graph[u_full] if n == v_full), 0)
                total_distance += dist
        
        return {"path": best_path, "cost": min_cost, "distance": total_distance, "fare": self._calculate_fare(total_distance)}

    def visualize_map(self, filename="delhi_metro_map.png"):
        """Creates a beautified PNG of the metro network using the pre-built graph."""
        edges_by_line = {line: [] for line in self.LINE_ORDER}
        for u_full, connections in self.graph.items():
            for v_full, _ in connections:
                u_simple, v_simple = self._get_simple_name(u_full), self._get_simple_name(v_full)
                common_lines = self._parse_station_lines(u_full).intersection(self._parse_station_lines(v_full))
                for line in common_lines:
                    if line in edges_by_line:
                        edges_by_line[line].append((u_simple, v_simple))
        
        line_colors_map = {'red': '#e51d25', 'yellow': '#f3d325', 'blue': '#2c60a4','green': '#58a742', 'violet': '#6f3f98', 'orange': '#f58220', 'magenta': '#e4007d', 'pink': '#FF69B4', 'grey': '#a4a6a9','aqua': '#00afad'}
        node_sizes, node_colors, labels_to_show = [], [], {}

        for station_simple in self.nx_graph.nodes():
            full_name = self.station_map[station_simple]
            if "_(interchange" in full_name:
                node_sizes.append(350); node_colors.append('black'); labels_to_show[station_simple] = station_simple.title()
            else:
                node_sizes.append(80); line = self._parse_station_lines(full_name).pop(); node_colors.append(line_colors_map.get(line, 'grey'))

        print("\nGenerating map... This may take a moment.")
        plt.figure(figsize=(40, 40)); ax = plt.gca()
        pos = nx.kamada_kawai_layout(self.nx_graph)
        for line, edges in edges_by_line.items():
            nx.draw_networkx_edges(self.nx_graph, pos, edgelist=edges, edge_color=line_colors_map.get(line, 'grey'), width=2.5)
        nx.draw_networkx_nodes(self.nx_graph, pos, node_size=node_sizes, node_color=node_colors)
        nx.draw_networkx_labels(self.nx_graph, pos, labels=labels_to_show, font_size=10, font_weight='bold')
        
        plt.title("Delhi Metro Network Map", size=40)
        legend_handles = [plt.Line2D([0], [0], color=c, lw=4, label=l.title()) for l, c in line_colors_map.items() if c]
        ax.legend(handles=legend_handles, loc='lower left', fontsize=16, title="Metro Lines", title_fontsize=18)
        for spine in ax.spines.values():
            spine.set_edgecolor('black'); spine.set_linewidth(1.5)
        ax.set_frame_on(True); plt.axis('off')
        plt.savefig(filename, dpi=300, bbox_inches='tight'); plt.close()
        print(f"✅ Map successfully saved as '{filename}' in your current directory.")

# --- Helper and Display Functions ---
def get_station_from_input(prompt, metro_system):
    """Handles user input for stations, accepting either a name or a number."""
    user_input = input(prompt).strip()
    if user_input.isdigit():
        try:
            index = int(user_input)
            station_name = metro_system.index_station_map.get(index)
            if not station_name: print(f"{Fore.RED}Error: Invalid station number.{Style.RESET_ALL}")
            return station_name
        except ValueError:
            print(f"{Fore.RED}Error: Invalid number format.{Style.RESET_ALL}"); return None
    elif user_input:
        return user_input.lower()
    return None

def display_path_details(path_info, start, end, metro_system, is_min_interchange=False):
    """A consolidated function to display results for both pathfinding types."""
    title = "Path with Minimum Interchanges" if is_min_interchange else "Shortest Path (by Distance)"
    
    print(f"\n--- {Style.BRIGHT}{title}{Style.RESET_ALL} ---")
    print(f"{Fore.CYAN}From:{Style.RESET_ALL} {start.title()}")
    print(f"{Fore.CYAN}To:{Style.RESET_ALL}   {end.title()}")
    print(f"{Fore.CYAN}Total Distance:{Style.RESET_ALL} {path_info['distance']:.2f} km")
    print(f"{Fore.CYAN}Calculated Fare:{Style.RESET_ALL} Rs. {path_info['fare']}")
    
    if is_min_interchange:
        print(f"{Fore.CYAN}Total Interchanges:{Style.RESET_ALL} {int(path_info['cost'] // 100)}")
        
    print(f"{Style.DIM}{'-' * 40}{Style.RESET_ALL}")
    
    if is_min_interchange: display_min_interchanges_directions(path_info['path'])
    else: display_directions(path_info['path'], metro_system)

def display_directions(path, metro_system):
    """Generates human-readable directions for a distance-based path."""
    print(f"{Style.BRIGHT}--- Directions ---{Style.RESET_ALL}")
    start_lines = metro_system._parse_station_lines(path[0]); second_lines = metro_system._parse_station_lines(path[1])
    current_line = (start_lines & second_lines).pop()
    print(f"  Start at {Style.BRIGHT}{metro_system._get_simple_name(path[0]).title()}{Style.RESET_ALL} on the {Fore.MAGENTA}{current_line.title()}{Style.RESET_ALL} line")

    for i in range(1, len(path)):
        current_name = metro_system._get_simple_name(path[i]).title()
        print(f"  Travel to {Style.BRIGHT}{current_name}{Style.RESET_ALL}")
        if i < len(path) - 1:
            next_lines = metro_system._parse_station_lines(path[i+1]); current_lines = metro_system._parse_station_lines(path[i])
            next_line_of_travel = (current_lines & next_lines).pop()
            if next_line_of_travel != current_line:
                print(f"  {Fore.YELLOW}Change at {Style.BRIGHT}{current_name}{Style.RESET_ALL} to the {Fore.MAGENTA}{next_line_of_travel.title()}{Style.RESET_ALL} line")
                current_line = next_line_of_travel

def display_min_interchanges_directions(path):
    """Generates human-readable directions for an interchange-based path."""
    print(f"{Style.BRIGHT}--- Directions ---{Style.RESET_ALL}")
    station, line = path[0]
    print(f"  Start at {Style.BRIGHT}{station.title()}{Style.RESET_ALL} on the {Fore.MAGENTA}{line.title()}{Style.RESET_ALL} line")
    for i in range(1, len(path)):
        prev_station, prev_line = path[i-1]
        curr_station, curr_line = path[i]
        if prev_station == curr_station and prev_line != curr_line:
            print(f"  {Fore.YELLOW}Change at {Style.BRIGHT}{curr_station.title()}{Style.RESET_ALL} to the {Fore.MAGENTA}{curr_line.title()}{Style.RESET_ALL} line")
        elif prev_station != curr_station:
            print(f"  Travel to {Style.BRIGHT}{curr_station.title()}{Style.RESET_ALL}")

def main():
    """The main function to run the command-line interface."""
    init(autoreset=True) # Initialize Colorama
    csv_file_path = 'delhi_metro_edges.csv'
    metro_system = DelhiMetro(csv_file_path)
    if not metro_system.graph: sys.exit(1)

    while True:
        clear_screen()
        print(f"\n{Style.BRIGHT}{Fore.YELLOW}===== Delhi Metro Assistant ====={Style.RESET_ALL}")
        print(f"{Fore.CYAN}--- Pathfinding ---{Style.RESET_ALL}")
        print("1. Find Shortest Path & Directions")
        print("2. Find Path with Minimum Interchanges")
        print(f"\n{Fore.CYAN}--- Network Info ---{Style.RESET_ALL}")
        print("3. Show All Stations (with numbers)")
        print("4. Show Fare Slabs")
        print("5. Visualize Metro Map (Save as PNG)")
        print(f"\n{Fore.RED}q. Quit{Style.RESET_ALL}")
        choice = input(f"{Fore.GREEN}\nEnter your choice: {Style.RESET_ALL}").strip().lower()

        if choice in ['1', '2']:
            start = get_station_from_input("\nEnter starting station (name or number): ", metro_system)
            if not start: continue
            end = get_station_from_input("Enter destination station (name or number): ", metro_system)
            if not end: continue
            if start not in metro_system.station_map or end not in metro_system.station_map:
                print(f"{Fore.RED}Error: One or both station names are invalid.{Style.RESET_ALL}"); continue
            
            path_details = metro_system.find_shortest_path(start, end) if choice == '1' else metro_system.find_path_min_interchanges(start, end)
            if path_details:
                display_path_details(path_details, start, end, metro_system, is_min_interchange=(choice == '2'))

        elif choice == '3': metro_system.display_station_list()
        elif choice == '4': metro_system.show_fare_slabs()
        elif choice == '5': metro_system.visualize_map()
        elif choice == 'q':
            print(f"{Fore.YELLOW}Thank you for using the Delhi Metro Assistant!{Style.RESET_ALL}"); break
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        
        input("\nPress Enter to return to the menu...")

if __name__ == "__main__":
    main()