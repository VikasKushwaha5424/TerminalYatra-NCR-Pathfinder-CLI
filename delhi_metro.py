import csv
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
        self.g_interchange = nx.Graph() # For minimum interchange pathfinding
        self.station_map = {} # Maps simple name to a full name
        self.station_index_map = {} # Maps simple name to index number
        self.index_station_map = {} # Maps index number to simple name
        self.fare_slabs = [(2, 11), (5, 20), (12, 30), (21, 43), (32, 54), (float('inf'), 64)]
        self.last_path = None # To store the most recent journey
        
        try:
            self._load_data()
            self._build_interchange_graph()
            print(f"{Fore.GREEN}Metro data loaded and graphs built successfully!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}An error occurred during initialization: {e}{Style.RESET_ALL}")
            self.graph = None # Flag to indicate failure

    def _get_simple_name(self, full_name):
        """Creates a simplified, lowercase name from a full station name."""
        return full_name.split('_')[0].strip().lower()

    def _parse_station_lines(self, full_name):
        """Helper to get a set of a station's lines for accurate intersection."""
        if "_(interchange" in full_name:
            match = re.search(r'interchange ([\w\s]+)\)', full_name)
            return set(match.group(1).split(' ')) if match else set()
        else:
            # Assumes the line is the last part after the underscore
            parts = full_name.split('_')
            return {parts[-1]} if len(parts) > 1 else set()

    def _calculate_fare(self, distance):
        """Calculates fare based on distance using the predefined fare slabs."""
        if distance == 0: return 0
        for max_dist, fare in self.fare_slabs:
            if distance <= max_dist: return fare
        return self.fare_slabs[-1][1] # Return max fare if distance is very large

    def _load_data(self):
        """Loads metro data and builds BOTH the simple graph and the NetworkX graph."""
        with open(self.file_path, mode='r', encoding='utf-8') as data_file:
            reader = csv.reader(row for row in data_file if not row.strip().startswith('#'))
            next(reader) # Skip header
            for row in reader:
                if len(row) != 3: continue
                station_u, station_v, distance_str = row
                try:
                    distance = float(distance_str)
                except ValueError: 
                    print(f"Skipping row with invalid distance: {row}")
                    continue
                
                # Populate simple name map and our basic graph
                for station in [station_u, station_v]:
                    if station not in self.graph: self.graph[station] = []
                    simple_name = self._get_simple_name(station)
                    # This map will only hold one full name per simple name
                    # It's mainly for getting *a* valid full name from a simple name
                    if simple_name not in self.station_map: 
                        self.station_map[simple_name] = station
                
                self.graph[station_u].append((station_v, distance))
                self.graph[station_v].append((station_u, distance))
                
                # Build the NetworkX graph with simple names for shortest distance
                simple_u, simple_v = self._get_simple_name(station_u), self._get_simple_name(station_v)
                self.nx_graph.add_edge(simple_u, simple_v, weight=distance)

        self._build_station_indices()

    def _build_station_indices(self):
        """Creates numerical and name-based mappings for all stations."""
        self.station_index_map.clear(); self.index_station_map.clear()
        # Use the station_map (simple names) as the definitive list
        for i, name in enumerate(sorted(self.station_map.keys()), 1):
            self.station_index_map[name] = i
            self.index_station_map[i] = name
            
    def _build_interchange_graph(self):
        """Builds the interchange-aware graph once and stores it."""
        print("Building interchange graph...")
        
        # Collect all unique full station names from the original graph
        all_full_names = set(self.graph.keys())

        # 1. Add interchange (penalty) edges
        for u_full in all_full_names:
            u_simple, u_lines = self._get_simple_name(u_full), self._parse_station_lines(u_full)
            if len(u_lines) > 1: # This is an interchange station
                # Add edges between its different line representations
                for line1, line2 in itertools.combinations(u_lines, 2):
                    self.g_interchange.add_edge((u_simple, line1), (u_simple, line2), weight=self.INTERCHANGE_PENALTY)

        # 2. Add travel (cost = 1) edges
        for u_full, connections in self.graph.items():
            for v_full, _ in connections:
                u_simple, v_simple = self._get_simple_name(u_full), self._get_simple_name(v_full)
                # Find lines that are common to both connected stations
                common_lines = self._parse_station_lines(u_full).intersection(self._parse_station_lines(v_full))
                for line in common_lines:
                    # Add an edge for travel on this specific line
                    # Weight=1 means "1 segment of travel"
                    self.g_interchange.add_edge((u_simple, line), (v_simple, line), weight=1)
        print("Interchange graph built.")

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
        names = list(self.index_station_map.items()) # Use the index map
        if not names:
            print("No stations loaded.")
            return
            
        max_len = len(names)
        col_len = (max_len + 2) // 3 # Calculate length of each column
        for i in range(col_len):
            # Column 1
            col1 = f"{Fore.YELLOW}{names[i][0]:>3}.{Style.RESET_ALL} {names[i][1].title()}" if i < max_len else ""
            # Column 2
            col2_idx = i + col_len
            col2 = f"{Fore.YELLOW}{names[col2_idx][0]:>3}.{Style.RESET_ALL} {names[col2_idx][1].title()}" if col2_idx < max_len else ""
            # Column 3
            col3_idx = i + 2 * col_len
            col3 = f"{Fore.YELLOW}{names[col3_idx][0]:>3}.{Style.RESET_ALL} {names[col3_idx][1].title()}" if col3_idx < max_len else ""
            
            print(f"{col1:<45}{col2:<45}{col3}")

    def find_shortest_path(self, start_station_simple, end_station_simple):
        """Finds the shortest path using the pre-built NetworkX graph."""
        try:
            # Use networkx's optimized Dijkstra for distance and path
            distance = nx.dijkstra_path_length(self.nx_graph, start_station_simple, end_station_simple, weight='weight')
            path_simple = nx.dijkstra_path(self.nx_graph, start_station_simple, end_station_simple, weight='weight')
            
            # Convert simple path back to full names for the directions function
            path_full = [self.station_map[s] for s in path_simple]
            
            self.last_path = path_simple # Store the path
            
            return {"distance": distance, "fare": self._calculate_fare(distance), "path": path_full}
        except nx.NetworkXNoPath:
            print(f"{Fore.RED}No path found between {start_station_simple.title()} and {end_station_simple.title()}{Style.RESET_ALL}")
            self.last_path = None # Clear last path on failure
            return None
        except KeyError as e:
            print(f"{Fore.RED}Error: Station {e} not found in nx_graph.{Style.RESET_ALL}")
            self.last_path = None # Clear last path on failure
            return None


    def find_path_min_interchanges(self, start_station_simple, end_station_simple):
        """Finds the path with the fewest line changes using the pre-built interchange graph."""
        
        best_path, min_cost = None, float('inf')

        # Find all (station, line) nodes in the interchange graph for start and end
        start_nodes = [node for node in self.g_interchange.nodes if node[0] == start_station_simple]
        end_nodes = [node for node in self.g_interchange.nodes if node[0] == end_station_simple]

        if not start_nodes:
            print(f"{Fore.RED}Error: Start station '{start_station_simple}' not found in interchange graph.{Style.RESET_ALL}")
            self.last_path = None
            return None
        if not end_nodes:
            print(f"{Fore.RED}Error: End station '{end_station_simple}' not found in interchange graph.{Style.RESET_ALL}")
            self.last_path = None
            return None

        # Run Dijkstra from all possible start lines to all possible end lines
        for start_node in start_nodes:
            for end_node in end_nodes:
                try:
                    cost, path = nx.single_source_dijkstra(self.g_interchange, start_node, end_node, weight='weight')
                    if cost < min_cost:
                        min_cost, best_path = cost, path
                except nx.NetworkXNoPath:
                    continue
        
        if not best_path:
            print(f"{Fore.RED}No path found between {start_station_simple.title()} and {end_station_simple.title()}{Style.RESET_ALL}"); 
            self.last_path = None
            return None

        # Calculate total distance for this path
        total_distance = 0
        simple_path_deduped = [] # To store for visualization
        for i in range(len(best_path)):
            u_node_simple, u_line = best_path[i]
            
            # Build the simple path for visualization
            if not simple_path_deduped or simple_path_deduped[-1] != u_node_simple:
                simple_path_deduped.append(u_node_simple)

            # Calculate distance
            if i < len(best_path) - 1:
                v_node_simple, v_line = best_path[i+1]
                if u_node_simple != v_node_simple: # Only add distance for travel edges
                    try:
                        # Get distance from the nx_graph (simple names)
                        dist = self.nx_graph[u_node_simple][v_node_simple]['weight']
                        total_distance += dist
                    except KeyError:
                        print(f"{Fore.YELLOW}Warning: Could not find distance for segment {u_node_simple} to {v_node_simple}{Style.RESET_ALL}")
        
        self.last_path = simple_path_deduped # Store the path
        return {"path": best_path, "cost": min_cost, "distance": total_distance, "fare": self._calculate_fare(total_distance)}

    def visualize_map(self, filename="delhi_metro_map_detailed.png"):
        """Creates a beautified PNG of the metro network using the pre-built graph."""
        edges_by_line = {line: [] for line in self.LINE_ORDER}
        edge_weights = {} # To store weights for labeling

        for u_full, connections in self.graph.items():
            for v_full, distance in connections: # Get distance here
                u_simple, v_simple = self._get_simple_name(u_full), self._get_simple_name(v_full)
                common_lines = self._parse_station_lines(u_full).intersection(self._parse_station_lines(v_full))
                
                # Ensure a consistent order for edge_weights key
                edge_key = tuple(sorted(((u_simple, v_simple))))
                if edge_key not in edge_weights: # Store only once per unique edge
                    edge_weights[edge_key] = distance

                for line in common_lines:
                    if line in edges_by_line:
                        edges_by_line[line].append((u_simple, v_simple))

        line_colors_map = {
            'red': '#e51d25', 'yellow': '#f3d325', 'blue': '#2c60a4',
            'green': '#58a742', 'violet': '#6f3f98', 'orange': '#f58220',
            'magenta': '#e4007d', 'pink': '#FF69B4', 'grey': '#a4a6a9',
            'aqua': '#00afad'
        }
        node_sizes, node_colors, labels_to_show = [], [], {}
        
        all_simple_stations = list(self.nx_graph.nodes())

        for station_simple in all_simple_stations:
            full_name_candidate = self.station_map.get(station_simple)
            if full_name_candidate is None:
                print(f"Warning: No full name found for simple station '{station_simple}'.")
                node_sizes.append(80) 
                node_colors.append('lightgrey') 
                continue

            if "_(interchange" in full_name_candidate:
                node_sizes.append(350) # Larger size for interchanges
                node_colors.append('black') # Interchange nodes are black
                labels_to_show[station_simple] = station_simple.title()
            else:
                node_sizes.append(80) # Regular station size
                lines = self._parse_station_lines(full_name_candidate)
                if len(lines) == 1:
                    line = lines.pop()
                    node_colors.append(line_colors_map.get(line, 'grey'))
                else:
                    # Fallback for stations not clearly single-line or data errors
                    node_colors.append('grey') 

        print("\nGenerating map... This may take a moment.")
        
        plt.figure(figsize=(40, 40)) 
        ax = plt.gca()

        # Use kamada_kawai_layout for a clean, map-like structure
        pos = nx.kamada_kawai_layout(self.nx_graph) 

        # Draw edges with increased width
        for line, edges in edges_by_line.items():
            nx.draw_networkx_edges(
                self.nx_graph, pos, edgelist=edges, 
                edge_color=line_colors_map.get(line, 'grey'), 
                width=4.0,
                alpha=0.8
            )

        # Draw nodes with borders
        nx.draw_networkx_nodes(
            self.nx_graph, pos, node_size=node_sizes, 
            node_color=node_colors, 
            linewidths=1.5,
            edgecolors='black'
        )

        # Draw labels for interchange stations
        nx.draw_networkx_labels(
            self.nx_graph, pos, labels=labels_to_show, 
            font_size=12,
            font_weight='bold', 
            font_color='black'
        )

        # Add edge labels (distances)
        edge_labels = {}
        for u, v, data in self.nx_graph.edges(data=True):
            edge_labels[(u, v)] = f"{data['weight']:.1f}"

        nx.draw_networkx_edge_labels(
            self.nx_graph, pos, 
            edge_labels=edge_labels, 
            font_size=7,       # Small font to reduce clutter
            font_color='dimgrey',
            alpha=0.9
        )

        plt.title("Delhi Metro Network Map", size=40, weight='bold', y=1.01)
        
        # Legend
        legend_handles = [plt.Line2D([0], [0], color=c, lw=6, label=l.title())
                          for l, c in line_colors_map.items() if c]
        ax.legend(
            handles=legend_handles, loc='lower left', fontsize=16, 
            title="Metro Lines", title_fontsize=18, 
            frameon=True, fancybox=True, shadow=True, borderpad=1.2
        )

        # Border for the overall plot
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(3.0) 
            spine.set_visible(True) 

        ax.set_frame_on(True)
        plt.axis('on') # Keep frame on
        plt.xticks([]); plt.yticks([]) # But hide the tick marks
        
        plt.tight_layout(pad=2) # Ensure nothing is cut off
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close() # Close the plot to free memory
        print(f"✅ Map successfully saved as '{filename}' in your current directory.")


    def visualize_journey(self):
        """Displays the last calculated path on a faded full map."""
        
        if not self.last_path:
            print(f"{Fore.RED}Error: You must find a path using option 1 or 2 first.{Style.RESET_ALL}")
            input("\nPress Enter to return to the menu...") # Added pause for error
            return

        print("\nGenerating journey map... Close the pop-up window to return to the menu.")
        
        plt.figure(figsize=(25, 25)) # Good size for a pop-up
        ax = plt.gca()
        # Ensure consistent layout with the main map
        pos = nx.kamada_kawai_layout(self.nx_graph)
        
        line_colors_map = {
            'red': '#e51d25', 'yellow': '#f3d325', 'blue': '#2c60a4',
            'green': '#58a742', 'violet': '#6f3f98', 'orange': '#f58220',
            'magenta': '#e4007d', 'pink': '#FF69B4', 'grey': '#a4a6a9',
            'aqua': '#00afad'
        }

        # 1. Draw all line edges lightly (faded)
        edges_by_line = {line: [] for line in self.LINE_ORDER}
        for u_full, connections in self.graph.items():
            for v_full, _ in connections:
                u_simple, v_simple = self._get_simple_name(u_full), self._get_simple_name(v_full)
                common_lines = self._parse_station_lines(u_full).intersection(self._parse_station_lines(v_full))
                for line in common_lines:
                    if line in edges_by_line:
                        edges_by_line[line].append((u_simple, v_simple))

        for line, edges in edges_by_line.items():
            nx.draw_networkx_edges(
                self.nx_graph, pos, edgelist=edges, 
                edge_color=line_colors_map.get(line, 'grey'), 
                width=1.0,  # Thin
                alpha=0.2   # Very light/faded
            )

        # 2. Draw all nodes lightly
        nx.draw_networkx_nodes(
            self.nx_graph, pos, 
            node_size=20,         # Small
            node_color='grey',  
            alpha=0.3
        )

        # 3. Create path edges and labels
        path_edges = list(zip(self.last_path[:-1], self.last_path[1:]))
        path_labels = {station: station.title() for station in self.last_path}

        # 4. Highlight path edges (bold and bright)
        nx.draw_networkx_edges(
            self.nx_graph, pos, edgelist=path_edges, 
            edge_color='#00FFFF', # Bright Cyan
            width=5.0,            # Very bold
            alpha=1.0
        )
        
        # 5. Highlight path nodes (large and bright)
        nx.draw_networkx_nodes(
            self.nx_graph, pos, nodelist=self.last_path, 
            node_size=150,        # Larger
            node_color='#FF0000',   # Bright Red
            edgecolors='black',     # With a border
            linewidths=1
        )
        
        # 6. Draw path labels
        nx.draw_networkx_labels(
            self.nx_graph, pos, labels=path_labels, 
            font_size=10, 
            font_weight='bold'
        )

        plt.title("Your Metro Journey", size=25)
        plt.axis('off')
        plt.tight_layout()
        plt.show() # Display the plot, don't save


