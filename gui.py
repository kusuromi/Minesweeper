# gui.py
import sys
import pygame

from logic import GameBoard

# ======== Уровни сложности ========

LEVELS = {
    "Простой":  {"width": 9,  "height": 9,  "mines": 10},
    "Средний":  {"width": 16, "height": 16, "mines": 40},
    "Сложный":  {"width": 30, "height": 16, "mines": 99},
}

LEVEL_ORDER = ["Простой", "Средний", "Сложный"]

CELL_SIZE = 40
HUD_HEIGHT = 50  # верхняя панель

# Кнопка выбора уровня
LEVEL_BTN_X = 10
LEVEL_BTN_Y = 10
LEVEL_BTN_W = 120
LEVEL_BTN_H = 30

# Цвета (в стиле Google Minesweeper)
TOP_BAR_COLOR = (84, 120, 48)
BOARD_CLOSED_LIGHT = (195, 222, 112)
BOARD_CLOSED_DARK = (184, 212, 100)
BOARD_OPEN_LIGHT = (220, 240, 155)
BOARD_OPEN_DARK = (210, 230, 145)
FLAG_COLOR = (230, 0, 0)
TIMER_ICON_COLOR = (245, 190, 70)


# ======== Основная функция ========

def run_game():
    pygame.init()
    pygame.display.set_caption("Сапёр (курсовая работа)")
    clock = pygame.time.Clock()

    current_level = "Простой"
    board = create_board_for_level(current_level)
    screen = create_window_for_board(board)

    start_ticks = pygame.time.get_ticks()
    final_time_sec = 0
    level_menu_open = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    board.reset()
                    start_ticks = pygame.time.get_ticks()
                    final_time_sec = 0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    mx, my = pygame.mouse.get_pos()

                    level_btn_rect = get_level_button_rect()
                    if level_btn_rect.collidepoint(mx, my):
                        level_menu_open = not level_menu_open
                    elif level_menu_open:
                        clicked_level = handle_level_menu_click(mx, my)
                        if clicked_level is not None and clicked_level != current_level:
                            current_level = clicked_level
                            board = create_board_for_level(current_level)
                            screen = create_window_for_board(board)
                            start_ticks = pygame.time.get_ticks()
                            final_time_sec = 0
                        level_menu_open = False
                    else:
                        if my >= HUD_HEIGHT:
                            col = mx // CELL_SIZE
                            row = (my - HUD_HEIGHT) // CELL_SIZE
                            if 0 <= row < board.height and 0 <= col < board.width:
                                if not board.game_over:
                                    board.open_cell(row, col)

                elif event.button == 3:  # ПКМ
                    mx, my = pygame.mouse.get_pos()
                    if my >= HUD_HEIGHT:
                        col = mx // CELL_SIZE
                        row = (my - HUD_HEIGHT) // CELL_SIZE
                        if 0 <= row < board.height and 0 <= col < board.width:
                            if not board.game_over:
                                board.toggle_flag(row, col)

        # таймер
        if board.game_over:
            if final_time_sec == 0:
                final_time_sec = (pygame.time.get_ticks() - start_ticks) // 1000
            elapsed = final_time_sec
        else:
            elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
            final_time_sec = elapsed

        draw_game(screen, board, current_level, elapsed, level_menu_open)

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


def get_level_button_rect() -> pygame.Rect:
    return pygame.Rect(LEVEL_BTN_X, LEVEL_BTN_Y, LEVEL_BTN_W, LEVEL_BTN_H)


def get_level_menu_rects():
    rects = []
    base = get_level_button_rect()
    for i, level_name in enumerate(LEVEL_ORDER):
        r = pygame.Rect(
            base.left,
            base.bottom + 4 + i * (LEVEL_BTN_H + 2),
            LEVEL_BTN_W,
            LEVEL_BTN_H,
        )
        rects.append((level_name, r))
    return rects


def handle_level_menu_click(mx: int, my: int):
    for level_name, rect in get_level_menu_rects():
        if rect.collidepoint(mx, my):
            return level_name
    return None


# ======== Отрисовка ========

