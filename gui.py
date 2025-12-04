import sys
import pygame
import json
import os

from logic import GameBoard

# Файл для хранения рекордов
SCORE_FILE = "highscores.json"

# Уровни сложности
LEVELS = {
    "Простой":  {"width": 9,  "height": 9,  "mines": 10},
    "Средний":  {"width": 16, "height": 16, "mines": 40},
    "Сложный":  {"width": 30, "height": 16, "mines": 99},
}

LEVEL_ORDER = ["Простой", "Средний", "Сложный"]

CELL_SIZE = 40
HUD_HEIGHT = 80

# Цвета
BG_COLOR = (50, 50, 50)           # Фон окна
HUD_BG_COLOR = (40, 40, 40)       # Фон панели
CELL_CLOSED_COLOR = (80, 80, 80)  # Закрытая ячейка
CELL_OPEN_COLOR = (45, 45, 45)    # Открытая ячейка
GRID_COLOR = (30, 30, 30)         # Граница

# LED Табло
LED_BG_COLOR = (60, 0, 0)
LED_FG_COLOR = (255, 0, 0)

# Центральная кнопка
BTN_COLOR = (70, 70, 70)
BTN_BORDER = (90, 90, 90)
BTN_TEXT_COLOR = (220, 220, 220)
RECORD_TEXT_COLOR = (180, 180, 180) # Цвет текста рекорда

# Цифры
NUMBER_COLORS = {
    1: (100, 160, 255),
    2: (100, 200, 100),
    3: (230, 80, 80),
    4: (180, 100, 200),
    5: (160, 50, 50),
    6: (50, 150, 150),
    7: (200, 200, 200),
    8: (100, 100, 100),
}

FLAG_COLOR = (230, 50, 50)
MINE_COLOR = (200, 200, 200)


# ======== Работа с рекордами ========

def load_high_scores():
    """Загружает рекорды из файла JSON."""
    if not os.path.exists(SCORE_FILE):
        return {}
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_high_scores(scores):
    """Сохраняет рекорды в файл JSON."""
    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=4)
    except OSError:
        pass


# ======== Основная функция ========

