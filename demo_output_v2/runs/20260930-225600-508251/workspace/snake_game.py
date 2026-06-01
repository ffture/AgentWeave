"""贪吃蛇游戏（Python 3 + pygame）。

运行：
    pip install pygame
    python snake_game.py

控制：
    方向键 或 WASD 控制方向；R 或 空格 在游戏结束后重新开始；ESC 或关闭窗口退出。
"""

import logging
import random
import sys
from collections import deque
from typing import Deque, List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# 可调整常量配置（C-3）
# ---------------------------------------------------------------------------

# 网格与窗口
CELL_SIZE = 24                      # 每个网格像素大小
GRID_COLS = 28                      # 横向网格数量
GRID_ROWS = 22                      # 纵向网格数量
HUD_HEIGHT = 48                     # 顶部信息栏高度（像素）
WINDOW_WIDTH = GRID_COLS * CELL_SIZE
WINDOW_HEIGHT = GRID_ROWS * CELL_SIZE + HUD_HEIGHT

# 帧率：逻辑更新频率与渲染帧率分离，游戏速度与画面平滑度独立可调
LOGIC_FPS = 12                      # 游戏逻辑更新频率（蛇移动速度）
RENDER_FPS = 60                     # 渲染帧率（画面平滑度）

# 颜色
COLOR_BG = (18, 18, 24)
COLOR_GRID = (30, 30, 40)
COLOR_HUD_BG = (12, 12, 18)
COLOR_SNAKE_HEAD = (90, 220, 120)
COLOR_SNAKE_BODY = (60, 170, 95)
COLOR_FOOD = (230, 80, 80)
COLOR_TEXT = (235, 235, 245)
COLOR_TEXT_DIM = (170, 170, 185)
COLOR_OVERLAY = (0, 0, 0, 170)

