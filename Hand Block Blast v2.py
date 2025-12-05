import pygame
import cv2
import mediapipe as mp
import math
import random
import os

# ---------------- Config chung ----------------
GRID_SIZE = 8
CELL = 60
PADDING = 40 

# [LAYOUT] Điều chỉnh kích thước cửa sổ chuẩn HD-ish cho thoáng
WIDTH = 1080 
HEIGHT = 720 
FPS = 30
CORNER_RADIUS = 15 # Bo tròn mềm mại hơn

# [LAYOUT] Tính toán vị trí Lưới (Căn giữa dọc, lệch trái)
GRID_W = GRID_SIZE * CELL
GRID_H = GRID_SIZE * CELL
GRID_START_X = 60 # Cách mép trái 60px
GRID_START_Y = (HEIGHT - GRID_H) // 2

# [LAYOUT] Tính toán vị trí Panel bên phải (Dashboard)
UI_START_X = GRID_START_X + GRID_W + 60 # Cách lưới 60px
UI_WIDTH = WIDTH - UI_START_X - 60 # Phần còn lại trừ padding phải
UI_CENTER_X = UI_START_X + UI_WIDTH // 2

# NEW THEME COLORS (Phong cách tối, công nghệ)
DARK_BG = (18, 20, 32) 
FRAME_BLUE = (35, 45, 70) 
GRID_AREA_BG = (10, 10, 20) 
HIGHLIGHT_GLOW = (0, 220, 255) 
BLOCK_EDGE = (255, 255, 255) 
GRID_LINE = (30, 30, 50) 
EMPTY_CELL_BORDER = (40, 50, 80) 
BLOCK_COLORS = [(76, 132, 255), (255, 99, 132), (255, 195, 0), (80, 200, 120), (154, 89, 255)]
TEXT = (255, 255, 255) 
SCORE_COLOR = (255, 230, 100) 
BEST_COLOR = (255, 100, 100)
VALID_HIGHLIGHT = (80, 255, 150)
INVALID_HIGHLIGHT = (255, 80, 80)

# ---------------- Khởi tạo Pygame ----------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand Block Blast")
clock = pygame.time.Clock()
# Font chữ
font = pygame.font.SysFont("sansserif", 24, bold=True)
bigfont = pygame.font.SysFont("sansserif", 48, bold=True)
titlefont = pygame.font.SysFont("sansserif", 56, bold=True) # Font riêng cho tiêu đề
medfont = pygame.font.SysFont("sansserif", 32, bold=True) 

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

score = 0
high_score = load_high_score()

# ---------------- Lưới & Khối ----------------
grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

BLOCK_SHAPES = [
    [(0,0)], [(0,0),(1,0)], [(0,0),(1,0),(2,0)], [(0,0),(1,0),(2,0),(3,0)],
    [(0,0),(1,0),(0,1),(1,1)], [(0,0),(0,1),(1,1)], [(0,0),(0,1),(0,2),(1,2)],
    [(0,0),(1,0),(2,0),(1,1)], [(0,0),(1,0),(1,1),(2,1)], [(1,0),(2,0),(0,1),(1,1)],
]

def new_block():
    shape = random.choice(BLOCK_SHAPES)
    color_index = random.randrange(len(BLOCK_COLORS)) 
    return {"shape": shape, "color_index": color_index, "color": BLOCK_COLORS[color_index]}

def new_tray():
    return [new_block(), new_block(), new_block()]

tray = new_tray()

# [LAYOUT] Cấu hình vị trí Khay (Tray) dựa trên UI Panel
TRAY_START_Y = 320 # Vị trí bắt đầu vẽ khay (bên dưới bảng điểm)
TRAY_SPACING = 130 # Khoảng cách giữa các khối

# ---------------- Logic Game ----------------
def can_place(grid, block, gx, gy):
    for dx, dy in block["shape"]:
        x = gx + dx
        y = gy + dy
        if x < 0 or y < 0 or x >= GRID_SIZE or y >= GRID_SIZE: return False
        if grid[y][x] != 0: return False
    return True

def place_block(grid, block, gx, gy):
    global score, high_score
    placed_cells = 0
    
    color_id = block["color_index"] + 1 
    
    for dx, dy in block["shape"]:
        x = gx + dx
        y = gy + dy
        grid[y][x] = color_id
        placed_cells += 1
    score += placed_cells 

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

def draw_styled_block(surface, color, x, y, size):
    pygame.draw.rect(surface, (0, 0, 0), (x+1, y+1, size-2, size-2), border_radius=CORNER_RADIUS - 5)
    pygame.draw.rect(surface, color, (x, y, size, size), border_radius=CORNER_RADIUS - 4)
    pygame.draw.rect(surface, BLOCK_EDGE, (x, y, size, size), 1, border_radius=CORNER_RADIUS - 4)
    
    highlight_color = tuple(min(255, c + 50) for c in color)
    pygame.draw.line(surface, highlight_color, (x + 3, y + 3), (x + size - 4, y + 3), 2)
    pygame.draw.line(surface, highlight_color, (x + 3, y + 3), (x + 3, y + size - 4), 2)

