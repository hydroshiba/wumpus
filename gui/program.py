import tkinter as tk
import os

from tkinter import filedialog
import tkinter.messagebox as messagebox

from core import Agent

class Program:
    def __init__(self, root):
        self.running = False
        self.run_interval = 500  # Interval in milliseconds between actions

        self.root = root
        self.root.title("Wumpus World")
        self.health = 100
        self.score = 0
        self.world_map = []
        self.N = 10
        self.logic_steps = []
        self.loaded_map_file = ""
        self.text_position = 10  # To keep track of where to add new text in the logic frame
        self.smoke_image = tk.PhotoImage(file="image/smoke-png-525.png").subsample(5, 5)
        self.smoke_coverage = [[True for _ in range(self.N)] for _ in range(self.N)]

        initial_x, initial_y = 9, 0
        self.smoke_coverage[initial_x][initial_y] = False

        self.agent_position = (9, 0)
        self.agent_direction = "right"

        # Initialize the Agent
        self.agent = Agent()

        # Load the agent images for each direction
        self.agent_images = {
            "up": tk.PhotoImage(file="image/agent_up.png").subsample(2, 2),  # Adjust the subsample factor as needed
            "down": tk.PhotoImage(file="image/agent_down.png").subsample(2, 2),
            "left": tk.PhotoImage(file="image/agent_left.png").subsample(2, 2),
            "right": tk.PhotoImage(file="image/agent_right.png").subsample(2, 2)
        }
        # Create frames
        self.create_menu_frame()
        self.create_map_frame()
        self.create_control_frame()
        self.create_logic_frame()


    def create_menu_frame(self):
        menu_frame = tk.Frame(self.root)
        menu_frame.pack(side="top", fill="x")

        load_button = tk.Button(menu_frame, text="Load Map", command=self.load_map)
        load_button.pack(side="left", padx=5, pady=5)

    def create_map_frame(self):
        self.map_frame = tk.Frame(self.root)
        self.map_frame.pack(side="left", padx=5, pady=5)

        # Create Canvas for the map
        self.canvas = tk.Canvas(self.map_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def create_control_frame(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side="right", fill="y", padx=5, pady=5)

        # Create Buttons
        next_button = tk.Button(control_frame, text="Next Step", command=self.next_step)
        next_button.pack(pady=5)

        run_button = tk.Button(control_frame, text="Run", command=self.run_agent)
        run_button.pack(pady=5)

        pause_button = tk.Button(control_frame, text="Pause", command=self.pause_agent)
        pause_button.pack(pady=5)

        self.health_label = tk.Label(control_frame, text=f"Health: {self.health}")
        self.health_label.pack(pady=5)

        self.score_label = tk.Label(control_frame, text=f"Score: {self.score}")
        self.score_label.pack(pady=5)

    def create_logic_frame(self):
        # Frame for propositional logic steps
        self.logic_frame = tk.Frame(self.root)
        self.logic_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Create a Scrollbar
        self.scrollbar = tk.Scrollbar(self.logic_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a Canvas for logic steps and associate it with the scrollbar
        self.logic_canvas = tk.Canvas(self.logic_frame, bg="white", yscrollcommand=self.scrollbar.set)
        self.logic_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure the scrollbar
        self.scrollbar.config(command=self.logic_canvas.yview)

        # Create a Frame inside the Canvas to hold the text
        self.text_frame = tk.Frame(self.logic_canvas, bg="white")
        self.logic_canvas.create_window((0, 0), window=self.text_frame, anchor="nw")

        # Update the scroll region whenever the size of the content changes
        self.text_frame.bind("<Configure>", lambda e: self.logic_canvas.configure(scrollregion=self.logic_canvas.bbox("all")))



    def sync_logic_frame_size(self):
        # Sync the size of the logic frame with the map canvas
        map_width = self.canvas.winfo_width()
        map_height = self.canvas.winfo_height()

        # Set the width of the top canvas to the width of the map
        self.logic_canvas.config(width=map_width // 2, height=map_height)


    def load_map(self):
        file_path = filedialog.askopenfilename(title="Select Map File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.loaded_map_file = file_path
            # Reset game state
            self.health = 100
            self.score = 0
            self.agent_position = (9, 0)
            self.agent_direction = "right"
            self.smoke_coverage = [[True for _ in range(self.N)] for _ in range(self.N)]
            self.smoke_coverage[9][0] = False  # Uncover the initial position
            self.agent = Agent()  # Reset the agent
            self.logic_steps = []
            self.current_step = 0
            self.text_position = 10  # Reset text position in logic frame

            # Clear the previous map and logic display
            self.canvas.delete("all")
            for widget in self.text_frame.winfo_children():
                widget.destroy()

            # Load the new map
            self.N, self.world_map = self.read_map(file_path)
            self.add_signals()
            self.display_map()

            # Update health and score labels
            self.health_label.config(text=f"Health: {self.health}")
            self.score_label.config(text=f"Score: {self.score}")

            # Update the logic frame with initial message
            self.update_logic_frame("Map loaded. Starting simulation.")

            # Delay to ensure the canvas size is updated
            self.root.after(100, self.sync_logic_frame_size)  # Adjust timing as needed


    def read_map(self, filename):
        with open(filename, 'r') as file:
            N = int(file.readline().strip())
            world_map = [file.readline().strip().split('.') for _ in range(N)]
        return N, world_map

    def add_signals(self):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right

        for i in range(self.N):
            for j in range(self.N):
                room = self.world_map[i][j]

                if '-' in room:
                    room = room.replace('-', '')
                    self.world_map[i][j] = room

                # Add Stench (S) for Wumpus (W)
                if 'W' in room.split():
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.N and 0 <= nj < self.N:
                            if 'S' not in self.world_map[ni][nj]:
                                self.world_map[ni][nj] += " S"

                # Add Breeze (B) for Pit (P)
                if 'P' in room.split():
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.N and 0 <= nj < self.N:
                            if 'B' not in self.world_map[ni][nj]:
                                self.world_map[ni][nj] += " B"

                # Add Whiff (W_H) for Poisonous Gas (P_G)
                if 'P_G' in room.split():
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.N and 0 <= nj < self.N:
                            if 'W_H' not in self.world_map[ni][nj]:
                                self.world_map[ni][nj] += " W_H"

                # Add Glow (G_L) for Healing Potions (H_P)
                if 'H_P' in room.split():
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.N and 0 <= nj < self.N:
                            if 'G_L' not in self.world_map[ni][nj]:
                                self.world_map[ni][nj] += " G_L"

    def display_map(self):
        self.canvas.delete("all")  # Clear the canvas

        cell_size = 65  # Increased size of each cell
        font_size = 8  # Adjust the font size as needed
        width = self.N * cell_size
        height = self.N * cell_size
        self.canvas.config(width=width, height=height)

        for i in range(self.N):
            for j in range(self.N):
                x1, y1 = j * cell_size, i * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                room_content = self.world_map[i][j].split()

                # Draw the rectangle
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="white")

                # Draw the agent image at its current position with the correct direction
                if (i, j) == self.agent_position:
                    self.canvas.create_image(
                        (x1 + x2) / 2, 
                        (y1 + y2) / 2, 
                        image=self.agent_images[self.agent_direction]
                    )

                # Draw each signal separately with its corresponding color
                if room_content:
                    y_offset = y1 + 10  # Start position for text in the cell
                    for symbol in room_content:
                        if symbol != 'A':  # Skip drawing 'A' as text
                            self.canvas.create_text(
                                (x1 + x2) / 2, y_offset, 
                                text=symbol, 
                                fill=self.color_map(symbol), 
                                font=("Arial", font_size)
                            )
                            y_offset += font_size + 5  # Move to the next line for the next symbol

                # Draw the smoke image if the cell is still covered by smoke
                if self.smoke_coverage[i][j]:
                    self.canvas.create_image(
                        (x1 + x2) / 2, 
                        (y1 + y2) / 2, 
                        image=self.smoke_image
                    )


    def color_map(self, symbol):
        return {
            'W': 'black',
            'P': 'black',
            'A': 'black',
            'G': 'black',
            'P_G': 'black',
            'H_P': 'black',
            'S': 'red',
            'B': 'blue',
            'W_H': 'green',
            'G_L': 'purple'
        }.get(symbol, 'black')


    def update_logic_frame(self, text_top):
        # Append new content at the current text position
        top_text_label = tk.Label(self.text_frame, text=text_top, anchor="nw", justify="left", bg="white", font=("Arial", 10))
        top_text_label.pack(anchor="nw", padx=10, pady=(self.text_position, 0))


    def next_step(self):
        percepts = self.get_percepts(self.agent_position)
        move = self.agent.move(percepts)
        
        self.execute_move(move)

    def _move_agent_position(self, direction):
        x, y = self.agent_position
        if direction == "up" and x > 0:
            x -= 1
        elif direction == "down" and x < self.N - 1:
            x += 1
        elif direction == "left" and y > 0:
            y -= 1
        elif direction == "right" and y < self.N - 1:
            y += 1  

        self.agent_position = (x, y)
        self.smoke_coverage[x][y] = False
        self.display_map()

    def get_percepts(self, position):
        i, j = position
        room_content = self.world_map[i][j].split()
        percepts = [item for item in room_content if item in ['S', 'B', 'W_H', 'G_L', 'W', 'P', 'G', 'P_G', 'H_P']]
        return percepts
    

    def _grab_item(self):
        x, y = self.agent_position
        room_content = self.world_map[x][y].split()
        
        if 'G' in room_content:
            room_content.remove('G')
        if 'H_P' in room_content:
            room_content.remove('H_P')
            self.remove_signals(x, y, ['G_L']) 
            
        self.world_map[x][y] = ' '.join(room_content)
        self.display_map()

    def _shoot_arrow(self):
        x, y = self.agent_position

        if self.agent_direction == "up" and x > 0:
            target_x, target_y = x - 1, y
        elif self.agent_direction == "down" and x < self.N - 1:
            target_x, target_y = x + 1, y
        elif self.agent_direction == "left" and y > 0:
            target_x, target_y = x, y - 1
        elif self.agent_direction == "right" and y < self.N - 1:
            target_x, target_y = x, y + 1
        else:
            return False  # No valid target

        room_content = self.world_map[target_x][target_y].split()

        if 'W' in room_content:
            room_content.remove('W')
            self.world_map[target_x][target_y] = ' '.join(room_content)
            self.remove_signals(target_x, target_y, ['S']) 
            self.display_map()
            return True  # Wumpus was killed

        self.display_map()
        return False  

    def _climb_exit(self):
        self.running = False
        message = f"Agent finished Wumpus World with score: {self.score} and health: {self.health}"
        messagebox.showinfo("Wumpus World", message)
        self.write_output()


    def _heal(self):
        self.health = self.agent.health
        self.health_label.config(text=f"Health: {self.health}")

    def run_agent(self):
        """Start running the agent automatically."""
        self.running = True
        self._auto_move()

    def pause_agent(self):
        """Pause the agent's automatic movement."""
        self.running = False

    def _auto_move(self):
        if self.running:
            percepts = self.get_percepts(self.agent_position)
            move = self.agent.move(percepts)
            self.score = self.agent.score
            self.score_label.config(text=f"Score: {self.score}")

            self.health = self.agent.health
            self.health_label.config(text=f"Health: {self.health}")  

            self.execute_move(move)
            self.root.after(self.run_interval, self._auto_move)

    def execute_move(self, move):
        killed = False
        """Execute the move returned by the agent."""
        move_actions = {
            'F': "Forward",
            'L': "Turn Left",
            'R': "Turn Right",
            'G': "Grab",
            'S': "Shoot Arrow",
            'C': "Exit the Cave",
            'H': "Heal"
        }

        action_name = move_actions.get(move, "Unknown Action")
        if action_name == "Unknown Action":
            self.running = False
            message = f"Agent got killed !!"
            messagebox.showinfo("Wumpus World", message)
            self.write_output()

        output_x = self.N - int(self.agent_position[0])  
        output_y = int(self.agent_position[1]) + 1
        tmp_str = "(" + str(output_x) + "," + str(output_y) + "): " + action_name
        self.logic_steps.append(tmp_str)

        if move == 'F':
            self._move_agent_position(self.agent_direction)
        elif move == 'L':
            self._turn_left()
        elif move == 'R':
            self._turn_right()
        elif move == 'G':
            self._grab_item()
        elif move == 'S':
            killed = self._shoot_arrow()
        elif move == 'C':
            self._climb_exit()
        elif move == 'H':
            self._heal()



        self.score = self.agent.score
        self.score_label.config(text=f"Score: {self.score}")

        self.health = self.agent.health
        self.health_label.config(text=f"Health: {self.health}")

        self.update_logic_frame(f"Agent performed move: {action_name}")
        if killed:
            self.update_logic_frame(f"Agent heard the scream!")

    def write_output(self):
        input_file_name = os.path.basename(self.loaded_map_file)
        output_file_name = input_file_name.replace("input", "output")
        
        testcase_folder = os.path.join(os.getcwd(), "testcase")
        os.makedirs(testcase_folder, exist_ok=True)
        output_file_path = os.path.join(testcase_folder, output_file_name)

        with open(output_file_path, 'w') as f:
            for step in self.logic_steps:
                f.write(step + '\n')


    def _turn_left(self):
        directions = ["up", "left", "down", "right"]
        current_idx = directions.index(self.agent_direction)
        self.agent_direction = directions[(current_idx + 1) % 4]
        self.display_map()

    def _turn_right(self):
        directions = ["up", "right", "down", "left"]
        current_idx = directions.index(self.agent_direction)
        self.agent_direction = directions[(current_idx + 1) % 4]
        self.display_map()

    def remove_signals(self, x, y, signals):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right

        for di, dj in directions:
            ni, nj = x + di, y + dj
            if 0 <= ni < self.N and 0 <= nj < self.N:
                room_content = self.world_map[ni][nj].split()
                room_content = [item for item in room_content if item not in signals]
                self.world_map[ni][nj] = ' '.join(room_content)

        # After modifying the map, refresh the display
        self.display_map()