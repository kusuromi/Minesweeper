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
        # Ограничим мин кол-вом (все клетки - 1), чтобы оставить место для первого клика
        if mines_count >= width * height:
            mines_count = width * height - 1

        self.width = width
        self.height = height
        self.mines_count = mines_count

        self.board: list[list[Cell]] = []
        self.flags_count: int = 0
        self.game_over: bool = False
        self.win: bool = False
        
        # Флаг первого хода
        self.first_move: bool = True

        self._create_new_board()


    def _create_new_board(self):
        """Создаём новое чистое поле. Мины расставим при первом клике."""
        self.board = [[Cell() for _ in range(self.width)] for _ in range(self.height)]
        self.flags_count = 0
        self.game_over = False
        self.win = False
        self.first_move = True


    def reset(self):
        """Полный сброс игры."""
        self._create_new_board()


    def _place_mines(self, exclude_coord: tuple[int, int] = None):
        """Случайное размещение мин с исключением конкретной клетки (для первого хода)."""
        all_coords = []
        for r in range(self.height):
            for c in range(self.width):
                if exclude_coord and (r, c) == exclude_coord:
                    continue
                all_coords.append((r, c))

        count = min(self.mines_count, len(all_coords))
        
        mine_coords = random.sample(all_coords, count)
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
                # Перебор соседей
                for nr, nc in self._get_neighbors(r, c):
                    if self.board[nr][nc].is_mine:
                        count += 1
                self.board[r][c].adjacent_mines = count


    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.height and 0 <= c < self.width


    def _get_neighbors(self, r: int, c: int):
        """Генератор координат соседей."""
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc):
                    yield nr, nc


    def open_cell(self, r: int, c: int):
        """Открыть клетку с учётом логики первого клика и аккорда."""
        if not self._in_bounds(r, c) or self.game_over:
            return

        cell = self.board[r][c]

        # === 1. Обработка первого клика ===
        if self.first_move:
            self.first_move = False
            # Расставляем мины, исключая текущую клетку
            self._place_mines(exclude_coord=(r, c))
            self._calculate_adjacent_mines()
            
            cell = self.board[r][c]

        # === 2. Логика "Аккорда" (Chording) ===
        if cell.is_open and not cell.is_flagged and cell.adjacent_mines > 0:
            # Считаем флаги вокруг
            flags_around = 0
            neighbors = list(self._get_neighbors(r, c))
            for nr, nc in neighbors:
                if self.board[nr][nc].is_flagged:
                    flags_around += 1
            
            # Если количество флагов совпадает с числом на клетке
            if flags_around == cell.adjacent_mines:
                for nr, nc in neighbors:
                    neighbor = self.board[nr][nc]
                    # Открываем только закрытые и не помеченные флагом клетки
                    if not neighbor.is_open and not neighbor.is_flagged:
                        self.open_cell(nr, nc)
            return

        # === 3. Обычное открытие ===
        if cell.is_open or cell.is_flagged:
            return

        cell.is_open = True

        if cell.is_mine:
            self.game_over = True
            self.win = False
            return

        # Если рядом нет мин — рекурсивно открываем соседей
        if cell.adjacent_mines == 0:
            for nr, nc in self._get_neighbors(r, c):
                neighbour = self.board[nr][nc]
                if not neighbour.is_open:
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
            # Ограничение кол-ва флагов кол-вом мин
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