def draw_grid(surface):
    # Khung bao quanh lưới
    outer_rect = pygame.Rect(GRID_START_X - 15, GRID_START_Y - 15, GRID_W + 30, GRID_H + 30)
    pygame.draw.rect(surface, FRAME_BLUE, outer_rect, border_radius=CORNER_RADIUS + 5)
    pygame.draw.rect(surface, HIGHLIGHT_GLOW, outer_rect, 2, border_radius=CORNER_RADIUS + 5)
    
    # Nền lưới
    pygame.draw.rect(surface, GRID_AREA_BG, (GRID_START_X, GRID_START_Y, GRID_W, GRID_H), border_radius=CORNER_RADIUS)

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = GRID_START_X + c * CELL + 2
            y = GRID_START_Y + r * CELL + 2
            size = CELL - 4
            
            cell_value = grid[r][c]
            
            if cell_value != 0:
                color_index = cell_value - 1
                color = BLOCK_COLORS[color_index] 
                draw_styled_block(surface, color, x, y, size)
            else:
                empty_rect = pygame.Rect(x, y, size, size)
                pygame.draw.rect(surface, GRID_AREA_BG, empty_rect, border_radius=CORNER_RADIUS - 5)
                pygame.draw.rect(surface, EMPTY_CELL_BORDER, empty_rect, 1, border_radius=CORNER_RADIUS - 5)
                

def draw_title(surface):
    # Vẽ tiêu đề căn giữa Panel bên phải
    # [ĐÃ SỬA] Chỉ hiển thị "HAND BLOCK BLAST"
    title_str = "HAND BLOCK BLAST"
    title_text = titlefont.render(title_str, True, HIGHLIGHT_GLOW)
    
    # Shadow
    shadow_text = titlefont.render(title_str, True, (0, 100, 150))
    
    x_pos = UI_CENTER_X - title_text.get_width() // 2
    y_pos = 60 # Căn chỉnh vị trí Y
    
    surface.blit(shadow_text, (x_pos + 3, y_pos + 3))
    surface.blit(title_text, (x_pos, y_pos))