def draw_game(screen: pygame.Surface,
              board: GameBoard,
              level_name: str,
              elapsed_sec: int,
              level_menu_open: bool):
    screen_rect = screen.get_rect()

    # общий фон
    screen.fill(BOARD_CLOSED_LIGHT)

    font_hud = pygame.font.SysFont("Arial", 20, bold=True)
    font_cell = pygame.font.SysFont("Arial", CELL_SIZE // 2, bold=True)

    # ----- сначала рисуем поле -----
    for r in range(board.height):
        for c in range(board.width):
            cell = board.board[r][c]
            x = c * CELL_SIZE
            y = HUD_HEIGHT + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            if cell.is_open:
                base_color = BOARD_OPEN_LIGHT if (r + c) % 2 == 0 else BOARD_OPEN_DARK
            else:
                base_color = BOARD_CLOSED_LIGHT if (r + c) % 2 == 0 else BOARD_CLOSED_DARK
            pygame.draw.rect(screen, base_color, rect)
            pygame.draw.rect(screen, (150, 170, 90), rect, 1)

            if cell.is_open:
                if cell.is_mine:
                    pygame.draw.circle(screen, (255, 0, 0), rect.center, CELL_SIZE // 3)
                else:
                    num = cell.adjacent_mines
                    if num > 0:
                        color = number_color(num)
                        num_surf = font_cell.render(str(num), True, color)
                        num_rect = num_surf.get_rect(center=rect.center)
                        screen.blit(num_surf, num_rect)
            else:
                if cell.is_flagged:
                    draw_flag_icon(screen, rect.centerx, rect.centery)
                if board.game_over and cell.is_mine and not cell.is_flagged:
                    pygame.draw.circle(screen, (255, 0, 0), rect.center, CELL_SIZE // 3)

    # ----- затем HUD, чтобы быть поверх поля -----
    hud_rect = pygame.Rect(0, 0, screen_rect.width, HUD_HEIGHT)
    pygame.draw.rect(screen, TOP_BAR_COLOR, hud_rect)

    # кнопка уровня
    level_btn_rect = get_level_button_rect()
    pygame.draw.rect(screen, (255, 255, 255), level_btn_rect, border_radius=6)
    pygame.draw.rect(screen, (200, 200, 200), level_btn_rect, 1, border_radius=6)

    level_text_surf = font_hud.render(level_name, True, (0, 0, 0))
    level_text_rect = level_text_surf.get_rect()
    level_text_rect.centery = level_btn_rect.centery
    level_text_rect.left = level_btn_rect.left + 8
    screen.blit(level_text_surf, level_text_rect)

    arrow_x = level_btn_rect.right - 15
    arrow_y = level_btn_rect.centery
    pygame.draw.polygon(
        screen,
        (0, 0, 0),
        [(arrow_x - 6, arrow_y - 3), (arrow_x + 6, arrow_y - 3), (arrow_x, arrow_y + 4)],
    )

    # флаг и количество мин
    flag_icon_center_y = HUD_HEIGHT // 2
    flag_icon_x = level_btn_rect.right + 20
    draw_flag_icon(screen, flag_icon_x, flag_icon_center_y)

    flags_text = str(board.remaining_mines)
    flags_text_surf = font_hud.render(flags_text, True, (255, 255, 255))
    flags_text_rect = flags_text_surf.get_rect()
    flags_text_rect.midleft = (flag_icon_x + 14, flag_icon_center_y)
    screen.blit(flags_text_surf, flags_text_rect)

    # таймер
    elapsed_display = min(elapsed_sec, 999)
    time_str = f"{elapsed_display:03d}"

    time_text_surf = font_hud.render(time_str, True, (255, 255, 255))
    time_text_rect = time_text_surf.get_rect()
    time_text_rect.centery = HUD_HEIGHT // 2
    time_text_rect.right = screen_rect.width - 10
    screen.blit(time_text_surf, time_text_rect)

    timer_icon_center_x = time_text_rect.left - 16
    timer_icon_center_y = HUD_HEIGHT // 2
    draw_timer_icon(screen, timer_icon_center_x, timer_icon_center_y)

    # выпадающее меню уровней — рисуем поверх всего
    if level_menu_open:
        draw_level_menu(screen, font_hud, level_name)

    # сообщение о конце игры
    if board.game_over:
        overlay = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        msg = "Вы победили!" if board.win else "Вы проиграли!"
        msg_surf = font_hud.render(msg, True, (255, 255, 255))
        msg_rect = msg_surf.get_rect(center=(screen_rect.width // 2, screen_rect.height // 2))
        screen.blit(msg_surf, msg_rect)


def draw_flag_icon(surface: pygame.Surface, cx: int, cy: int):
    pole_height = 18
    pole_rect = pygame.Rect(cx - 1, cy - pole_height // 2, 2, pole_height)
    pygame.draw.rect(surface, (120, 70, 20), pole_rect)

    flag_points = [
        (cx + 1, cy - pole_height // 2),
        (cx + 14, cy - pole_height // 2 + 5),
        (cx + 1, cy - pole_height // 2 + 10),
    ]
    pygame.draw.polygon(surface, FLAG_COLOR, flag_points)


def draw_timer_icon(surface: pygame.Surface, cx: int, cy: int):
    radius = 10
    pygame.draw.circle(surface, TIMER_ICON_COLOR, (cx, cy), radius)
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius - 3)

    pygame.draw.line(surface, (0, 0, 0), (cx, cy), (cx, cy - 4), 2)
    pygame.draw.line(surface, (0, 0, 0), (cx, cy), (cx + 3, cy + 2), 2)

    pygame.draw.line(surface, TIMER_ICON_COLOR, (cx - 6, cy - radius - 2), (cx - 2, cy - radius + 2), 2)
    pygame.draw.line(surface, TIMER_ICON_COLOR, (cx + 2, cy - radius + 2), (cx + 6, cy - radius - 2), 2)


def draw_level_menu(screen: pygame.Surface, font_hud: pygame.font.Font, current_level: str):
    for level_name, rect in get_level_menu_rects():
        if level_name == current_level:
            pygame.draw.rect(screen, (240, 240, 240), rect, border_radius=6)
        else:
            pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), rect, 1, border_radius=6)

        text_surf = font_hud.render(level_name, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)


def number_color(num: int) -> tuple[int, int, int]:
    colors = {
        1: (0, 0, 255),
        2: (0, 128, 0),
        3: (255, 0, 0),
        4: (0, 0, 128),
        5: (128, 0, 0),
        6: (0, 128, 128),
        7: (0, 0, 0),
        8: (128, 128, 128),
    }
    return colors.get(num, (0, 0, 0))

