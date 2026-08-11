"""
NEXUS GAME CENTER v1.0 — Free Games Collection
8 built-in games. No install, no ads, no internet needed.
Snake, Tetris, Pong, Space Invaders, Flappy, Memory, 2048, Breakout.
"""
import os, sys, json, random, math, time, threading
from collections import deque
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

C = {
    "bg": "#080810", "bg2": "#101022", "card": "#181835",
    "border": "#202050", "text": "#d0d0e8", "dim": "#484878",
    "accent": "#6366f1", "accent2": "#818cf8",
    "green": "#34d399", "red": "#f87171", "orange": "#fb923c",
    "gold": "#fbbf24", "blue": "#60a5fa", "pink": "#ec4899",
}

SAVES_DIR = Path.home() / "Documents" / "NexusGames"
SAVES_DIR.mkdir(parents=True, exist_ok=True)
SCORES_FILE = SAVES_DIR / "highscores.json"

def load_scores():
    try:
        with open(SCORES_FILE, "r") as f: return json.load(f)
    except: return {}

def save_score(game, score):
    s = load_scores()
    prev = s.get(game, 0)
    if score > prev:
        s[game] = score
        with open(SCORES_FILE, "w") as f: json.dump(s, f)
        return True, score
    return False, prev


class GameWindow:
    def __init__(self, root, title, width, height):
        self.win = tk.Toplevel(root)
        self.win.title(title)
        self.win.geometry(f"{width}x{height}")
        self.win.configure(bg="#0a0a0f")
        self.win.resizable(False, False)
        self.win.transient(root)
        self.win.grab_set()
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() - width) // 2
        y = (self.win.winfo_screenheight() - height) // 2
        self.win.geometry(f"+{x}+{y}")
        self.canvas = tk.Canvas(self.win, width=width, height=height,
                                bg="#0a0a0f", highlightthickness=0)
        self.canvas.pack()
        self.score = 0
        self.running = True
        self.score_text = self.canvas.create_text(width // 2, 15, text="Score: 0",
                                                   fill=C["accent"], font=("Consolas", 12, "bold"))
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.bind("<KeyPress>", self.key_press)
        self.win.bind("<KeyRelease>", self.key_release)
        self.keys = set()

    def update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")

    def key_press(self, e):
        self.keys.add(e.keysym.lower())

    def key_release(self, e):
        self.keys.discard(e.keysym.lower())

    def close(self):
        self.running = False
        self.win.destroy()


class SnakeGame(GameWindow):
    def __init__(self, root):
        super().__init__(root, "🐍 Snake", 420, 440)
        self.snake = [(10, 10), (10, 9), (10, 8)]
        self.direction = (0, 1)
        self.food = self._spawn_food()
        self.speed = 120
        self._draw()
        self._loop()

    def _spawn_food(self):
        while True:
            f = (random.randint(0, 19), random.randint(0, 19))
            if f not in self.snake: return f

    def _draw(self):
        self.canvas.delete("snake")
        for i, (x, y) in enumerate(self.snake):
            color = C["accent"] if i == 0 else C["accent2"]
            self.canvas.create_rectangle(x * 20 + 10, y * 20 + 30,
                                         x * 20 + 28, y * 20 + 48,
                                         fill=color, outline="", tags="snake")
        fx, fy = self.food
        self.canvas.create_oval(fx * 20 + 12, fy * 20 + 32,
                                fx * 20 + 26, fy * 20 + 46,
                                fill=C["red"], outline="", tags="snake")

    def key_press(self, e):
        k = e.keysym.lower()
        if k == "up" and self.direction != (1, 0): self.direction = (-1, 0)
        elif k == "down" and self.direction != (-1, 0): self.direction = (1, 0)
        elif k == "left" and self.direction != (0, 1): self.direction = (0, -1)
        elif k == "right" and self.direction != (0, -1): self.direction = (0, 1)

    def _loop(self):
        if not self.running: return
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        if new_head[0] < 0 or new_head[0] >= 20 or new_head[1] < 0 or new_head[1] >= 20 or new_head in self.snake:
            self.canvas.create_text(210, 220, text=f"GAME OVER\nScore: {self.score}",
                                    fill=C["red"], font=("Consolas", 16, "bold"), justify="center")
            is_new, prev = save_score("snake", self.score)
            if is_new:
                self.canvas.create_text(210, 270, text="🏆 NEW HIGH SCORE!",
                                        fill=C["gold"], font=("Consolas", 12, "bold"))
            return
        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.update_score()
            self.food = self._spawn_food()
        else:
            self.snake.pop()
        self._draw()
        self.win.after(self.speed, self._loop)