def draw_score(surface):
    SCORE_Y = 140 # Vị trí Y cố định cho bảng điểm (dưới tiêu đề)
    PANEL_HEIGHT = 140
    
    # Khung bảng điểm
    score_rect = pygame.Rect(UI_START_X, SCORE_Y, UI_WIDTH, PANEL_HEIGHT)
    pygame.draw.rect(surface, FRAME_BLUE, score_rect, border_radius=CORNER_RADIUS)
    pygame.draw.rect(surface, (50, 60, 90), score_rect, 2, border_radius=CORNER_RADIUS) 

    # Chia đôi bảng điểm: Trái (Score) - Phải (Best)
    center_div = UI_START_X + UI_WIDTH // 2
    pygame.draw.line(surface, (50, 60, 90), (center_div, SCORE_Y + 10), (center_div, SCORE_Y + PANEL_HEIGHT - 10), 2)

    # --- SCORE (Trái) ---
    lbl_score = font.render("SCORE", True, (200, 200, 200))
    val_score = bigfont.render(str(score), True, SCORE_COLOR)
    
    surface.blit(lbl_score, (UI_START_X + (UI_WIDTH//4) - lbl_score.get_width()//2, SCORE_Y + 20))
    surface.blit(val_score, (UI_START_X + (UI_WIDTH//4) - val_score.get_width()//2, SCORE_Y + 60))
    
    # --- BEST (Phải) ---
    lbl_best = font.render("BEST", True, (200, 200, 200))
    val_best = bigfont.render(str(high_score), True, BEST_COLOR)
    
    surface.blit(lbl_best, (center_div + (UI_WIDTH//4) - lbl_best.get_width()//2, SCORE_Y + 20))
    surface.blit(val_best, (center_div + (UI_WIDTH//4) - val_best.get_width()//2, SCORE_Y + 60))


def draw_tray(surface, tray):
    for i, block in enumerate(tray):
        y = TRAY_START_Y + i*TRAY_SPACING
        
        # Vẽ nền cho từng khối (Tray Slot)
        slot_rect = pygame.Rect(UI_START_X, y, UI_WIDTH, 110)
        pygame.draw.rect(surface, (25, 30, 50), slot_rect, border_radius=CORNER_RADIUS) # Nền tối hơn chút
        pygame.draw.rect(surface, (40, 50, 80), slot_rect, 1, border_radius=CORNER_RADIUS) # Viền mờ

        if block is None:
            # Vẽ chữ USED hoặc icon mờ
            empty = medfont.render("---", True, (60, 60, 80))
            surface.blit(empty, (UI_CENTER_X - empty.get_width() // 2, y + 40))
            continue
            
        # Tính toán vị trí để căn giữa khối trong slot
        # 1. Tìm kích thước thực của khối
        block_w = 0
        block_h = 0
        shapes = block["shape"]
        if shapes:
            max_x = max(p[0] for p in shapes)
            max_y = max(p[1] for p in shapes)
            block_w = (max_x + 1) * (CELL // 2 + 3)
            block_h = (max_y + 1) * (CELL // 2 + 3)
        
        # 2. Tính offset để căn giữa
        start_x = UI_CENTER_X - block_w // 2
        start_y = y + (110 - block_h) // 2
        
        block_color = block["color"]
        
        for dx, dy in shapes:
            rx = start_x + dx * (CELL // 2 + 3) 
            ry = start_y + dy * (CELL // 2 + 3)
            size = CELL // 2 - 2
            draw_styled_block(surface, block_color, rx, ry, size)


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
            # Kiểm tra xem con trỏ có nằm trong vùng Panel bên phải không
            if x < UI_START_X or x > UI_START_X + UI_WIDTH: return None
            
            for i in range(len(tray)):
                ty0 = TRAY_START_Y + i*TRAY_SPACING 
                ty1 = ty0 + 110 # Chiều cao của slot
                if ty0 <= y <= ty1: return i
            return None

        if dist < DIST_THRESHOLD:
            if not holding:
                idx = hovered_tray_index(cursor_x, cursor_y)
                if idx is not None and tray[idx] is not None:
                    holding = True
                    held_block_index = idx
                    held_block = tray[idx]
        else:
            if holding:
                # Logic thả khối vào lưới
                gx = (cursor_x - GRID_START_X) // CELL
                gy = (cursor_y - GRID_START_Y) // CELL
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

    screen.fill(DARK_BG) 

    draw_grid(screen) # Vẽ lưới bên trái
    
    # Vẽ Dashboard bên phải
    draw_title(screen)
    draw_score(screen)
    draw_tray(screen, tray)
    
    if holding and held_block is not None:
        gx = (cursor_x - GRID_START_X) // CELL
        gy = (cursor_y - GRID_START_Y) // CELL
        valid = 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE and can_place(grid, held_block, gx, gy)
        
        drag_color = held_block["color"] 
        
        temp_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))
        
        for dx, dy in held_block["shape"]:
            x = GRID_START_X + (gx + dx)*CELL + 2
            y = GRID_START_Y + (gy + dy)*CELL + 2
            size = CELL - 4
            
            draw_styled_block(temp_surface, drag_color, x, y, size)
            
            rect = pygame.Rect(x, y, size, size)
            highlight_color = VALID_HIGHLIGHT if valid else INVALID_HIGHLIGHT
            pygame.draw.rect(temp_surface, highlight_color, rect, 4, border_radius=CORNER_RADIUS - 4)
        
        temp_surface.set_alpha(180)
        screen.blit(temp_surface, (0, 0))


    if hand_detected:
        cursor_color = (255, 50, 50) if holding else HIGHLIGHT_GLOW 
        
        # Đường nối ngón tay
        pygame.draw.line(screen, (80, 80, 120), (thumb_x, thumb_y), (cursor_x, cursor_y), 2)
        
        # Ngón cái
        pygame.draw.circle(screen, FRAME_BLUE, (thumb_x, thumb_y), 8)
        pygame.draw.circle(screen, (200, 200, 255), (thumb_x, thumb_y), 4)
        
        # Ngón trỏ (Con trỏ chính)
        pygame.draw.circle(screen, DARK_BG, (cursor_x, cursor_y), 12) # Viền nền
        pygame.draw.circle(screen, cursor_color, (cursor_x, cursor_y), 10) # Màu chính
        pygame.draw.circle(screen, (255, 255, 255), (cursor_x, cursor_y), 12, 1) # Viền trắng mỏng

    if not game_over and not any_moves_available(grid, tray):
        game_over = True

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 400, 250
        box_x, box_y = (WIDTH - box_w)//2, (HEIGHT - box_h)//2
        
        pygame.draw.rect(screen, FRAME_BLUE, (box_x, box_y, box_w, box_h), border_radius=20)
        pygame.draw.rect(screen, HIGHLIGHT_GLOW, (box_x, box_y, box_w, box_h), 2, border_radius=20)
        
        msg1 = bigfont.render("GAME OVER", True, BEST_COLOR)
        msg2 = medfont.render(f"Final Score: {score}", True, TEXT)
        msg3 = font.render("Press 'R' to Restart", True, (200, 200, 200))
        
        screen.blit(msg1, (WIDTH//2 - msg1.get_width()//2, box_y + 40))
        screen.blit(msg2, (WIDTH//2 - msg2.get_width()//2, box_y + 110))
        screen.blit(msg3, (WIDTH//2 - msg3.get_width()//2, box_y + 180))

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