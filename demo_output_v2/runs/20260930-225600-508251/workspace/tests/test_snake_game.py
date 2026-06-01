"""贪吃蛇游戏验收与边界测试。

运行：
    python -m unittest discover -s tests -v

使用 SDL dummy 驱动，无需真实桌面即可运行。
"""

import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import snake_game as sg  # noqa: E402


class LogicTests(unittest.TestCase):
    """纯逻辑函数测试（AC-2、AC-3、AC-4 边界）。"""

    def test_is_opposite(self):
        self.assertTrue(sg.is_opposite(sg.LEFT, sg.RIGHT))
        self.assertTrue(sg.is_opposite(sg.UP, sg.DOWN))
        self.assertFalse(sg.is_opposite(sg.UP, sg.LEFT))

    def test_next_head_position(self):
        self.assertEqual(sg.next_head_position((5, 5), sg.RIGHT), (6, 5))
        self.assertEqual(sg.next_head_position((5, 5), sg.UP), (5, 4))

    def test_is_out_of_bounds(self):
        self.assertTrue(sg.is_out_of_bounds((-1, 0)))
        self.assertTrue(sg.is_out_of_bounds((0, -1)))
        self.assertTrue(sg.is_out_of_bounds((sg.GRID_COLS, 0)))
        self.assertTrue(sg.is_out_of_bounds((0, sg.GRID_ROWS)))
        self.assertFalse(sg.is_out_of_bounds((0, 0)))
        self.assertFalse(sg.is_out_of_bounds((sg.GRID_COLS - 1, sg.GRID_ROWS - 1)))

    def test_spawn_food_not_on_snake(self):
        snake = [(x, 0) for x in range(sg.GRID_COLS)]
        rng = random.Random(1)
        for _ in range(50):
            food = sg.spawn_food(snake, rng)
            self.assertIsNotNone(food)
            self.assertNotIn(food, snake)

    def test_spawn_food_full_grid_returns_none(self):
        full = [(x, y) for y in range(sg.GRID_ROWS) for x in range(sg.GRID_COLS)]
        self.assertIsNone(sg.spawn_food(full, random.Random(0)))

    def test_initial_snake(self):
        snake = sg.build_initial_snake()
        self.assertEqual(len(snake), sg.INITIAL_SNAKE_LENGTH)
        self.assertEqual(snake[0], sg.INITIAL_SNAKE_POS)


class StateTests(unittest.TestCase):
    """GameState 行为测试（AC-2、AC-3、AC-4、AC-6）。"""

    def setUp(self):
        self.state = sg.GameState(random.Random(42))

    def test_no_reverse(self):
        self.state.request_direction(sg.LEFT)
        self.state.step()
        self.assertEqual(self.state.direction, sg.INITIAL_DIRECTION)

    def test_direction_applies_next_frame(self):
        self.state.request_direction(sg.UP)
        self.assertEqual(self.state.direction, sg.INITIAL_DIRECTION)
        self.state.step()
        self.assertEqual(self.state.direction, sg.UP)

    def test_input_queue_buffers_multiple_turns(self):
        self.state.request_direction(sg.UP)
        self.state.request_direction(sg.LEFT)
        self.state.step()
        self.assertEqual(self.state.direction, sg.UP)
        self.state.step()
        self.assertEqual(self.state.direction, sg.LEFT)

    def test_eat_food_grows_and_scores(self):
        head = self.state.snake[0]
        self.state.food = (head[0] + 1, head[1])
        before_len = len(self.state.snake)
        before_score = self.state.score
        self.state.step()
        self.assertEqual(len(self.state.snake), before_len + 1)
        self.assertEqual(self.state.score, before_score + sg.SCORE_PER_FOOD)
        self.assertNotIn(self.state.food, self.state.snake_set)

    def test_snake_set_consistent_after_move(self):
        self.state.step()
        self.assertEqual(self.state.snake_set, set(self.state.snake))

    def test_wall_collision_ends_game(self):
        self.state.snake.clear()
        self.state.snake.append((sg.GRID_COLS - 1, 5))
        self.state.snake_set = set(self.state.snake)
        self.state.direction = sg.RIGHT
        self.state.pending_direction = sg.RIGHT
        self.state.food = (0, 0)
        self.state.step()
        self.assertTrue(self.state.game_over)

    def test_self_collision_ends_game(self):
        self.state.snake.clear()
        for cell in [(5, 5), (4, 5), (4, 6), (5, 6), (6, 6)]:
            self.state.snake.append(cell)
        self.state.snake_set = set(self.state.snake)
        self.state.direction = sg.DOWN
        self.state.pending_direction = sg.DOWN
        self.state.food = (0, 0)
        self.state.step()
        self.assertTrue(self.state.game_over)

    def test_tail_cell_exempt_when_not_eating(self):
        self.state.snake.clear()
        for cell in [(5, 5), (4, 5), (4, 6), (5, 6)]:
            self.state.snake.append(cell)
        self.state.snake_set = set(self.state.snake)
        self.state.direction = sg.DOWN
        self.state.pending_direction = sg.DOWN
        self.state.food = (0, 0)
        self.state.step()
        self.assertFalse(self.state.game_over)

    def test_reset_clears_state(self):
        self.state.score = 100
        self.state.game_over = True
        self.state.reset()
        self.assertEqual(self.state.score, 0)
        self.assertFalse(self.state.game_over)
        self.assertEqual(len(self.state.snake), sg.INITIAL_SNAKE_LENGTH)


class RenderTests(unittest.TestCase):
    """渲染与资源释放测试（AC-1、AC-5、QR-4）。"""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((sg.WINDOW_WIDTH, sg.WINDOW_HEIGHT))
        cls.font = pygame.font.SysFont("consolas,menlo,monospace", 20)
        cls.big_font = pygame.font.SysFont("consolas,menlo,monospace", 44, bold=True)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_render_runs(self):
        state = sg.GameState(random.Random(7))
        sg.render(self.screen, state, self.font, self.big_font)
        state.game_over = True
        sg.render(self.screen, state, self.font, self.big_font)

    def test_hud_shows_score(self):
        state = sg.GameState(random.Random(7))
        state.score = 30
        sg.render(self.screen, state, self.font, self.big_font)
        self.assertEqual(state.score, 30)


if __name__ == "__main__":
    unittest.main()