class PongGame(GameWindow):
    def __init__(self, root):
        super().__init__(root, "🏓 Pong", 500, 350)
        self.paddle_y = 150
        self.ai_y = 150
        self.ball_x, self.ball_y = 250, 175
        self.ball_dx, self.ball_dy = random.choice([-3, 3]), random.choice([-2, 2])
        self._draw()
        self._loop()

    def _draw(self):
        self.canvas.delete("game")
        self.canvas.create_rectangle(10, self.paddle_y - 30, 20, self.paddle_y + 30,
                                     fill=C["accent"], outline="", tags="game")
        self.canvas.create_rectangle(480, self.ai_y - 30, 490, self.ai_y + 30,
                                     fill=C["red"], outline="", tags="game")
        self.canvas.create_oval(self.ball_x - 5, self.ball_y - 5,
                                self.ball_x + 5, self.ball_y + 5,
                                fill=C["gold"], outline="", tags="game")
        self.canvas.create_line(250, 0, 250, 350, fill=C["dim"], dash=(5, 5), tags="game")

    def _loop(self):
        if not self.running: return
        self.ball_x += self.ball_dx; self.ball_y += self.ball_dy
        if self.ball_y <= 5 or self.ball_y >= 345: self.ball_dy = -self.ball_dy
        if self.ball_x <= 25 and abs(self.ball_y - self.paddle_y) < 40:
            self.ball_dx = abs(self.ball_dx) + 0.2; self.score += 1; self.update_score()
        elif self.ball_x >= 475 and abs(self.ball_y - self.ai_y) < 40:
            self.ball_dx = -abs(self.ball_dx) - 0.2
        if self.ball_x < 0 or self.ball_x > 500:
            self.canvas.create_text(250, 170, text=f"GAME OVER\nScore: {self.score}",
                                    fill=C["red"] if self.ball_x < 0 else C["accent"],
                                    font=("Consolas", 16, "bold"), justify="center")
            save_score("pong", self.score); return
        if "up" in self.keys: self.paddle_y = max(35, self.paddle_y - 6)
        if "down" in self.keys: self.paddle_y = min(315, self.paddle_y + 6)
        if self.ai_y < self.ball_y: self.ai_y = min(315, self.ai_y + 3)
        if self.ai_y > self.ball_y: self.ai_y = max(35, self.ai_y - 3)
        self._draw()
        self.win.after(20, self._loop)


class TetrisGame(GameWindow):
    PIECES = [
        [[1,1,1,1]], [[1,1],[1,1]], [[0,1,0],[1,1,1]],
        [[1,1,0],[0,1,1]], [[0,1,1],[1,1,0]], [[1,0,0],[1,1,1]], [[0,0,1],[1,1,1]]
    ]
    COLORS = [C["accent"], C["gold"], C["pink"], C["red"], C["green"], C["blue"], C["orange"]]

    def __init__(self, root):
        super().__init__(root, "🧱 Tetris", 300, 520)
        self.grid = [[0] * 10 for _ in range(20)]
        self.piece = random.choice(self.PIECES)
        self.piece_color = random.randint(0, 6)
        self.px, self.py = 3, 0
        self._draw()
        self._loop()

    def _draw(self):
        self.canvas.delete("game")
        for y in range(20):
            for x in range(10):
                if self.grid[y][x]:
                    self.canvas.create_rectangle(x * 25 + 25, y * 25 + 30,
                                                  x * 25 + 48, y * 25 + 53,
                                                  fill=self.COLORS[self.grid[y][x] - 1],
                                                  outline="#0a0a0f", tags="game")
        for y, row in enumerate(self.piece):
            for x, cell in enumerate(row):
                if cell:
                    self.canvas.create_rectangle(
                        (self.px + x) * 25 + 25, (self.py + y) * 25 + 30,
                        (self.px + x) * 25 + 48, (self.py + y) * 25 + 53,
                        fill=self.COLORS[self.piece_color], outline="#0a0a0f", tags="game")

    def _collision(self, px, py):
        for y, row in enumerate(self.piece):
            for x, cell in enumerate(row):
                if cell:
                    nx, ny = px + x, py + y
                    if nx < 0 or nx >= 10 or ny >= 20 or (ny >= 0 and self.grid[ny][nx]):
                        return True
        return False

    def _lock(self):
        for y, row in enumerate(self.piece):
            for x, cell in enumerate(row):
                if cell:
                    if self.py + y < 0:
                        self.canvas.create_text(150, 260, text="GAME OVER",
                                                fill=C["red"], font=("Consolas", 18, "bold"))
                        save_score("tetris", self.score); self.running = False; return
                    self.grid[self.py + y][self.px + x] = self.piece_color + 1
        cleared = 0
        for y in range(19, -1, -1):
            if all(self.grid[y]):
                del self.grid[y]
                self.grid.insert(0, [0] * 10)
                cleared += 1
        self.score += [0, 40, 100, 300, 1200][cleared]
        self.update_score()
        self.piece = random.choice(self.PIECES)
        self.piece_color = random.randint(0, 6)
        self.px, self.py = 3, 0

    def key_press(self, e):
        k = e.keysym.lower()
        if k == "left" and not self._collision(self.px - 1, self.py): self.px -= 1
        elif k == "right" and not self._collision(self.px + 1, self.py): self.px += 1
        elif k == "down":
            if not self._collision(self.px, self.py + 1): self.py += 1; self.score += 1; self.update_score()
        elif k == "up":
            old = self.piece
            self.piece = list(zip(*self.piece[::-1]))
            if self._collision(self.px, self.py): self.piece = old
        elif k == "space":
            while not self._collision(self.px, self.py + 1):
                self.py += 1; self.score += 2
            self._lock()
            self.update_score()

    def _loop(self):
        if not self.running: return
        if not self._collision(self.px, self.py + 1):
            self.py += 1
        else:
            self._lock()
        self._draw()
        self.win.after(500, self._loop)


