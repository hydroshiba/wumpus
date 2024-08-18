import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
from core import Agent

class WumpusWorldGUI:
    def __init__(self, root):
        self.running = False  # Variable to track if the agent is running
        self.run_interval = 500  # Interval in milliseconds between actions

        self.root = root
        self.root.title("Wumpus World")
        self.health = 100
        self.score = 0
        self.world_map = []
        self.N = 10
        self.logic_steps = []
        self.current_step = 0
        self.smoke_image = tk.PhotoImage(file="image/smoke-png-525.png").subsample(5, 5)
        self.smoke_coverage = [[True for _ in range(self.N)] for _ in range(self.N)]

        initial_x, initial_y = 9, 0
        self.smoke_coverage[initial_x][initial_y] = False

        # Track the agent's position and direction (initially set to (0, 0) and facing "down")
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

        # Bind keys to movement
        self.bind_keys()

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

        prev_button = tk.Button(control_frame, text="Previous Step", command=self.prev_step)
        prev_button.pack(pady=5)

        run_button = tk.Button(control_frame, text="Run", command=self.run_agent)
        run_button.pack(pady=5)

        pause_button = tk.Button(control_frame, text="Pause", command=self.pause_agent)
        pause_button.pack(pady=5)

        # Add Health and Score Labels
        self.health_label = tk.Label(control_frame, text=f"Health: {self.health}")
        self.health_label.pack(pady=5)

        self.score_label = tk.Label(control_frame, text=f"Score: {self.score}")
        self.score_label.pack(pady=5)

    def create_logic_frame(self):
        # Frame for propositional logic steps
        self.logic_frame = tk.Frame(self.root)
        self.logic_frame.pack(side="bottom", fill="both", padx=5, pady=5)

        # Create top frame for general information
        self.logic_frame_top = tk.Frame(self.logic_frame)
        self.logic_frame_top.pack(side="top", fill="both", expand=True)

        # Create bottom frame for detailed information
        self.logic_frame_bottom = tk.Frame(self.logic_frame)
        self.logic_frame_bottom.pack(side="bottom", fill="both", expand=True)

        # Create Canvas for top logic steps
        self.logic_canvas_top = tk.Canvas(self.logic_frame_top, bg="white")
        self.logic_canvas_top.pack(fill=tk.BOTH, expand=True)

        # Create Canvas for bottom logic steps
        self.logic_canvas_bottom = tk.Canvas(self.logic_frame_bottom, bg="white")
        self.logic_canvas_bottom.pack(fill=tk.BOTH, expand=True)


    def sync_logic_frame_size(self):
        # Sync the size of the logic frame with the map canvas
        map_width = self.canvas.winfo_width()
        map_height = self.canvas.winfo_height()

        # Set the width of the top canvas to the width of the map
        self.logic_canvas_top.config(width=map_width // 2, height=map_height // 2)
        
        # Set the width of the bottom canvas to the width of the map
        self.logic_canvas_bottom.config(width=map_width // 2, height=map_height // 2)


    def load_map(self):
        file_path = filedialog.askopenfilename(title="Select Map File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.N, self.world_map = self.read_map(file_path)
            self.add_signals()
            self.display_map()
            self.logic_steps = []  # Clear previous logic steps
            self.current_step = 0
            self.update_logic_frame("Map loaded. Starting simulation.", "")
            
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
                if room == 'P':
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


    def update_logic_frame(self, text_top, text_bottom):
        self.logic_canvas_top.delete("all")  # Clear the top canvas
        self.logic_canvas_top.create_text(10, 10, anchor=tk.NW, text=text_top, fill="black", font=("Arial", 10))

        self.logic_canvas_bottom.delete("all")  # Clear the bottom canvas
        self.logic_canvas_bottom.create_text(10, 10, anchor=tk.NW, text=text_bottom, fill="black", font=("Arial", 10))


    def next_step(self):
        if self.current_step < len(self.logic_steps) - 1:
            self.current_step += 1
            self.update_logic_frame(self.logic_steps[self.current_step])

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_logic_frame(self.logic_steps[self.current_step])
    
    def move_agent(self):
        percepts = self.get_percepts(self.agent_position)
        move = self.agent.move(percepts)

        if move == 'F':
            self._move_agent_position(self.agent_direction)
        elif move == 'L':
            self._turn_agent('left')
        elif move == 'R':
            self._turn_agent('right')
        elif move == 'G':
            self._grab_item()
        elif move == 'S':
            self._shoot_arrow()
        elif move == 'C':
            self._climb_exit()
        elif move == 'H':
            self._heal()

        # Redraw the map after each move
        self.display_map()

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
        percepts = [item for item in room_content if item in ['S', 'B', 'W_H', 'G_L']]
        return percepts
    
    def _turn_agent(self, turn_direction):
        if turn_direction == 'left':
            if self.agent_direction == "up":
                self.agent_direction = "left"
            elif self.agent_direction == "left":
                self.agent_direction = "down"
            elif self.agent_direction == "down":
                self.agent_direction = "right"
            elif self.agent_direction == "right":
                self.agent_direction = "up"
        elif turn_direction == 'right':
            if self.agent_direction == "up":
                self.agent_direction = "right"
            elif self.agent_direction == "right":
                self.agent_direction = "down"
            elif self.agent_direction == "down":
                self.agent_direction = "left"
            elif self.agent_direction == "left":
                self.agent_direction = "up"

    def _grab_item(self):
        x, y = self.agent_position
        room_content = self.world_map[x][y].split()
        
        if 'G' in room_content:
            room_content.remove('G')
            self.score += 100  # Assuming grabbing gold increases score by 100
        if 'H_P' in room_content:
            room_content.remove('H_P')
            self.score += 50  # Assuming grabbing healing potion increases score by 50
            
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
            return  # No valid target
        
        room_content = self.world_map[target_x][target_y].split()
        
        if 'W' in room_content:
            room_content.remove('W')
            self.score += 200  # Assuming killing Wumpus increases score by 200
        
        self.world_map[target_x][target_y] = ' '.join(room_content)
        self.display_map()

    def _climb_exit(self):
        message = f"Agent finished Wumpus World with score: {self.score} and health: {self.health}"
        messagebox.showinfo("Wumpus World", message)

    def _heal(self):
        # Assuming each healing potion restores 25 health
        self.health = min(self.health + 25, 100)
        self.health_label.config(text=f"Health: {self.health}")  # Assuming there's a label to display health


    def bind_keys(self):
        self.root.bind("<space>", lambda event: self.move_agent())

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

            self.execute_move(move)
            self.root.after(self.run_interval, self._auto_move)

    def execute_move(self, move):
        """Execute the move returned by the agent."""
        if move == 'F':
            self._move_agent_position(self.agent_direction)
        elif move == 'L':
            self._turn_left()
        elif move == 'R':
            self._turn_right()
        elif move == 'G':
            self._grab_item()
        elif move == 'S':
            self._shoot_arrow()
        elif move == 'C':
            self._climb_exit()
        elif move == 'H':
            self._heal()

    def _turn_left(self):
        directions = ["up", "left", "down", "right"]
        current_idx = directions.index(self.agent_direction)
        self.agent_direction = directions[(current_idx + 1) % 4]
        self.display_map()

    # Example implementation for turning right
    def _turn_right(self):
        directions = ["up", "right", "down", "left"]
        current_idx = directions.index(self.agent_direction)
        self.agent_direction = directions[(current_idx + 1) % 4]
        self.display_map()




if __name__ == "__main__":
    root = tk.Tk()
    gui = WumpusWorldGUI(root)
    root.mainloop()
