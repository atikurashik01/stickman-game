import tkinter as tk
import random
import math
import time
from PIL import Image, ImageTk  # Add this import

class StickmanJump:
    def __init__(self, master):
        self.master = master
        master.title("Stickman Jump - Jump Over Blocks!")
        self.play_width = 500
        self.play_height = 400
        self.width = self.play_width
        self.height = self.play_height
        self.canvas = tk.Canvas(master, width=self.width, height=self.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        # Load background image
        self.bg_image = Image.open("/home/ashik/Documents/python project/bg2.png")
        self.bg_image = self.bg_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.ground_y = self.play_height - 60
        self.stickman_x = 80
        self.gap = 20  # Gap between stickman and ground
        self.stickman_y = self.ground_y - self.gap
        self.stickman_radius = 20
        self.jump_velocity = 0
        self.gravity = 1.2
        
        self.is_jumping = False
        self.jump_count = 0  # For double jump
        self.max_jumps = 2
        self.blocks = []
        self.block_speed = 8       # Slower speed for blocks
        self.block_interval = 40   # Increase interval for more distance between blocks
        self.frame_count = 0
        self.bg_hue = 0
        self.block_hue = 180
        self.score = 0
        self.high_score = 0
        self.running = True
        self.restart_button = None
        # Shield power-up
        self.shield = False
        self.shield_timer = 0
        self.shield_icon = None
        self.shield_duration = 120  # frames (about 2.4 seconds)
        self.powerups = []
        self.powerup_interval = 300  # frames
        # Clouds for background animation
        self.clouds = [self.create_cloud() for _ in range(3)]
        self.paused = False
        self.create_bindings()
        self.master.bind('<Configure>', self.on_resize)
        self.offset_x = 0
        self.offset_y = 0
        self.update_game()

    def create_cloud(self):
        return {
            'x': random.randint(0, self.width),
            'y': random.randint(30, 120),
            'size': random.randint(40, 80),
            'speed': random.uniform(0.5, 1.2)
        }

    def create_bindings(self):
        self.master.bind('<space>', self.jump)
        self.master.bind('<Up>', self.jump)
        self.master.bind('r', self.restart_key)
        self.master.bind('R', self.restart_key)
        self.master.bind('<Button-1>', self.jump)  # Left mouse button triggers jump

    def jump(self, event):
        if self.jump_count < self.max_jumps and self.running:
            self.jump_velocity = -18
            self.is_jumping = True
            self.jump_count += 1

    def restart_key(self, event):
        if not self.running or self.running:
            self.restart()

    def draw_stickman(self):
        x = self.offset_x + self.stickman_x
        y = self.offset_y + self.stickman_y
        self.canvas.create_text(x, y, text='🦸', font=("Arial", 48), anchor='s')
        if self.shield:
            self.canvas.create_oval(x-28, y-58, x+28, y-2, outline='#00e6ff', width=4)

    def hsv_to_hex(self, h, s, v):
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def draw_background(self):
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor='nw')
        # Draw ground
        self.canvas.create_rectangle(self.offset_x, self.offset_y + self.ground_y+30,
                                    self.offset_x + self.play_width, self.offset_y + self.play_height,
                                    fill="#222", outline="")

    def update_clouds(self):
        for cloud in self.clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > self.width:
                cloud['x'] = -cloud['size']
                cloud['y'] = random.randint(30, 120)
                cloud['size'] = random.randint(40, 80)
                cloud['speed'] = random.uniform(0.5, 1.2)

    def draw_blocks(self):
        for block in self.blocks:
            color = self.hsv_to_hex(block['hue'], 0.7, 1)
            self.canvas.create_rectangle(self.offset_x + block['x'], self.offset_y + block['y'], self.offset_x + block['x']+block['w'], self.offset_y + block['y']+block['h'], fill=color, outline="")
            block['hue'] = (block['hue'] + 1) % 360

    def update_blocks(self):
        for block in self.blocks:
            block['x'] -= self.block_speed
        self.blocks = [b for b in self.blocks if b['x']+b['w'] > 0]

    def spawn_block(self):
        w = random.randint(18, 32)  # More narrow blocks
        h = random.randint(30, 50)
        x = self.width
        y = self.ground_y + 30 - h
        hue = (self.block_hue + random.randint(-40, 40)) % 360
        self.blocks.append({'x': x, 'y': y, 'w': w, 'h': h, 'hue': hue})
        self.block_hue = (self.block_hue + 40) % 360

    def draw_powerups(self):
        for p in self.powerups:
            self.canvas.create_text(self.offset_x + p['x']+p['size']//2, self.offset_y + p['y']+p['size']//2, text='🛡️', font=("Arial", p['size']))

    def update_powerups(self):
        for p in self.powerups:
            p['x'] -= self.block_speed
        self.powerups = [p for p in self.powerups if p['x']+p['size'] > 0]

    def spawn_powerup(self):
        size = 32
        x = self.width
        y = self.ground_y + 30 - size - random.randint(0, 40)
        self.powerups.append({'x': x, 'y': y, 'size': size})

    def check_powerup_collision(self):
        for p in self.powerups:
            stickman_bottom = self.stickman_y
            stickman_top = self.stickman_y - 48
            stickman_left = self.stickman_x - 24
            stickman_right = self.stickman_x + 24
            powerup_left = p['x']
            powerup_right = p['x'] + p['size']
            powerup_top = p['y']
            powerup_bottom = p['y'] + p['size']
            if (stickman_right > powerup_left and stickman_left < powerup_right and
                stickman_bottom > powerup_top and stickman_top < powerup_bottom):
                self.powerups.remove(p)
                self.shield = True
                self.shield_timer = self.shield_duration
                break

    def check_collision(self):
        if self.shield:
            return False
        stickman_bottom = self.stickman_y + 45
        stickman_top = self.stickman_y - 40
        stickman_left = self.stickman_x - 15
        stickman_right = self.stickman_x + 15
        for block in self.blocks:
            block_top = block['y']
            block_bottom = block['y'] + block['h']
            block_left = block['x']
            block_right = block['x'] + block['w']
            if (stickman_right > block_left and stickman_left < block_right and
                stickman_bottom > block_top and stickman_top < block_bottom):
                return True
        return False

    def draw_score(self):
        self.canvas.create_text(self.offset_x + 10, self.offset_y + 10, anchor='nw', text=f"Score: {self.score}", font=("Arial", 16, "bold"), fill="#fff")
        self.canvas.create_text(self.offset_x + 10, self.offset_y + 35, anchor='nw', text=f"High Score: {self.high_score}", font=("Arial", 12), fill="#fff")
        if self.shield:
            self.canvas.create_text(self.offset_x + self.play_width-10, self.offset_y + 10, anchor='ne', text=f"🛡️ {self.shield_timer//20+1}", font=("Arial", 16), fill="#00e6ff")

    def game_over(self):
        self.running = False
        if self.score > self.high_score:
            self.high_score = self.score
        self.canvas.create_text(self.offset_x + self.play_width//2, self.offset_y + self.play_height//2-30, text="GAME OVER", font=("Arial", 32, "bold"), fill="#fff")
        self.canvas.create_text(self.offset_x + self.play_width//2, self.offset_y + self.play_height//2+10, text=f"Final Score: {self.score}", font=("Arial", 20), fill="#fff")
        self.canvas.create_text(self.offset_x + self.play_width//2, self.offset_y + self.play_height//2+40, text=f"High Score: {self.high_score}", font=("Arial", 16), fill="#fff")
        self.restart_button = tk.Button(self.master, text="Restart", font=("Arial", 16), command=self.restart)
        self.canvas.create_window(self.offset_x + self.play_width//2, self.offset_y + self.play_height//2+80, window=self.restart_button)

    def restart(self):
        self.stickman_y = self.ground_y - self.gap
        self.jump_velocity = 0
        self.is_jumping = False
        self.jump_count = 0
        self.blocks = []
        self.powerups = []
        self.shield = False
        self.shield_timer = 0
        self.score = 0
        self.running = True
        if self.restart_button:
            self.restart_button.destroy()
            self.restart_button = None
        self.update_game()

    def update_game(self):
        self.canvas.delete("all")
        self.draw_background()
        self.update_clouds()
        if self.paused:
            self.canvas.create_text(self.offset_x + self.play_width//2, self.offset_y + self.play_height//2, text="Paused", font=("Arial", 32, "bold"), fill="#fff")
            return
        if self.running:
            self.frame_count += 1
            if self.frame_count % self.block_interval == 0:
                self.spawn_block()
            if self.frame_count % self.powerup_interval == 0:
                self.spawn_powerup()
            self.update_blocks()
            self.update_powerups()
            self.draw_blocks()
            self.draw_powerups()
            self.draw_stickman()
            self.draw_score()
            # Handle jump physics
            if self.is_jumping:
                self.stickman_y += self.jump_velocity
                self.jump_velocity += self.gravity
                if self.stickman_y >= self.ground_y - self.gap:
                    self.stickman_y = self.ground_y - self.gap
                    self.is_jumping = False
                    self.jump_count = 0
            # Handle shield timer
            if self.shield:
                self.shield_timer -= 1
                if self.shield_timer <= 0:
                    self.shield = False
            self.check_powerup_collision()
            if self.check_collision():
                self.game_over()
            else:
                self.score += 1
                self.master.after(12, self.update_game)  # Was 7, now slower

    def on_resize(self, event):
        if event.widget == self.master:
            win_width = self.master.winfo_width()
            win_height = self.master.winfo_height()
            self.width = win_width
            self.height = win_height
            self.canvas.config(width=self.width, height=self.height)
            self.offset_x = (self.width - self.play_width) // 2
            self.offset_y = (self.height - self.play_height) // 2
            # Update background image for new size
            self.bg_image = Image.open("/home/ashik/Documents/python project/bg2.png")
            self.bg_image = self.bg_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)


# Left mouse button triggers jump


if __name__ == "__main__":
    root = tk.Tk()
    root.update()  # Force the window to appear immediately
    game = StickmanJump(root)
    root.mainloop()