class FlappyGame(GameWindow):
    def __init__(self, root):
        super().__init__(root, "🐦 Flappy Bird", 400, 500)
        self.bird_y = 250
        self.velocity = 0
        self.gaps = []
        for i in range(3):
            self.gaps.append([400 + i * 180, random.randint(80, 350)])
        self._draw()
        self._loop()

    def _draw(self):
        self.canvas.delete("game")
        self.canvas.create_oval(60, self.bird_y - 12, 84, self.bird_y + 12,
                                fill=C["gold"], outline="", tags="game")
        for gx, gy in self.gaps:
            self.canvas.create_rectangle(gx, 0, gx + 50, gy - 40,
                                         fill=C["green"], outline="", tags="game")
            self.canvas.create_rectangle(gx, gy + 40, gx + 50, 500,
                                         fill=C["green"], outline="", tags="game")

    def _loop(self):
        if not self.running: return
        self.velocity += 0.5
        self.bird_y += self.velocity
        if "space" in self.keys or "up" in self.keys:
            self.velocity = -7
            self.keys.clear()

        for i, (gx, gy) in enumerate(self.gaps):
            self.gaps[i][0] -= 4
            if self.gaps[i][0] < -50:
                self.gaps[i][0] = 400
                self.gaps[i][1] = random.randint(80, 350)
                self.score += 1
                self.update_score()

            if 60 < gx + 50 and 84 > gx:
                if self.bird_y - 12 < gy - 40 or self.bird_y + 12 > gy + 40:
                    self._game_over(); return

        if self.bird_y < 0 or self.bird_y > 500:
            self._game_over(); return

        self._draw()
        self.win.after(25, self._loop)

    def _game_over(self):
        self.canvas.create_text(200, 200, text=f"GAME OVER\nScore: {self.score}",
                                fill=C["red"], font=("Consolas", 18, "bold"), justify="center")
        is_new, _ = save_score("flappy", self.score)
        if is_new:
            self.canvas.create_text(200, 270, text="🏆 NEW HIGH SCORE!",
                                    fill=C["gold"], font=("Consolas", 12, "bold"))
        self.running = False


