import random
from dataclasses import dataclass


@dataclass
class Cell:
    """Одна клетка игрового поля."""
    is_mine: bool = False
    is_open: bool = False
    is_flagged: bool = False
    adjacent_mines: int = 0


class GameBoard:
    """Логика игры."""
    def __init__(self, width: int, height: int, mines_count: int):
        if mines_count >= width * height:
            raise ValueError("Слишком много мин для такого поля.")

        self.width = width
        self.height = height
        self.mines_count = mines_count

        self.board: list[list[Cell]] = []
        self.flags_count: int = 0
        self.game_over: bool = False
        self.win: bool = False

        self._create_new_board()


    def _create_new_board(self):
        """Создаём новое поле, расставляем мины и считаем соседей."""
        self.board = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        self.flags_count = 0
        self.game_over = False
        self.win = False

        self._place_mines()
        self._calculate_adjacent_mines()


    def reset(self):
        """Полный сброс игры."""
        self._create_new_board()


    def _place_mines(self):
        """Случайное размещение мин."""
        all_coords = [(r, c) for r in range(self.height) for c in range(self.width)]
        mine_coords = random.sample(all_coords, self.mines_count)
        for r, c in mine_coords:
            self.board[r][c].is_mine = True


    def _calculate_adjacent_mines(self):
        """Подсчёт количества мин вокруг каждой клетки."""
        for r in range(self.height):
            for c in range(self.width):
                if self.board[r][c].is_mine:
                    self.board[r][c].adjacent_mines = 0
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if self._in_bounds(nr, nc) and self.board[nr][nc].is_mine:
                            count += 1
                self.board[r][c].adjacent_mines = count


    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.height and 0 <= c < self.width


    def open_cell(self, r: int, c: int):
        """Открытие клетки. Если мина — игра заканчивается."""
        if not self._in_bounds(r, c) or self.game_over:
            return

        cell = self.board[r][c]
        if cell.is_open or cell.is_flagged:
            return

        cell.is_open = True

        if cell.is_mine:
            self.game_over = True
            self.win = False
            return

        # Если рядом нет мин — рекурсивно открываем соседей
        if cell.adjacent_mines == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self._in_bounds(nr, nc):
                        neighbour = self.board[nr][nc]
                        if not neighbour.is_open and not neighbour.is_mine:
                            self.open_cell(nr, nc)

        self._update_win_condition()


    def toggle_flag(self, r: int, c: int):
        """Поставить/убрать флаг."""
        if not self._in_bounds(r, c) or self.game_over:
            return

        cell = self.board[r][c]
        if cell.is_open:
            return

        if cell.is_flagged:
            cell.is_flagged = False
            self.flags_count -= 1
        else:
            # Можно ограничить количество флагов количеством мин
            if self.flags_count < self.mines_count:
                cell.is_flagged = True
                self.flags_count += 1


    def _update_win_condition(self):
        """Проверка условия победы: все не-мины открыты."""
        for r in range(self.height):
            for c in range(self.width):
                cell = self.board[r][c]
                if not cell.is_mine and not cell.is_open:
                    return
        self.win = True
        self.game_over = True


    @property
    def remaining_mines(self) -> int:
        """Оценка: сколько мин осталось."""
        return self.mines_count - self.flags_count
