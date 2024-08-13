import tkinter as tk
from tkinter import filedialog

class WumpusWorldGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Wumpus World")
        self.health = 100
        self.score = 0
        self.world_map = []
        self.N = 0
        self.logic_steps = []
        self.current_step = 0

        # Track the agent's position and direction (initially set to (0, 0) and facing "down")
        self.agent_position = (9, 0)
        self.agent_direction = "down"

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

        run_button = tk.Button(control_frame, text="Run")
        run_button.pack(pady=5)

        pause_button = tk.Button(control_frame, text="Pause")
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

        # Create Canvas for logic steps
        self.logic_canvas = tk.Canvas(self.logic_frame, bg="white")
        self.logic_canvas.pack(fill=tk.BOTH, expand=True)

    def sync_logic_frame_size(self):
        # Sync the size of the logic frame with the map canvas
        map_width = self.canvas.winfo_width()
        map_height = self.canvas.winfo_height()
        self.logic_canvas.config(width=map_width // 2, height=map_height)

    def load_map(self):
        file_path = filedialog.askopenfilename(title="Select Map File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.N, self.world_map = self.read_map(file_path)
            self.add_signals()
            self.display_map()
            self.logic_steps = []  # Clear previous logic steps
            self.current_step = 0
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


    def update_logic_frame(self, text):
        self.logic_canvas.delete("all")  # Clear the canvas
        self.logic_canvas.create_text(10, 10, anchor=tk.NW, text=text, fill="black", font=("Arial", 10))

    def next_step(self):
        if self.current_step < len(self.logic_steps) - 1:
            self.current_step += 1
            self.update_logic_frame(self.logic_steps[self.current_step])

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_logic_frame(self.logic_steps[self.current_step])
    
    def move_agent(self, direction):
        x, y = self.agent_position

        # Update the position based on the direction
        if direction == "up" and x > 0:
            x -= 1
            self.agent_direction = "up"
        elif direction == "down" and x < self.N - 1:
            x += 1
            self.agent_direction = "down"
        elif direction == "left" and y > 0:
            y -= 1
            self.agent_direction = "left"
        elif direction == "right" and y < self.N - 1:
            y += 1
            self.agent_direction = "right"

        # Update the agent's position
        self.agent_position = (x, y)

        # Redraw the map to reflect the agent's new position and direction
        self.display_map()

    def bind_keys(self):
        self.root.bind("<Up>", lambda event: self.move_agent("up"))
        self.root.bind("<Down>", lambda event: self.move_agent("down"))
        self.root.bind("<Left>", lambda event: self.move_agent("left"))
        self.root.bind("<Right>", lambda event: self.move_agent("right"))



if __name__ == "__main__":
    root = tk.Tk()
    gui = WumpusWorldGUI(root)
    root.mainloop()