class InvadersGame(GameWindow):
    def __init__(self, root):
        super().__init__(root, "👾 Space Invaders", 500, 480)
        self.player_x = 230
        self.bullets = []
        self.enemies = []
        for row in range(4):
            for col in range(8):
                self.enemies.append([60 + col * 50, 50 + row * 40, 20, 20, True])
        self.enemy_dir = 2
        self.shoot_cooldown = 0
        self._draw()
        self._loop()

    def _draw(self):
        self.canvas.delete("game")
        self.canvas.create_rectangle(self.player_x, 430, self.player_x + 40, 445,
                                     fill=C["accent"], outline="", tags="game")
        for ex, ey, ew, eh, alive in self.enemies:
            if alive:
                self.canvas.create_rectangle(ex, ey, ex + ew, ey + eh,
                                             fill=C["red"], outline="", tags="game")
        for bx, by in self.bullets:
            self.canvas.create_rectangle(bx, by, bx + 3, by + 10,
                                         fill=C["gold"], outline="", tags="game")

    def _loop(self):
        if not self.running: return
        if "left" in self.keys: self.player_x = max(0, self.player_x - 5)
        if "right" in self.keys: self.player_x = min(460, self.player_x + 5)
        if "space" in self.keys and self.shoot_cooldown <= 0:
            self.bullets.append([self.player_x + 18, 425])
            self.shoot_cooldown = 15
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)

        for b in self.bullets[:]:
            b[1] -= 8
            if b[1] < 0: self.bullets.remove(b)
        for i, (ex, ey, ew, eh, alive) in enumerate(self.enemies):
            if not alive: continue
            for b in self.bullets[:]:
                if ex < b[0] < ex + ew and ey < b[1] < ey + eh:
                    self.enemies[i][4] = False
                    self.bullets.remove(b)
                    self.score += 10
                    self.update_score()
                    break

        down = False
        for ex, ey, _, _, alive in self.enemies:
            if alive and (ex <= 0 or ex >= 480): self.enemy_dir = -self.enemy_dir; down = True; break
        for i in range(len(self.enemies)):
            if self.enemies[i][4]:
                self.enemies[i][0] += self.enemy_dir
                if down: self.enemies[i][1] += 10
                if self.enemies[i][1] > 400:
                    self.canvas.create_text(250, 220, text="GAME OVER",
                                            fill=C["red"], font=("Consolas", 18, "bold"))
                    save_score("invaders", self.score); self.running = False; return

        if not any(a for _,_,_,_,a in self.enemies):
            self.canvas.create_text(250, 220, text="YOU WIN!",
                                    fill=C["green"], font=("Consolas", 18, "bold"))
            save_score("invaders", self.score); self.running = False; return

        self._draw()
        self.win.after(30, self._loop)