def run_game():
    pygame.init()
    pygame.display.set_caption("Minesweeper")
    clock = pygame.time.Clock()

    # Загружаем рекорды
    high_scores = load_high_scores()

    # Индекс текущего уровня в списке LEVEL_ORDER
    current_level_idx = 0
    current_level_name = LEVEL_ORDER[current_level_idx]

    board = create_board_for_level(current_level_name)
    screen = create_window_for_board(board)

    start_ticks = pygame.time.get_ticks()
    final_time_sec = 0
    
    running = True
    while running:
        screen_w = screen.get_width()
        
        # Размеры кнопки
        btn_w, btn_h = 140, 35  
        btn_y = (HUD_HEIGHT - btn_h) // 2 - 8 
        
        center_btn_rect = pygame.Rect(
            (screen_w - btn_w) // 2, 
            btn_y, 
            btn_w, 
            btn_h
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # 1. Нажатие на кнопку смены уровня
                if center_btn_rect.collidepoint(mx, my) and event.button == 1:
                    # Циклическая смена уровня
                    current_level_idx = (current_level_idx + 1) % len(LEVEL_ORDER)
                    current_level_name = LEVEL_ORDER[current_level_idx]
                    
                    # Пересоздаем игру
                    board = create_board_for_level(current_level_name)
                    screen = create_window_for_board(board)
                    start_ticks = pygame.time.get_ticks()
                    final_time_sec = 0

                # 2. Нажатие на игровое поле
                elif my >= HUD_HEIGHT:
                    col = mx // CELL_SIZE
                    row = (my - HUD_HEIGHT) // CELL_SIZE
                    
                    if 0 <= row < board.height and 0 <= col < board.width:
                        # Если игра ЗАКОНЧЕНА
                        if board.game_over:
                            if event.button == 1: # ЛКМ для рестарта
                                board.reset()
                                start_ticks = pygame.time.get_ticks()
                                final_time_sec = 0
                        
                        # Если игра ИДЕТ
                        else:
                            if event.button == 1: # ЛКМ
                                board.open_cell(row, col)
                            elif event.button == 3: # ПКМ
                                board.toggle_flag(row, col)

        # Таймер и рекорды
        if board.game_over:
            if final_time_sec == 0:
                final_time_sec = (pygame.time.get_ticks() - start_ticks) // 1000
                
                if board.win:
                    current_record = high_scores.get(current_level_name)
                    if current_record is None or final_time_sec < current_record:
                        high_scores[current_level_name] = final_time_sec
                        save_high_scores(high_scores)

            elapsed = final_time_sec
        else:
            elapsed = (pygame.time.get_ticks() - start_ticks) // 1000

        # Получаем текущий рекорд для отрисовки
        best_time = high_scores.get(current_level_name)

        draw_game(screen, board, current_level_name, elapsed, center_btn_rect, best_time)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


# ======== Вспомогательные функции ========

def create_board_for_level(level_name: str) -> GameBoard:
    params = LEVELS[level_name]
    return GameBoard(params["width"], params["height"], params["mines"])


def create_window_for_board(board: GameBoard) -> pygame.Surface:
    width = board.width * CELL_SIZE
    height = HUD_HEIGHT + board.height * CELL_SIZE
    return pygame.display.set_mode((width, height))


# ======== Отрисовка ========

def draw_game(screen: pygame.Surface,
              board: GameBoard,
              level_name: str,
              elapsed_sec: int,
              btn_rect: pygame.Rect,
              best_time: int):
    
    screen_rect = screen.get_rect()
    screen.fill(BG_COLOR)

    font_cell = pygame.font.SysFont("Verdana", int(CELL_SIZE * 0.6), bold=True)
    font_btn = pygame.font.SysFont("Arial", 18, bold=True)
    font_record = pygame.font.SysFont("Arial", 14)

    # ----- Сетка поля -----
    for r in range(board.height):
        for c in range(board.width):
            cell = board.board[r][c]
            x = c * CELL_SIZE
            y = HUD_HEIGHT + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            if cell.is_open:
                color = CELL_OPEN_COLOR
            else:
                color = CELL_CLOSED_COLOR
            
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)

            center = rect.center
            
            if cell.is_open:
                if cell.is_mine:
                    if board.game_over:
                        pygame.draw.rect(screen, (100, 50, 50), rect)
                        pygame.draw.rect(screen, GRID_COLOR, rect, 1)
                    draw_mine(screen, center[0], center[1], CELL_SIZE//3)
                else:
                    num = cell.adjacent_mines
                    if num > 0:
                        txt_color = NUMBER_COLORS.get(num, (255, 255, 255))
                        num_surf = font_cell.render(str(num), True, txt_color)
                        num_rect = num_surf.get_rect(center=center)
                        screen.blit(num_surf, num_rect)
            else:
                if cell.is_flagged:
                    draw_flag(screen, center[0], center[1])
                
                if board.game_over and cell.is_mine and not cell.is_flagged:
                     draw_mine(screen, center[0], center[1], CELL_SIZE//3, color=(150, 100, 100))
                
                if board.game_over and not cell.is_mine and cell.is_flagged:
                    draw_flag(screen, center[0], center[1])
                    pygame.draw.line(screen, (0,0,0), rect.topleft, rect.bottomright, 2)
                    pygame.draw.line(screen, (0,0,0), rect.topright, rect.bottomleft, 2)


    # ----- HUD -----
    hud_rect = pygame.Rect(0, 0, screen_rect.width, HUD_HEIGHT)
    pygame.draw.rect(screen, HUD_BG_COLOR, hud_rect)
    pygame.draw.line(screen, (0, 0, 0), (0, HUD_HEIGHT-1), (screen_rect.width, HUD_HEIGHT-1), 2)

    # -- Табло мин --
    mines_left = max(0, board.remaining_mines)
    led_w, led_h = 70, 35
    
    # Используем btn_rect.y, чтобы выровнять индикаторы по кнопке
    led_y = btn_rect.y 
    
    mines_rect = pygame.Rect(20, led_y, led_w, led_h)
    draw_led_display(screen, mines_rect, mines_left)

    # -- Табло таймера --
    time_val = min(elapsed_sec, 999)
    time_rect = pygame.Rect(screen_rect.width - 20 - led_w, led_y, led_w, led_h)
    draw_led_display(screen, time_rect, time_val)

    # -- Центральная кнопка --
    pygame.draw.rect(screen, BTN_COLOR, btn_rect)
    pygame.draw.rect(screen, BTN_BORDER, btn_rect, 1)
    
    btn_text = f"{level_name}"
    text_surf = font_btn.render(btn_text, True, BTN_TEXT_COLOR)
    text_rect = text_surf.get_rect(center=btn_rect.center)
    screen.blit(text_surf, text_rect)

    # -- Текст рекорда под кнопкой --
    if best_time is not None:
        rec_str = f"Рекорд: {best_time}"
    else:
        rec_str = "Рекорд: --"
    
    rec_surf = font_record.render(rec_str, True, RECORD_TEXT_COLOR)
    # Позиционируем текст чуть ниже кнопки
    rec_rect = rec_surf.get_rect(center=(btn_rect.centerx, btn_rect.bottom + 12))
    screen.blit(rec_surf, rec_rect)


    # ----- Экран победы/поражения -----
    if board.game_over:
        overlay = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        msg = "ПОБЕДА" if board.win else "GAME OVER"
        col = (100, 255, 100) if board.win else (255, 80, 80)
        
        font_big = pygame.font.SysFont("Arial", 40, bold=True)
        
        shadow_surf = font_big.render(msg, True, (0,0,0))
        main_surf = font_big.render(msg, True, col)
        
        center_x = screen_rect.width // 2
        center_y = screen_rect.height // 2 
        
        r_shadow = shadow_surf.get_rect(center=(center_x+2, center_y+2))
        r_main = main_surf.get_rect(center=(center_x, center_y))
        
        screen.blit(shadow_surf, r_shadow)
        screen.blit(main_surf, r_main)
        
        # Подсказка
        font_small = pygame.font.SysFont("Arial", 18)
        hint_surf = font_small.render("Кликните для рестарта", True, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(center_x, center_y + 40))
        screen.blit(hint_surf, hint_rect)


def draw_led_display(surface: pygame.Surface, rect: pygame.Rect, value: int):
    pygame.draw.rect(surface, LED_BG_COLOR, rect)
    pygame.draw.rect(surface, (80, 40, 40), rect, 1)
    
    font_led = pygame.font.SysFont("Consolas", 28, bold=True)
    text_str = f"{value:03d}"
    
    text_surf = font_led.render(text_str, True, LED_FG_COLOR)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)


def draw_flag(surface: pygame.Surface, cx: int, cy: int):
    # Палка
    pygame.draw.line(surface, (200, 200, 200), (cx - 2, cy - 8), (cx - 2, cy + 8), 2)
    # Основание
    pygame.draw.rect(surface, (200, 200, 200), (cx - 4, cy + 6, 6, 2))
    # Полотно флага
    points = [(cx - 2, cy - 9), (cx + 8, cy - 4), (cx - 2, cy + 1)]
    pygame.draw.polygon(surface, FLAG_COLOR, points)


def draw_mine(surface: pygame.Surface, cx: int, cy: int, r: int, color=MINE_COLOR):
    pygame.draw.circle(surface, color, (cx, cy), r)
    # Шипы
    pygame.draw.line(surface, color, (cx - r - 2, cy), (cx + r + 2, cy), 2)
    pygame.draw.line(surface, color, (cx, cy - r - 2), (cx, cy + r + 2), 2)
    pygame.draw.line(surface, color, (cx - r, cy - r), (cx + r, cy + r), 2)
    pygame.draw.line(surface, color, (cx + r, cy - r), (cx - r, cy + r), 2)
    # Блик
    pygame.draw.circle(surface, (255, 255, 255), (cx - r//3, cy - r//3), r//3)
