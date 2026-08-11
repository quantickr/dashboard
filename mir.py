import pygame
import sys
import os


WIDTH, HEIGHT = 1200, 800
TOOLBAR_HEIGHT = 80
BACKGROUND_COLOR = (30, 30, 30)
CANVAS_BG = (255, 255, 255)


class Button:
    def __init__(self, rect, label, callback, bg, fg=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.bg = bg
        self.fg = fg

    def draw(self, surface, font):
        pygame.draw.rect(surface, self.bg, self.rect, border_radius=6)
        text_surf = font.render(self.label, True, self.fg)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()


class DrawingBoard:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Доска для рисования (без Tkinter)")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 22)

        # Холст (под тулбаром)
        self.canvas_rect = pygame.Rect(0, TOOLBAR_HEIGHT, WIDTH, HEIGHT - TOOLBAR_HEIGHT)
        self.canvas = pygame.Surface(self.canvas_rect.size)
        self.canvas.fill(CANVAS_BG)

        # Состояние рисования
        self.current_tool = "brush"  # brush, line, rect, circle, ellipse
        self.brush_size = 5
        self.color = (0, 0, 0)
        self.drawing = False
        self.last_pos = None
        self.shape_start = None
        self.canvas_backup = None  # для предпросмотра фигур

        # UI
        self.buttons = []
        self.palette = []
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        x = 10
        y = 10
        w = 90
        h = 28
        margin = 5

        def add_btn(label, cb, bg):
            nonlocal x
            self.buttons.append(Button((x, y, w, h), label, cb, bg))
            x += w + margin

        add_btn("Кисть", lambda: self._set_tool("brush"), (76, 175, 80))
        add_btn("Линия", lambda: self._set_tool("line"), (33, 150, 243))
        add_btn("Прямоуг.", lambda: self._set_tool("rect"), (255, 152, 0))
        add_btn("Круг", lambda: self._set_tool("circle"), (156, 39, 176))
        add_btn("Эллипс", lambda: self._set_tool("ellipse"), (233, 30, 99))

        x += 10
        self.buttons.append(Button((x, y, 30, h), "-", self._dec_brush, (97, 97, 97)))
        x += 30 + margin
        self.buttons.append(Button((x, y, 30, h), "+", self._inc_brush, (97, 97, 97)))
        x += 30 + margin

        x += 10
        self.buttons.append(Button((x, y, 80, h), "Открыть", self.load_image, (96, 125, 139)))
        x += 80 + margin
        self.buttons.append(Button((x, y, 80, h), "Сохран.", self.save_image, (0, 150, 136)))
        x += 80 + margin
        self.buttons.append(Button((x, y, 80, h), "Очистить", self.clear_canvas, (244, 67, 54)))
        x += 80 + margin

        # Палитра цветов
        palette_colors = [
            (0, 0, 0),
            (255, 255, 255),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 165, 0),
            (255, 0, 255),
        ]
        x += 20
        for c in palette_colors:
            rect = pygame.Rect(x, y + 2, 24, 24)
            self.palette.append((rect, c))
            x += 24 + 4

    def _set_tool(self, tool):
        self.current_tool = tool

    def _dec_brush(self):
        self.brush_size = max(1, self.brush_size - 1)

    def _inc_brush(self):
        self.brush_size = min(100, self.brush_size + 1)

    # ---------- Файлы ----------
    def load_image(self):
        print("Введите путь к изображению (png/jpg и т.п.) и нажмите Enter:")
        path = input().strip().strip("\"'")
        if not path:
            return
        if not os.path.exists(path):
            print("Файл не найден.")
            return
        try:
            img = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return

        img_w, img_h = img.get_size()
        cw, ch = self.canvas.get_size()
        scale = min(cw / img_w, ch / img_h, 1.0)
        if scale != 1.0:
            img = pygame.transform.smoothscale(img, (int(img_w * scale), int(img_h * scale)))
            img_w, img_h = img.get_size()

        self.canvas.fill(CANVAS_BG)
        x = (cw - img_w) // 2
        y = (ch - img_h) // 2
        self.canvas.blit(img, (x, y))
        print("Изображение загружено.")

    def save_image(self):
        print("Введите путь для сохранения (например, drawing.png) и нажмите Enter:")
        path = input().strip().strip("\"'")
        if not path:
            return
        try:
            pygame.image.save(self.canvas, path)
            print(f"Сохранено в {path}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def clear_canvas(self):
        self.canvas.fill(CANVAS_BG)

    # ---------- Рисование ----------
    def handle_mouse_down(self, pos):
        if not self.canvas_rect.collidepoint(pos):
            return

        canvas_pos = (pos[0] - self.canvas_rect.x, pos[1] - self.canvas_rect.y)
        self.drawing = True
        self.last_pos = canvas_pos
        self.shape_start = canvas_pos
        if self.current_tool == "brush":
            pygame.draw.circle(self.canvas, self.color, canvas_pos, self.brush_size)

        if self.current_tool in ("line", "rect", "circle", "ellipse"):
            self.canvas_backup = self.canvas.copy()

    def handle_mouse_move(self, pos):
        if not self.drawing or not self.canvas_rect.collidepoint(pos):
            return

        canvas_pos = (pos[0] - self.canvas_rect.x, pos[1] - self.canvas_rect.y)

        if self.current_tool == "brush":
            if self.last_pos is not None:
                pygame.draw.line(self.canvas, self.color, self.last_pos, canvas_pos, self.brush_size * 2)
            self.last_pos = canvas_pos
            return

        # Фигуры – рисуем предпросмотр из бэкапа
        if self.current_tool in ("line", "rect", "circle", "ellipse") and self.canvas_backup is not None:
            self.canvas = self.canvas_backup.copy()
            x1, y1 = self.shape_start
            x2, y2 = canvas_pos

            if self.current_tool == "line":
                pygame.draw.line(self.canvas, self.color, (x1, y1), (x2, y2), self.brush_size)
            elif self.current_tool == "rect":
                rect = pygame.Rect(min(x1, x2), min(y1, y2),
                                   abs(x2 - x1), abs(y2 - y1))
                pygame.draw.rect(self.canvas, self.color, rect, self.brush_size)
            elif self.current_tool == "circle":
                radius = int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
                pygame.draw.circle(self.canvas, self.color, (x1, y1), radius, self.brush_size)
            elif self.current_tool == "ellipse":
                rect = pygame.Rect(min(x1, x2), min(y1, y2),
                                   abs(x2 - x1), abs(y2 - y1))
                pygame.draw.ellipse(self.canvas, self.color, rect, self.brush_size)

    def handle_mouse_up(self, pos):
        if not self.drawing:
            return
        self.drawing = False
        self.last_pos = None
        self.shape_start = None
        self.canvas_backup = None

    # ---------- Основной цикл ----------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Кнопки
                    for b in self.buttons:
                        b.handle_event(event)
                    # Палитра
                    for rect, col in self.palette:
                        if rect.collidepoint(event.pos):
                            self.color = col
                    # Холст
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_move(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.handle_mouse_up(event.pos)

            self._draw_ui()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def _draw_ui(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Тулбар
        pygame.draw.rect(self.screen, (45, 45, 45), (0, 0, WIDTH, TOOLBAR_HEIGHT))
        for b in self.buttons:
            b.draw(self.screen, self.font)

        # Палитра
        for rect, col in self.palette:
            pygame.draw.rect(self.screen, col, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

        # Толщина кисти и инструмент
        info = f"Инструмент: {self.current_tool} | Толщина: {self.brush_size}"
        info_surf = self.font.render(info, True, (220, 220, 220))
        self.screen.blit(info_surf, (10, TOOLBAR_HEIGHT - 24))

        # Текущий цвет
        color_rect = pygame.Rect(WIDTH - 50, 10, 40, 40)
        pygame.draw.rect(self.screen, self.color, color_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), color_rect, 2)

        # Холст
        self.screen.blit(self.canvas, self.canvas_rect.topleft)


def main():
    board = DrawingBoard()
    board.run()


if __name__ == "__main__":
    main()
