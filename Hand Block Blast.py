import pygame
import cv2
import mediapipe as mp
import math
import random
import os

# ---------------- Config chung ----------------
GRID_SIZE = 8
CELL = 60
PADDING = 20
WIDTH = PADDING*2 + GRID_SIZE*CELL + 300 
HEIGHT = PADDING*2 + GRID_SIZE*CELL
FPS = 60

BG = (245, 245, 245)
GRID_BG = (230, 230, 230)
GRID_LINE = (200, 200, 200)
# Lưu ý: Các màu này có index từ 0 đến 4
BLOCK_COLORS = [(76, 132, 255), (255, 99, 132), (255, 195, 0), (80, 200, 120), (154, 89, 255)]
TEXT = (30, 30, 30)
VALID_HIGHLIGHT = (120, 255, 160)
INVALID_HIGHLIGHT = (255, 140, 140)

# ---------------- Khởi tạo Pygame ----------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand Block Blast")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)
bigfont = pygame.font.SysFont("arial", 36)
medfont = pygame.font.SysFont("arial", 28) 

# ---------------- MediaPipe Hands ----------------
mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

# ---------------- Xử lý Kỷ lục (High Score) ----------------
HIGHSCORE_FILE = "highscore.txt"

def load_high_score():
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read())
    except:
        return 0

def save_high_score(new_high):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(new_high))

# Khởi tạo điểm
score = 0
high_score = load_high_score()

# ---------------- Lưới & Khối ----------------
# [ĐÃ SỬA]: Lưới giờ sẽ lưu trữ index màu (1 đến len(BLOCK_COLORS)) thay vì chỉ 0 hoặc 1.
# 0: Trống
# 1..n: Index của màu trong BLOCK_COLORS (index thực: index - 1)
grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

BLOCK_SHAPES = [
    [(0,0)], [(0,0),(1,0)], [(0,0),(1,0),(2,0)], [(0,0),(1,0),(2,0),(3,0)],
    [(0,0),(1,0),(0,1),(1,1)], [(0,0),(0,1),(1,1)], [(0,0),(0,1),(0,2),(1,2)],
    [(0,0),(1,0),(2,0),(1,1)], [(0,0),(1,0),(1,1),(2,1)], [(1,0),(2,0),(0,1),(1,1)],
]

def new_block():
    shape = random.choice(BLOCK_SHAPES)
    # [ĐÃ SỬA]: Lưu index màu thay vì giá trị màu RGB
    color_index = random.randrange(len(BLOCK_COLORS)) 
    return {"shape": shape, "color_index": color_index, "color": BLOCK_COLORS[color_index]}

def new_tray():
    return [new_block(), new_block(), new_block()]

tray = new_tray()
TRAY_X = PADDING + GRID_SIZE*CELL + 30
TRAY_Y = PADDING
TRAY_SPACING = 150

# ---------------- Logic Game ----------------
def can_place(grid, block, gx, gy):
    for dx, dy in block["shape"]:
        x = gx + dx
        y = gy + dy
        if x < 0 or y < 0 or x >= GRID_SIZE or y >= GRID_SIZE: return False
        # [ĐÃ SỬA]: Kiểm tra nếu ô đã khác 0 (tức là đã có màu)
        if grid[y][x] != 0: return False
    return True

def place_block(grid, block, gx, gy):
    global score, high_score
    placed_cells = 0
    
    # [ĐÃ SỬA]: Lưu trữ index màu + 1 vào lưới thay vì chỉ số 1
    color_id = block["color_index"] + 1 
    
    for dx, dy in block["shape"]:
        x = gx + dx
        y = gy + dy
        grid[y][x] = color_id # <-- LƯU MÃ MÀU VÀO LƯỚI
        placed_cells += 1
    score += placed_cells 

    # [ĐÃ SỬA]: Kiểm tra hàng/cột đầy bằng cách kiểm tra nếu không có ô nào là 0
    full_rows = [r for r in range(GRID_SIZE) if all(grid[r][c] != 0 for c in range(GRID_SIZE))]
    full_cols = [c for c in range(GRID_SIZE) if all(grid[r][c] != 0 for r in range(GRID_SIZE))]

    combo = 0
    for r in full_rows:
        for c in range(GRID_SIZE): grid[r][c] = 0
        combo += 1
    for c in full_cols:
        for r in range(GRID_SIZE): grid[r][c] = 0
        combo += 1
    if combo > 0: score += combo * GRID_SIZE
    
    if score > high_score:
        high_score = score
        save_high_score(high_score)
        
    return combo