# --- Helper and Display Functions ---
def get_station_from_input(prompt, metro_system):
    """Handles user input for stations, accepting either a name or a number."""
    user_input = input(prompt).strip()
    if user_input.isdigit():
        try:
            index = int(user_input)
            station_name = metro_system.index_station_map.get(index)
            if not station_name: 
                print(f"{Fore.RED}Error: Invalid station number.{Style.RESET_ALL}")
            return station_name # Returns None if invalid
        except ValueError:
            print(f"{Fore.RED}Error: Invalid number format.{Style.RESET_ALL}"); 
            return None
    elif user_input:
        simple_name = user_input.lower()
        if simple_name in metro_system.station_map:
            return simple_name
        else:
            print(f"{Fore.RED}Error: Station '{user_input}' not found.{Style.RESET_ALL}"); 
            return None
    return None # Return None if input is empty

def display_path_details(path_info, start, end, metro_system, is_min_interchange=False):
    """A consolidated function to display results for both pathfinding types."""
    title = "Path with Minimum Interchanges" if is_min_interchange else "Shortest Path (by Distance)"
    
    print(f"\n--- {Style.BRIGHT}{title}{Style.RESET_ALL} ---")
    print(f"{Fore.CYAN}From:{Style.RESET_ALL} {start.title()}")
    print(f"{Fore.CYAN}To:{Style.RESET_ALL}    {end.title()}")
    print(f"{Fore.CYAN}Total Distance:{Style.RESET_ALL} {path_info['distance']:.2f} km")
    print(f"{Fore.CYAN}Calculated Fare:{Style.RESET_ALL} Rs. {path_info['fare']}")
    
    if is_min_interchange:
        # Cost = (hops * 1) + (interchanges * 100)
        # Integer division by 100 gives the number of interchanges.
        interchanges = int(path_info['cost'] // metro_system.INTERCHANGE_PENALTY)
        print(f"{Fore.CYAN}Total Interchanges:{Style.RESET_ALL} {interchanges}")
        
    print(f"{Style.DIM}{'-' * 40}{Style.RESET_ALL}")
    
    if is_min_interchange: 
        display_min_interchanges_directions(path_info['path'])
    else: 
        display_directions(path_info['path'], metro_system)

def display_directions(path, metro_system):
    """Generates human-readable directions for a distance-based path."""
    print(f"{Style.BRIGHT}--- Directions ---{Style.RESET_ALL}")
    
    if not path or len(path) < 2:
        print(f"{Fore.RED}Cannot generate directions for this path.{Style.RESET_ALL}")
        return

    try:
        start_lines = metro_system._parse_station_lines(path[0])
        second_lines = metro_system._parse_station_lines(path[1])
        common_line_set = start_lines & second_lines
        
        if not common_line_set:
            # Fallback: just use one of the start station's lines
            current_line = list(start_lines)[0] if start_lines else "Unknown"
            print(f"{Fore.YELLOW}Warning: No common line to start. Defaulting to {current_line} line.{Style.RESET_ALL}")
        else:
            current_line = common_line_set.pop()

        print(f"  Start at {Style.BRIGHT}{metro_system._get_simple_name(path[0]).title()}{Style.RESET_ALL} on the {Fore.MAGENTA}{current_line.title()}{Style.RESET_ALL} line")

        for i in range(1, len(path)):
            current_name = metro_system._get_simple_name(path[i]).title()
            print(f"  Travel to {Style.BRIGHT}{current_name}{Style.RESET_ALL}")
            
            if i < len(path) - 1:
                # Check for line change
                current_station_lines = metro_system._parse_station_lines(path[i])
                next_station_lines = metro_system._parse_station_lines(path[i+1])
                next_line_of_travel_set = (current_station_lines & next_station_lines)
                
                if not next_line_of_travel_set:
                    print(f"{Fore.YELLOW}  Warning: Cannot determine line after {current_name}.{Style.RESET_ALL}")
                    continue
                
                next_line_of_travel = next_line_of_travel_set.pop()
                
                if next_line_of_travel != current_line:
                    print(f"  {Fore.YELLOW}Change at {Style.BRIGHT}{current_name}{Style.RESET_ALL} to the {Fore.MAGENTA}{next_line_of_travel.title()}{Style.RESET_ALL} line")
                    current_line = next_line_of_travel
    except Exception as e:
        print(f"{Fore.RED}An error occurred during direction generation: {e}{Style.RESET_ALL}")


def display_min_interchanges_directions(path):
    """Generates human-readable directions for an interchange-based path."""
    print(f"{Style.BRIGHT}--- Directions ---{Style.RESET_ALL}")
    
    if not path:
        print(f"{Fore.RED}No path to display directions for.{Style.RESET_ALL}")
        return

    station, line = path[0]
    print(f"  Start at {Style.BRIGHT}{station.title()}{Style.RESET_ALL} on the {Fore.MAGENTA}{line.title()}{Style.RESET_ALL} line")
    
    for i in range(1, len(path)):
        prev_station, prev_line = path[i-1]
        curr_station, curr_line = path[i]
        
        if prev_station == curr_station and prev_line != curr_line:
            # This is an interchange
            print(f"  {Fore.YELLOW}Change at {Style.BRIGHT}{curr_station.title()}{Style.RESET_ALL} to the {Fore.MAGENTA}{curr_line.title()}{Style.RESET_ALL} line")
        elif prev_station != curr_station:
            # This is travel
            print(f"  Travel to {Style.BRIGHT}{curr_station.title()}{Style.RESET_ALL}")

def main():
    """The main function to run the command-line interface."""
    init(autoreset=True) # Initialize Colorama
    
    # --- IMPORTANT ---
    # Make sure this CSV file is in the same directory as your Python script
    csv_file_path = 'delhi_metro_edges.csv'
    
    metro_system = DelhiMetro(csv_file_path)
    if not metro_system.graph: 
        print(f"{Fore.RED}Failed to load metro data. Exiting.{Style.RESET_ALL}")
        sys.exit(1)

    while True:
        clear_screen()
        print(f"\n{Style.BRIGHT}{Fore.YELLOW}===== Delhi Metro Assistant ====={Style.RESET_ALL}")
        print(f"{Fore.CYAN}--- Pathfinding ---{Style.RESET_ALL}")
        print("1. Find Shortest Path & Directions (by Distance)")
        print("2. Find Path with Minimum Interchanges")
        print(f"\n{Fore.CYAN}--- Network Info ---{Style.RESET_ALL}")
        print("3. Show All Stations (with numbers)")
        print("4. Show Fare Slabs")
        print("5. Visualize Metro Map (Save as PNG)")
        print(f"6. {Style.BRIGHT}Visualize Last Journey{Style.RESET_ALL}")
        print(f"\n{Fore.RED}q. Quit{Style.RESET_ALL}")
        choice = input(f"{Fore.GREEN}\nEnter your choice: {Style.RESET_ALL}").strip().lower()

        should_pause = True # Flag to control the "Press Enter" prompt

        if choice in ['1', '2']:
            start = get_station_from_input("\nEnter starting station (name or number): ", metro_system)
            if not start: 
                input("\nPress Enter to return to the menu...")
                continue
                
            end = get_station_from_input("Enter destination station (name or number): ", metro_system)
            if not end: 
                input("\nPress Enter to return to the menu...")
                continue
                
            if start == end:
                print(f"{Fore.YELLOW}Start and destination stations are the same!{Style.RESET_ALL}")
                input("\nPress Enter to return to the menu...")
                continue

            # `start` and `end` are guaranteed to be valid simple names here
            
            path_details = None
            if choice == '1':
                path_details = metro_system.find_shortest_path(start, end)
            else:
                path_details = metro_system.find_path_min_interchanges(start, end)
                
            if path_details:
                display_path_details(path_details, start, end, metro_system, is_min_interchange=(choice == '2'))

        elif choice == '3': 
            metro_system.display_station_list()
        elif choice == '4': 
            metro_system.show_fare_slabs()
        elif choice == '5': 
            metro_system.visualize_map()
        elif choice == '6':
            metro_system.visualize_journey()
            should_pause = False # Don't pause, plt.show() handles it
        elif choice == 'q':
            print(f"{Fore.YELLOW}Thank you for using the Delhi Metro Assistant!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        
        if should_pause:
            # Pause to let the user see the output before clearing
            input("\nPress Enter to return to the menu...")

if __name__ == "__main__":
    main()