class MemoryGame(GameWindow):
    def __init__(self, root):
        super().__init__(root, "🧠 Memory Match", 420, 420)
        emojis = ["🐶","🐱","🐸","🦊","🐻","🐼","🐨","🦁"] * 2
        random.shuffle(emojis)
        self.cards = emojis
        self.flipped = [False] * 16
        self.matched = [False] * 16
        self.selected = []
        self.moves = 0
        self._draw()

    def _draw(self):
        self.canvas.delete("game")
        for i in range(16):
            x, y = 25 + (i % 4) * 95, 40 + (i // 4) * 95
            if self.matched[i]:
                self.canvas.create_rectangle(x, y, x + 80, y + 80, fill=C["green"],
                                             outline=C["border"], tags="game")
            elif self.flipped[i]:
                self.canvas.create_rectangle(x, y, x + 80, y + 80, fill=C["card"],
                                             outline=C["border"], tags="game")
                self.canvas.create_text(x + 40, y + 40, text=self.cards[i],
                                        font=("Segoe UI", 28), tags="game")
            else:
                self.canvas.create_rectangle(x, y, x + 80, y + 80,
                                             fill=C["accent"], outline=C["bg"], tags="game")
                self.canvas.create_text(x + 40, y + 40, text="?", font=("Segoe UI", 20, "bold"),
                                        fill="#000", tags="game")

    def key_press(self, e): pass

    def close(self):
        super().close()
        self.canvas.unbind("<Button-1>")

    def _draw(self):
        super()._draw()
        self.canvas.bind("<Button-1>", self._click)

    def _click(self, e):
        if not self.running or len(self.selected) >= 2: return
        col, row = (e.x - 25) // 95, (e.y - 40) // 95
        idx = row * 4 + col
        if idx < 0 or idx >= 16 or self.flipped[idx] or self.matched[idx]: return
        self.flipped[idx] = True
        self.selected.append(idx)
        if len(self.selected) == 2:
            self.moves += 1
            a, b = self.selected
            self.canvas.itemconfig(self.score_text,
                                   text=f"Score: {self.score} | Moves: {self.moves}")
            if self.cards[a] == self.cards[b]:
                self.matched[a] = self.matched[b] = True
                self.score += 20
                self.update_score()
                self.selected = []
            else:
                self.win.after(600, lambda: self._flip_back(a, b))
        GameWindow._draw(self)

    def _flip_back(self, a, b):
        self.flipped[a] = self.flipped[b] = False
        self.selected = []
        GameWindow._draw(self)


class Game2048(GameWindow):
    def __init__(self, root):
        super().__init__(root, "🔢 2048", 350, 400)
        self.grid = [[0]*4 for _ in range(4)]
        self._add_tile(); self._add_tile()
        self._draw()

    def _add_tile(self):
        empty = [(r,c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def _draw(self):
        self.canvas.delete("game")
        colors = {0:"#1a1a3a",2:"#3a3a6a",4:"#4a4a8a",8:"#f59e0b",16:"#fb923c",32:"#f87171",
                  64:"#ef4444",128:"#fbbf24",256:"#fbbf24",512:"#fbbf24",1024:"#34d399",2048:"#34d399"}
        for r in range(4):
            for c in range(4):
                v = self.grid[r][c]
                x, y = 20 + c * 80, 60 + r * 80
                self.canvas.create_rectangle(x, y, x + 70, y + 70,
                                             fill=colors.get(v, "#34d399"),
                                             outline=C["border"], tags="game")
                if v:
                    self.canvas.create_text(x + 35, y + 35, text=str(v),
                                            font=("Consolas", 18, "bold"), fill="#fff", tags="game")

    def key_press(self, e):
        k = e.keysym.lower()
        moved = False
        old = [r[:] for r in self.grid]
        if k == "left": moved = self._move(0, 1, 0, 1)
        elif k == "right": moved = self._move(0, -1, 3, -1)
        elif k == "up": moved = self._move(1, 0, 0, 1)
        elif k == "down": moved = self._move(1, 0, 3, -1)
        if moved:
            self._add_tile()
            self.score = max(max(r) for r in self.grid)
            self.update_score()
            self._draw()
            if 2048 in [v for r in self.grid for v in r]:
                self.canvas.create_text(175, 30, text="YOU WIN!", fill=C["gold"],
                                        font=("Consolas", 16, "bold"))
                save_score("2048", self.score)

    def _move(self, axis, step, start, dir):
        moved = False
        if axis == 0:
            for r in range(4):
                row = [self.grid[r][c] for c in range(start, start + 4 * dir, dir) if self.grid[r][c]]
                merged = []
                i = 0
                while i < len(row):
                    if i + 1 < len(row) and row[i] == row[i + 1]:
                        merged.append(row[i] * 2); i += 2
                    else:
                        merged.append(row[i]); i += 1
                merged += [0] * (4 - len(merged))
                for c in range(4):
                    new_val = merged[c] if dir == 1 else merged[3 - c]
                    if self.grid[r][c] != new_val: moved = True
                    self.grid[r][c] = new_val
        else:
            for c in range(4):
                col = [self.grid[r][c] for r in range(start, start + 4 * dir, dir) if self.grid[r][c]]
                merged = []
                i = 0
                while i < len(col):
                    if i + 1 < len(col) and col[i] == col[i + 1]:
                        merged.append(col[i] * 2); i += 2
                    else:
                        merged.append(col[i]); i += 1
                merged += [0] * (4 - len(merged))
                for r in range(4):
                    new_val = merged[r] if dir == 1 else merged[3 - r]
                    if self.grid[r][c] != new_val: moved = True
                    self.grid[r][c] = new_val
        return moved

    def close(self):
        self.running = False
        self.win.destroy()


class BreakoutGame(GameWindow):
    def __init__(self, root):
        super().__init__(root, "🧱 Breakout", 400, 500)
        self.paddle_x = 160
        self.ball_x, self.ball_y = 200, 400
        self.ball_dx, self.ball_dy = 3, -3
        self.blocks = []
        for r in range(5):
            for c in range(8):
                self.blocks.append([15 + c * 46, 50 + r * 22, 40, 18,
                                    ["#ef4444","#fb923c","#fbbf24","#34d399","#60a5fa"][r]])
        self._draw()
        self._loop()

    def _draw(self):
        self.canvas.delete("game")
        self.canvas.create_rectangle(self.paddle_x, 470, self.paddle_x + 80, 480,
                                     fill=C["accent"], outline="", tags="game")
        self.canvas.create_oval(self.ball_x - 5, self.ball_y - 5,
                                self.ball_x + 5, self.ball_y + 5,
                                fill=C["gold"], outline="", tags="game")
        for bx, by, bw, bh, color in self.blocks:
            self.canvas.create_rectangle(bx, by, bx + bw, by + bh, fill=color, outline="", tags="game")

    def _loop(self):
        if not self.running: return
        self.ball_x += self.ball_dx; self.ball_y += self.ball_dy
        if self.ball_x <= 0 or self.ball_x >= 395: self.ball_dx = -self.ball_dx
        if self.ball_y <= 5: self.ball_dy = abs(self.ball_dy)
        if self.ball_y > 480:
            self.canvas.create_text(200, 250, text=f"GAME OVER\nScore: {self.score}",
                                    fill=C["red"], font=("Consolas", 16, "bold"), justify="center")
            save_score("breakout", self.score); return
        if self.ball_y >= 465 and self.paddle_x < self.ball_x < self.paddle_x + 80:
            self.ball_dy = -abs(self.ball_dy)
        for i, (bx, by, bw, bh, color) in enumerate(self.blocks):
            if bx < self.ball_x < bx + bw and by < self.ball_y < by + bh:
                self.ball_dy = -self.ball_dy
                del self.blocks[i]
                self.score += 10
                self.update_score()
                if not self.blocks:
                    self.canvas.create_text(200, 250, text="YOU WIN!",
                                            fill=C["green"], font=("Consolas", 18, "bold"))
                    save_score("breakout", self.score); return
                break
        if "left" in self.keys: self.paddle_x = max(0, self.paddle_x - 6)
        if "right" in self.keys: self.paddle_x = min(320, self.paddle_x + 6)
        self._draw()
        self.win.after(16, self._loop)


class NexusGames:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS GAME CENTER")
        self.root.geometry("780x560")
        self.root.minsize(600, 420)
        self.root.configure(bg=C["bg"])
        self._center()
        self.highscores = load_scores()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 780) // 2
        y = (self.root.winfo_screenheight() - 560) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build(self):
        tk.Label(self.root, text="🎮 NEXUS GAME CENTER", font=("Segoe UI", 20, "bold"),
                fg=C["accent2"], bg=C["bg"]).pack(pady=(20, 4))
        tk.Label(self.root, text="8 Free Games • No Ads • No Install • 100% Offline",
                font=("Segoe UI", 9), fg=C["dim"], bg=C["bg"]).pack()

        grid = tk.Frame(self.root, bg=C["bg"])
        grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        games = [
            ("🐍", "Snake", "Classic snake game", SnakeGame, "snake"),
            ("🧱", "Tetris", "Block stacking puzzle", TetrisGame, "tetris"),
            ("🏓", "Pong", "Table tennis vs AI", PongGame, "pong"),
            ("🐦", "Flappy", "Flappy bird clone", FlappyGame, "flappy"),
            ("👾", "Invaders", "Space invaders", InvadersGame, "invaders"),
            ("🧠", "Memory", "Card matching", MemoryGame, "memory"),
            ("🔢", "2048", "Number merge puzzle", Game2048, "2048"),
            ("🧱", "Breakout", "Brick breaker", BreakoutGame, "breakout"),
        ]

        for i, (icon, name, desc, game_class, score_key) in enumerate(games):
            row, col = i // 4, i % 4
            card = tk.Frame(grid, bg=C["card"], highlightbackground=C["border"], highlightthickness=1,
                           cursor="hand2", padx=2, pady=2)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            grid.grid_columnconfigure(col, weight=1)
            grid.grid_rowconfigure(row, weight=1)

            tk.Label(card, text=icon, font=("Segoe UI", 32), bg=C["card"]).pack(pady=(14, 0))
            tk.Label(card, text=name, font=("Segoe UI", 13, "bold"), fg=C["text"], bg=C["card"]).pack()
            tk.Label(card, text=desc, font=("Segoe UI", 8), fg=C["dim"], bg=C["card"]).pack(pady=(2, 4))

            hs = self.highscores.get(score_key, 0)
            if hs > 0:
                tk.Label(card, text=f"🏆 {hs}", font=("Segoe UI", 9, "bold"), fg=C["gold"],
                        bg=C["card"]).pack(pady=(0, 8))

            card.bind("<Button-1>", lambda e, gc=game_class: self._launch(gc))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, gc=game_class: self._launch(gc))

    def _launch(self, game_class):
        def _run():
            game = game_class(self.root)
            self.root.wait_window(game.win)
            self.highscores = load_scores()
        threading.Thread(target=_run, daemon=True).start()


def main():
    root = tk.Tk()
    NexusGames(root)
    root.mainloop()


if __name__ == "__main__":
    main()