def any_moves_available(grid, tray):
    for i, block in enumerate(tray):
        if block is None: continue
        for gy in range(GRID_SIZE):
            for gx in range(GRID_SIZE):
                if can_place(grid, block, gx, gy): return True
    return False

# ---------------- Vẽ ----------------
def draw_grid(surface):
    pygame.draw.rect(surface, GRID_BG, (PADDING, PADDING, GRID_SIZE*CELL, GRID_SIZE*CELL), border_radius=8)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = PADDING + c*CELL
            y = PADDING + r*CELL
            rect = pygame.Rect(x, y, CELL, CELL)
            
            cell_value = grid[r][c]
            
            if cell_value == 0:
                color = (255,255,255) # Ô trống màu trắng
            else:
                # [ĐÃ SỬA]: Lấy màu từ BLOCK_COLORS dựa trên index lưu trong lưới
                # cell_value là index + 1, nên index thực là cell_value - 1
                color_index = cell_value - 1
                color = BLOCK_COLORS[color_index] 
                
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, GRID_LINE, rect, 1, border_radius=6) # Viền lưới

def draw_tray(surface, tray):
    for i, block in enumerate(tray):
        y = TRAY_Y + i*TRAY_SPACING
        label = font.render(f"Khoi {i+1}", True, TEXT)
        surface.blit(label, (TRAY_X, y))
        if block is None:
            empty = font.render("(Da dung)", True, (160,160,160))
            surface.blit(empty, (TRAY_X, y+24))
            continue
        base_x, base_y = TRAY_X, y + 30
        for dx, dy in block["shape"]:
            rx = base_x + dx*(CELL//2)
            ry = base_y + dy*(CELL//2)
            rect = pygame.Rect(rx, ry, CELL//2, CELL//2)
            # [SỬ DỤNG MÀU RGB TRONG BLOCK]: Vẫn sử dụng màu RGB đã lưu trong block cho khay
            pygame.draw.rect(surface, block["color"], rect, border_radius=6) 
            pygame.draw.rect(surface, (80,80,80), rect, 1, border_radius=6)

def draw_score(surface):
    txt = bigfont.render(f"Score: {score}", True, TEXT)
    surface.blit(txt, (TRAY_X, HEIGHT - 80))
    
    best_txt = medfont.render(f"Best: {high_score}", True, (200, 50, 50)) 
    surface.blit(best_txt, (TRAY_X, HEIGHT - 40))

# ---------------- Điều khiển Tay ----------------
holding = False
held_block_index = None
held_block = None
cursor_x, cursor_y = WIDTH//2, HEIGHT//2
thumb_x, thumb_y = WIDTH//2, HEIGHT//2
hand_detected = False
DIST_THRESHOLD = 40 

def update_hand_control(frame):
    global holding, held_block_index, held_block, cursor_x, cursor_y, thumb_x, thumb_y, hand_detected
    
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        hand_detected = True
        hand = results.multi_hand_landmarks[0]
        
        ix, iy = int(hand.landmark[8].x * WIDTH), int(hand.landmark[8].y * HEIGHT)
        tx, ty = int(hand.landmark[4].x * WIDTH), int(hand.landmark[4].y * HEIGHT)
        
        cursor_x, cursor_y = ix, iy
        thumb_x, thumb_y = tx, ty
        dist = math.hypot(ix - tx, iy - ty)

        def hovered_tray_index(x, y):
            if x < TRAY_X - 10: return None
            for i in range(len(tray)):
                ty0 = TRAY_Y + i*TRAY_SPACING
                ty1 = ty0 + 100
                if ty0 <= y <= ty1: return i
            return None

        if dist < DIST_THRESHOLD:
            if not holding:
                idx = hovered_tray_index(cursor_x, cursor_y)
                if idx is not None and tray[idx] is not None:
                    holding = True
                    held_block_index = idx
                    held_block = tray[idx]
            # Giữ khối: Không làm gì thêm
        else:
            if holding:
                # Thả khối
                gx = (cursor_x - PADDING) // CELL
                gy = (cursor_y - PADDING) // CELL
                if held_block is not None and 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                    if can_place(grid, held_block, gx, gy):
                        place_block(grid, held_block, gx, gy)
                        if held_block_index is not None: tray[held_block_index] = None
                        if all(b is None for b in tray): tray[:] = new_tray()
                holding = False
                held_block = None
                held_block_index = None
    else:
        hand_detected = False
        # Nếu tay mất dấu khi đang giữ khối, khối sẽ tự động bị hủy (giống như thao tác thả)
        if holding:
             holding = False
             held_block = None
             held_block_index = None

# ---------------- Game loop ----------------
running = True
game_over = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BG)
    draw_grid(screen)
    draw_tray(screen, tray)
    draw_score(screen)
    
    if holding and held_block is not None:
        gx = (cursor_x - PADDING) // CELL
        gy = (cursor_y - PADDING) // CELL
        valid = 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE and can_place(grid, held_block, gx, gy)
        
        # [ĐÃ SỬA]: Vẫn sử dụng màu RGB đã lưu trong block cho khối đang kéo
        drag_color = held_block["color"] 
        
        for dx, dy in held_block["shape"]:
            x = PADDING + (gx + dx)*CELL
            y = PADDING + (gy + dy)*CELL
            rect = pygame.Rect(x, y, CELL, CELL)
            
            # Tô màu của khối đang kéo (hơi trong suốt)
            s = pygame.Surface((CELL, CELL))
            s.set_alpha(150)  # Độ trong suốt 
            s.fill(drag_color)
            screen.blit(s, (x, y))

            # Vẽ viền highlight (valid/invalid)
            highlight_color = VALID_HIGHLIGHT if valid else INVALID_HIGHLIGHT
            pygame.draw.rect(screen, highlight_color, rect, 4, border_radius=6)

    if hand_detected:
        cursor_color = (255, 50, 50) if holding else (0, 200, 0)
        pygame.draw.line(screen, (150, 150, 150), (thumb_x, thumb_y), (cursor_x, cursor_y), 2)
        pygame.draw.circle(screen, (100, 100, 100), (thumb_x, thumb_y), 8)
        pygame.draw.circle(screen, cursor_color, (cursor_x, cursor_y), 12)
        pygame.draw.circle(screen, (255, 255, 255), (cursor_x, cursor_y), 14, 2)

    if not game_over and not any_moves_available(grid, tray):
        game_over = True

    if game_over:
        # Vẽ khung thông báo Game Over
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH//2 - 150, HEIGHT//2 - 60, 300, 120), border_radius=10)
        pygame.draw.rect(screen, (200, 60, 60), (WIDTH//2 - 150, HEIGHT//2 - 60, 300, 120), 2, border_radius=10)
        
        msg1 = bigfont.render("GAME OVER", True, (200,60,60))
        msg2 = font.render(f"Final Score: {score}", True, TEXT)
        msg3 = font.render("Press 'R' to Restart", True, TEXT)
        
        screen.blit(msg1, (WIDTH//2 - msg1.get_width()//2, HEIGHT//2 - 40))
        screen.blit(msg2, (WIDTH//2 - msg2.get_width()//2, HEIGHT//2))
        screen.blit(msg3, (WIDTH//2 - msg3.get_width()//2, HEIGHT//2 + 30))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
            tray = new_tray()
            score = 0
            game_over = False

    pygame.display.flip()

    ret, frame = cap.read()
    if ret:
        update_hand_control(frame)
    
    clock.tick(FPS)

cap.release()
pygame.quit()
# Hùng đẹp trai vãi