# 分数与初始状态
SCORE_PER_FOOD = 10                 # 每吃一个食物增加的分数（FR-5）
INITIAL_SNAKE_LENGTH = 3            # 初始蛇长（节）
INITIAL_SNAKE_POS = (GRID_COLS // 2, GRID_ROWS // 2)  # 蛇头初始网格坐标
INITIAL_DIRECTION = (1, 0)          # 初始方向：向右

# 按键映射
RESTART_KEYS = (pygame.K_r, pygame.K_SPACE)  # 结束后重开按键（FR-8）

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# 方向键与 WASD 统一映射为方向向量（FR-2）
KEY_TO_DIRECTION = {
    pygame.K_UP: UP,
    pygame.K_w: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT,
    pygame.K_d: RIGHT,
}

GridPos = Tuple[int, int]


# ---------------------------------------------------------------------------
# 纯逻辑函数（与 pygame 渲染解耦，便于测试）
# ---------------------------------------------------------------------------

def is_opposite(direction: GridPos, other: GridPos) -> bool:
    """判断两个方向是否互为反向（FR-3）。"""
    return direction[0] == -other[0] and direction[1] == -other[1]


def next_head_position(head: GridPos, direction: GridPos) -> GridPos:
    """根据当前蛇头与方向计算下一帧蛇头位置。"""
    return head[0] + direction[0], head[1] + direction[1]


def is_out_of_bounds(pos: GridPos) -> bool:
    """判断位置是否越出游戏区域（撞墙，FR-6）。"""
    x, y = pos
    return x < 0 or y < 0 or x >= GRID_COLS or y >= GRID_ROWS


def spawn_food(snake_cells: List[GridPos], rng: Optional[random.Random] = None) -> Optional[GridPos]:
    """在空白网格中随机生成食物，且不与蛇身重叠（FR-4）。

    从空格集合中随机采样，避免每次全网格扫描。
    若没有可用空格则返回 None（表示通关）。
    """
    rng = rng or random
    occupied = set(snake_cells)
    free_cells = [
        (x, y)
        for y in range(GRID_ROWS)
        for x in range(GRID_COLS)
        if (x, y) not in occupied
    ]
    if not free_cells:
        return None
    return rng.choice(free_cells)


def build_initial_snake() -> Deque[GridPos]:
    """构造初始蛇身，蛇头在 INITIAL_SNAKE_POS，身体沿初始方向反方向延伸。"""
    head_x, head_y = INITIAL_SNAKE_POS
    dx, dy = INITIAL_DIRECTION
    snake: Deque[GridPos] = deque()
    for i in range(INITIAL_SNAKE_LENGTH):
        snake.append((head_x - dx * i, head_y - dy * i))
    return snake


# ---------------------------------------------------------------------------
# 游戏状态管理
# ---------------------------------------------------------------------------

class GameState:
    """保存一局游戏的全部可变状态。

    内部缓存蛇身集合（self.snake_set），移动时增量更新，避免每帧重建 set。
    使用输入队列（self.input_queue）缓冲同一帧内多次转向。
    """

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        """重置分数、蛇身、方向与食物（FR-8、AC-6）。"""
        self.snake: Deque[GridPos] = build_initial_snake()
        self.snake_set = set(self.snake)
        self.direction: GridPos = INITIAL_DIRECTION
        self.pending_direction: GridPos = INITIAL_DIRECTION
        self.input_queue: Deque[GridPos] = deque()
        self.score: int = 0
        self.game_over: bool = False
        self.food: Optional[GridPos] = spawn_food(list(self.snake), self.rng)

    def request_direction(self, new_direction: GridPos) -> None:
        """记录玩家输入方向；禁止直接反向（FR-3、QR-2）。

        输入进入队列，在下一帧移动时按序应用，支持同一帧内多次转向的缓冲。
        与队列中最后一个有效方向比较，避免瞬间自撞。
        """
        reference = self.input_queue[-1] if self.input_queue else self.direction
        if is_opposite(new_direction, reference):
            return
        self.input_queue.append(new_direction)

    def step(self) -> None:
        """推进一帧：应用方向、移动蛇、处理吃食物与碰撞（FR-5、FR-6）。

        碰撞检测与游戏结束逻辑：
        - 撞墙：新蛇头越界即 game_over=True 并立即返回，停止移动。
        - 撞自身：新蛇头落在蛇身集合中即 game_over=True 并立即返回；
          若本帧会吃到食物，尾部不移除，因此尾部格也参与碰撞判定；
          否则尾部会随移动让出，尾部格豁免。
        """
        if self.game_over:
            return

        # 从输入队列取出一个方向，在下一帧生效（QR-2）
        if self.input_queue:
            self.direction = self.input_queue.popleft()
        new_head = next_head_position(self.snake[0], self.direction)

        # 撞墙检测（FR-6、AC-4）
        if is_out_of_bounds(new_head):
            self.game_over = True
            return

        # 撞自身检测（FR-6、AC-4）：若不吃食物，尾部会移动，因此尾部格子不算碰撞
        will_eat = self.food is not None and new_head == self.food
        if will_eat:
            if new_head in self.snake_set:
                self.game_over = True
                return
        else:
            tail = self.snake[-1]
            if new_head in self.snake_set and new_head != tail:
                self.game_over = True
                return

        # 移动蛇：蛇头前插，未吃食物时移除尾部（身体跟随）
        self.snake.appendleft(new_head)
        self.snake_set.add(new_head)
        if will_eat:
            # 吃到食物：长度 +1 节（不移除尾部），分数增加固定值，并重新生成食物（FR-5）
            self.score += SCORE_PER_FOOD
            self.food = spawn_food(list(self.snake), self.rng)
            if self.food is None:
                # 无空格可放食物，视为通关，结束本局
                self.game_over = True
        else:
            tail = self.snake.pop()
            self.snake_set.discard(tail)


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

def cell_to_rect(pos: GridPos) -> pygame.Rect:
    """将网格坐标转换为屏幕矩形（含顶部信息栏偏移）。"""
    x, y = pos
    return pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + HUD_HEIGHT, CELL_SIZE, CELL_SIZE)


def draw_grid(surface: pygame.Surface) -> None:
    """绘制背景网格线。"""
    for col in range(GRID_COLS + 1):
        x = col * CELL_SIZE
        pygame.draw.line(surface, COLOR_GRID, (x, HUD_HEIGHT), (x, WINDOW_HEIGHT))
    for row in range(GRID_ROWS + 1):
        y = row * CELL_SIZE + HUD_HEIGHT
        pygame.draw.line(surface, COLOR_GRID, (0, y), (WINDOW_WIDTH, y))


def draw_snake(surface: pygame.Surface, snake: Deque[GridPos]) -> None:
    """绘制蛇身与蛇头。"""
    for index, cell in enumerate(snake):
        rect = cell_to_rect(cell).inflate(-2, -2)
        color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
        pygame.draw.rect(surface, color, rect, border_radius=5)


