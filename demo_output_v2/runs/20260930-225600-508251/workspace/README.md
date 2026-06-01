# 贪吃蛇游戏（Snake）

使用 Python 3 与 pygame 实现的可运行贪吃蛇游戏。

## 环境要求

- Python 3.8 或更高版本（C-1）
- pygame 库

## 依赖安装

```bash
pip install pygame
```

若系统同时存在 Python 2/3，可使用：

```bash
python3 -m pip install pygame
```

本游戏仅依赖 pygame 与 Python 标准库（random、sys、collections、typing、logging），不引入其他第三方依赖（C-2）。

## 启动游戏

在项目目录下执行：

```bash
python snake_game.py
```

或：

```bash
python3 snake_game.py
```

运行后会出现游戏窗口，蛇与食物可见（AC-1）。

## 操作说明

- 方向键（↑ ↓ ← →）或 WASD 控制蛇的移动方向（FR-2、AC-2）。
- 蛇不能直接反向移动（例如向右时不能立即向左），反向输入会被忽略（FR-3、AC-2）。
- 方向切换在下一帧生效，输入响应及时（QR-2）。
- 吃到食物后蛇身长度增加 1 节，分数增加 10 分（FR-5、AC-3）。
- 蛇头撞到墙壁或自身时游戏结束，界面显示 GAME OVER 与最终分数（FR-6、AC-4）。
- 游戏过程中顶部信息栏实时显示当前分数（FR-7、AC-5）。
- 游戏结束后按 R 或 空格 重新开始，分数与蛇身重置（FR-8、AC-6）。
- 按 ESC 或关闭窗口退出游戏，pygame 资源会被正常释放（QR-4）。

## 计分规则

| 事件 | 分数变化 |
| --- | --- |
| 吃到 1 个食物 | +10 分 |
| 撞墙 / 撞自身 | 游戏结束，分数保留显示 |

每吃一个食物，蛇身长度增加 1 节，食物会在空白网格中重新随机生成，且不与蛇身重叠（FR-4）。

## 可调整常量

所有可调参数集中在 `snake_game.py` 顶部（C-3）：

| 常量 | 说明 |
| --- | --- |
| `CELL_SIZE` | 每个网格像素大小 |
| `GRID_COLS` / `GRID_ROWS` | 横向 / 纵向网格数量 |
| `HUD_HEIGHT` | 顶部信息栏高度 |
| `LOGIC_FPS` | 游戏逻辑更新频率（蛇移动速度） |
| `RENDER_FPS` | 渲染帧率（画面平滑度） |
| `SCORE_PER_FOOD` | 每吃一个食物增加的分数 |
| `INITIAL_SNAKE_LENGTH` | 初始蛇长 |
| `INITIAL_SNAKE_POS` | 蛇头初始网格坐标 |
| `INITIAL_DIRECTION` | 初始方向 |
| `RESTART_KEYS` | 结束后重开按键 |
| `COLOR_*` | 各类颜色 |

## 代码结构

- 常量配置：窗口、网格、逻辑/渲染帧率、颜色、分数、初始状态、按键映射。
- 纯逻辑函数：`is_opposite`、`next_head_position`、`is_out_of_bounds`、`spawn_food`、`build_initial_snake`。
- `GameState`：状态管理，包含 `reset`、`request_direction`、`step`，内部缓存蛇身集合增量更新。
- 渲染函数：`draw_grid`、`draw_snake`、`draw_food`、`draw_hud`、`draw_game_over`、`render`。
- 输入处理：`handle_events`，使用输入队列缓冲同帧多次转向。
- 主循环：`main`，逻辑更新与渲染分离，含异常捕获与友好提示。

## 测试

项目包含验收与边界测试，使用 SDL dummy 驱动，无需真实桌面：

```bash
python -m unittest discover -s tests -v
```

覆盖 AC-1 至 AC-7 及边界：食物不与蛇重叠、撞墙、自撞、尾部豁免、填满网格、资源释放。

## 常见问题

- 提示 `ModuleNotFoundError: No module named 'pygame'`：请先执行 `pip install pygame`。
- 窗口无响应或卡顿：确认未同时运行多个实例，并检查 `LOGIC_FPS` / `RENDER_FPS` 设置是否过高。
- 无图形界面环境（如纯 SSH 服务器）无法运行 pygame 窗口，请在带桌面的环境中运行。