def draw_food(surface: pygame.Surface, food: Optional[GridPos]) -> None:
    """绘制食物。"""
    if food is None:
        return
    rect = cell_to_rect(food).inflate(-4, -4)
    pygame.draw.ellipse(surface, COLOR_FOOD, rect)


def draw_hud(surface: pygame.Surface, font: pygame.font.Font, score: int) -> None:
    """绘制顶部信息栏，实时显示分数（FR-7）。"""
    pygame.draw.rect(surface, COLOR_HUD_BG, pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT))
    score_text = font.render(f"Score: {score}", True, COLOR_TEXT)
    surface.blit(score_text, (12, (HUD_HEIGHT - score_text.get_height()) // 2))
    hint_text = font.render("Arrows / WASD", True, COLOR_TEXT_DIM)
    surface.blit(
        hint_text,
        (WINDOW_WIDTH - hint_text.get_width() - 12, (HUD_HEIGHT - hint_text.get_height()) // 2),
    )


def draw_game_over(surface: pygame.Surface, big_font: pygame.font.Font, small_font: pygame.font.Font, score: int) -> None:
    """绘制游戏结束遮罩与提示（FR-8、AC-4）。"""
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(COLOR_OVERLAY)
    surface.blit(overlay, (0, 0))

    title = big_font.render("GAME OVER", True, COLOR_TEXT)
    score_line = small_font.render(f"Final Score: {score}", True, COLOR_TEXT)
    restart_line = small_font.render("Press R or SPACE to restart", True, COLOR_TEXT_DIM)

    center_y = WINDOW_HEIGHT // 2
    surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, center_y - 60))
    surface.blit(score_line, (WINDOW_WIDTH // 2 - score_line.get_width() // 2, center_y))
    surface.blit(restart_line, (WINDOW_WIDTH // 2 - restart_line.get_width() // 2, center_y + 40))


def render(surface: pygame.Surface, state: GameState, font: pygame.font.Font, big_font: pygame.font.Font) -> None:
    """渲染完整一帧。"""
    surface.fill(COLOR_BG)
    draw_grid(surface)
    draw_food(surface, state.food)
    draw_snake(surface, state.snake)
    draw_hud(surface, font, state.score)
    if state.game_over:
        draw_game_over(surface, big_font, font, state.score)


# ---------------------------------------------------------------------------
# 输入处理
# ---------------------------------------------------------------------------

def handle_events(state: GameState) -> bool:
    """处理事件队列。返回 False 表示请求退出程序（QR-4）。

    游戏结束状态下仅响应重开按键（R 或 空格），调用 state.reset() 重置本局；
    其他按键（含方向键）被忽略，避免结束后继续改变方向。
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if state.game_over:
                if event.key in RESTART_KEYS:
                    state.reset()
                continue
            direction = KEY_TO_DIRECTION.get(event.key)
            if direction is not None:
                state.request_direction(direction)
    return True


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------

def main() -> int:
    """程序入口：初始化 pygame，运行主循环，退出时释放资源（FR-1、QR-4）。

    逻辑更新频率（LOGIC_FPS）与渲染帧率（RENDER_FPS）分离，
    使用累加器控制逻辑步进，画面更平滑。
    启动失败时给出友好提示。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        pygame.init()
    except Exception as exc:  # pragma: no cover - 环境相关
        logging.error("pygame 初始化失败：%s", exc)
        logging.error("请确认已安装 pygame（pip install pygame）并具备图形环境。")
        return 1

    try:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("consolas,menlo,monospace", 20)
        big_font = pygame.font.SysFont("consolas,menlo,monospace", 44, bold=True)

        state = GameState()
        running = True
        accumulator = 0.0
        logic_interval = 1.0 / LOGIC_FPS
        while running:
            dt = clock.tick(RENDER_FPS) / 1000.0
            running = handle_events(state)
            if not running:
                break
            accumulator += dt
            while accumulator >= logic_interval:
                state.step()
                accumulator -= logic_interval
            render(screen, state, font, big_font)
            pygame.display.flip()
    except Exception as exc:  # pragma: no cover - 环境相关
        logging.exception("游戏运行过程中发生错误：%s", exc)
        return 1
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
