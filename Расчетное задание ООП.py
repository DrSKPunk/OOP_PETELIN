import pygame
import random
import sys


class Map:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.initialize_map()

    def initialize_map(self):
        for i in range(1, self.rows - 1):
            for j in range(1, self.cols - 1):
                if j % 2 != 0 or i % 2 != 0:
                    self.grid[i][j] = 0
                else:
                    self.grid[i][j] = 1

    def get_cell(self, x, y):
        return self.grid[x][y]

    def set_cell(self, x, y, value):
        self.grid[x][y] = value

    def is_valid_position(self, x, y):
        return 0 <= x < self.rows and 0 <= y < self.cols

    def is_road(self, x, y):
        return self.is_valid_position(x, y) and self.grid[x][y] == 0

    def get_random_border_position(self):
        border = random.randint(1, 4)
        if border == 1:
            x = 0
            y = random.choice([i for i, val in enumerate(self.grid[0]) if val == 0])
        elif border == 2:
            x = random.choice([i for i, row in enumerate(self.grid) if row[-1] == 0])
            y = self.cols - 1
        elif border == 3:
            x = self.rows - 1
            y = random.choice([i for i, val in enumerate(self.grid[self.rows - 1]) if val == 0])
        else:
            x = random.choice([i for i, row in enumerate(self.grid) if row[0] == 0])
            y = 0
        return x, y


class Transport:
    def __init__(self, name, transport_type, max_speed, pollution_level, noise_level, energy_type, x, y, color):
        self.name = name
        self.transport_type = transport_type
        self.max_speed = max_speed
        self.pollution_level = pollution_level
        self.noise_level = noise_level
        self.energy_type = energy_type
        self.x = x
        self.y = y
        self.fx = float(x)
        self.fy = float(y)
        self.prev_direction = None
        self.active = True
        self.color = color
        self.target_x = x
        self.target_y = y
        self.is_moving = False
        self.speed_factor = 0.02

    def spawn(self, tile_map):
        self.x, self.y = tile_map.get_random_border_position()
        self.fx = float(self.x)
        self.fy = float(self.y)
        self.target_x = self.x
        self.target_y = self.y
        self.is_moving = False
        tile_map.set_cell(self.x, self.y, self.name)

    def change_direction(self, tile_map, transports):
        directions = {
            1: (1, 0),  # Вниз
            2: (0, 1),  # Вправо
            3: (0, -1),  # Влево
            4: (-1, 0)  # Вверх
        }

        valid_directions = []

        for direction in directions:
            dx, dy = directions[direction]
            new_x, new_y = self.x + dx, self.y + dy

            if tile_map.is_valid_position(new_x, new_y) and tile_map.get_cell(new_x, new_y) == 0:
                valid_directions.append(direction)
            elif tile_map.is_valid_position(new_x, new_y) and tile_map.get_cell(new_x, new_y) != 1:
                for transport in transports:
                    if transport.x == new_x and transport.y == new_y:
                        if self.energy_type == "Электричество" and transport.energy_type != "Электричество":
                            break
                        else:
                            valid_directions.append(direction)
                            break

        if self.prev_direction is not None:
            opposite_direction = {
                1: 4,
                2: 3,
                3: 2,
                4: 1
            }.get(self.prev_direction)
            if opposite_direction in valid_directions:
                valid_directions.remove(opposite_direction)

        if not valid_directions:
            self.spawn_on_other_border(tile_map)
            return self.x, self.y

        direction = random.choice(valid_directions)
        dx, dy = directions[direction]
        self.prev_direction = direction

        return self.x + dx, self.y + dy

    def move(self, tile_map, transports):
        if not self.active or self.is_moving:
            return

        tile_map.set_cell(self.x, self.y, 0)

        new_x, new_y = self.change_direction(tile_map, transports)

        if new_x == self.x and new_y == self.y:
            tile_map.set_cell(self.x, self.y, self.name)
        else:
            self.target_x, self.target_y = new_x, new_y
            self.is_moving = True

    def update_position(self, tile_map):
        if not self.is_moving:
            return

        dx = self.target_x - self.fx
        dy = self.target_y - self.fy
        distance = (dx**2 + dy**2)**0.5

        if distance < 0.1:
            self.fx = self.target_x
            self.fy = self.target_y
            self.x = self.target_x
            self.y = self.target_y
            self.is_moving = False
            tile_map.set_cell(self.x, self.y, self.name)
        else:
            speed = self.max_speed * self.speed_factor
            self.fx += dx * speed / distance
            self.fy += dy * speed / distance

    def spawn_on_other_border(self, tile_map):
        self.spawn(tile_map)

    def is_within_bounds(self, tile_map):
        return 1 <= self.x < tile_map.rows - 1 and 1 <= self.y < tile_map.cols - 1

    def get_pollution_level(self, tile_map):
        return self.pollution_level if self.is_within_bounds(tile_map) else 0

    def get_noise_level(self, tile_map):
        return self.noise_level if self.is_within_bounds(tile_map) else 0


class Gruz(Transport):
    def __init__(self, name, transport_type, max_speed, pollution_level, noise_level, energy_type, x, y, color,
                 max_cargo, current_cargo):
        super().__init__(name, transport_type, max_speed, pollution_level, noise_level, energy_type, x, y, color)
        self.max_cargo = max_cargo
        self.current_cargo = current_cargo

    def get_current_cargo(self, tile_map):
        return self.current_cargo if self.is_within_bounds(tile_map) else 0


class PassengerTransport(Transport):
    def __init__(self, name, transport_type, max_speed, pollution_level, noise_level, energy_type, x, y, color,
                 max_passengers=50, passengers=0):
        super().__init__(name, transport_type, max_speed, pollution_level, noise_level, energy_type, x, y, color)
        self.max_passengers = max_passengers
        self.passengers = passengers

    def get_passengers(self, tile_map):
        return self.passengers if self.is_within_bounds(tile_map) else 0


class CitySimulator:
    def __init__(self):
        pygame.init()

        self.cell_count = 19
        self.cell_size = 40
        self.width = self.cell_count * self.cell_size
        self.height = self.cell_count * self.cell_size
        self.button_height = 50
        self.panel_width = 300
        self.window_width = self.width + self.panel_width

        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'blue': (128, 166, 255),
            'green': (0, 255, 0),
            'purple': (128, 0, 128),
            'gray': (200, 200, 200),
            'dark_gray': (100, 100, 100),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'orange': (255, 165, 0)
        }

        self.rows = self.cell_count + 2
        self.cols = self.cell_count + 2

        self.tile_map = Map(self.rows, self.cols)
        self.transports = self.create_transports()

        self.screen = pygame.display.set_mode((self.window_width, self.height + self.button_height))
        pygame.display.set_caption("Город")

        self.button_rect = pygame.Rect(self.width // 2 - 100, self.height + 10, 200, 30)
        self.button_color = self.colors['gray']
        self.button_text = "Режим"
        self.font = pygame.font.SysFont(None, 30)
        self.info_font = pygame.font.SysFont(None, 24)

        self.clock = pygame.time.Clock()
        self.move_interval = 100
        self.last_move_time = pygame.time.get_ticks()
        self.auto_mode = True
        self.selected_transport = None

        self.transport_types = {
            "Легковой автомобиль": 0,
            "Троллейбус": 0,
            "Грузовик": 0
        }

        self.load_images()

    def load_images(self):

            car_img = pygame.image.load(r"C:\Users\anime\OneDrive\Изображения\машинка.png")
            trolley_img = pygame.image.load(r"C:\Users\anime\OneDrive\Изображения\троллейбус.png")
            truck_img = pygame.image.load(r"C:\Users\anime\OneDrive\Изображения\грузовик.jpg")
            house_img = pygame.image.load(r"C:\Users\anime\OneDrive\Изображения\дом.png")

            self.vehicle_images = {
                "Легковой автомобиль": pygame.transform.scale(car_img, (self.cell_size, self.cell_size)),
                "Троллейбус": pygame.transform.scale(trolley_img, (self.cell_size, self.cell_size)),
                "Грузовик": pygame.transform.scale(truck_img, (self.cell_size, self.cell_size))
            }

            self.house_image = pygame.transform.scale(house_img, (self.cell_size, self.cell_size))


    def create_transports(self):
        transports = [
            # Легковые автомобили
            Transport("Лексус", "Легковой автомобиль", 2, 1, 2, "Бензин", 1, 1, self.colors['red']),
            Transport("Лада", "Легковой автомобиль", 1, 1, 2, "Бензин", 1, 1, self.colors['blue']),
            Transport("Тойота", "Легковой автомобиль", 2, 1, 1, "Бензин", 1, 1, self.colors['yellow']),
            Transport("Хонда", "Легковой автомобиль", 1, 1, 1, "Бензин", 1, 1, self.colors['cyan']),

            # Троллейбусы
            PassengerTransport("Троллейбус 53", "Троллейбус", 1, 0, 1, "Электричество", 1, 1, self.colors['green'],
                               passengers=random.randint(0, 50)),
            PassengerTransport("Троллейбус 1", "Троллейбус", 1, 0, 1, "Электричество", 1, 1, self.colors['green'],
                               passengers=random.randint(0, 50)),
            PassengerTransport("Троллейбус 7", "Троллейбус", 1, 0, 1, "Электричество", 1, 1, self.colors['green'],
                               passengers=random.randint(0, 50)),
            PassengerTransport("Троллейбус 12", "Троллейбус", 1, 0, 1, "Электричество", 1, 1, self.colors['green'],
                               passengers=random.randint(0, 50)),

            # Грузовики
            Gruz("Грузовик Subaru", "Грузовик", 1, 3, 3, "Бензин", 1, 1, self.colors['purple'], 300,
                           random.randint(0, 300)),
            Gruz("Грузовик Volvo", "Грузовик", 1, 3, 3, "Дизель", 1, 1, self.colors['orange'], 400,
                           random.randint(0, 400)),
            Gruz("Грузовик MAN", "Грузовик", 2, 3, 2, "Дизель", 1, 1, self.colors['dark_gray'], 500,
                           random.randint(0, 500))
        ]

        for transport in transports:
            transport.spawn(self.tile_map)

        return transports

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.button_rect.collidepoint(mouse_pos):
                        self.auto_mode = not self.auto_mode
                        self.selected_transport = None
                    elif not self.auto_mode and mouse_pos[1] < self.height:
                        mouse_x, mouse_y = mouse_pos
                        self.selected_transport = None
                        for transport in self.transports:
                            x_screen = (transport.y - 1) * self.cell_size
                            y_screen = (transport.x - 1) * self.cell_size
                            transport_rect = pygame.Rect(x_screen, y_screen, self.cell_size, self.cell_size)
                            if transport_rect.collidepoint(mouse_x, mouse_y):
                                self.selected_transport = transport
                                break

    def update(self):
        current_time = pygame.time.get_ticks()

        if self.auto_mode and current_time - self.last_move_time >= self.move_interval:
            for transport in self.transports:
                transport.move(self.tile_map, self.transports)
            self.last_move_time = current_time

        for transport in self.transports:
            transport.update_position(self.tile_map)

    def draw(self):
        self.screen.fill(self.colors['white'])

        # Сбрасываем счетчики транспорта перед подсчетом
        self.transport_types = {
            "Легковой автомобиль": 0,
            "Троллейбус": 0,
            "Грузовик": 0
        }

        # Рисуем карту (оставляем без изменений)
        for i in range(1, self.rows - 1):
            for j in range(1, self.cols - 1):
                x_screen = (j - 1) * self.cell_size
                y_screen = (i - 1) * self.cell_size
                if self.tile_map.get_cell(i, j) == 1:
                    if self.house_image:
                        self.screen.blit(self.house_image, (x_screen, y_screen))
                    else:
                        pygame.draw.rect(self.screen, self.colors['gray'],
                                         (x_screen, y_screen, self.cell_size, self.cell_size))

        # Рисуем транспорт и считаем его
        for transport in self.transports:
            x_screen = (transport.fy - 1) * self.cell_size
            y_screen = (transport.fx - 1) * self.cell_size

            if 0 <= x_screen < self.width and 0 <= y_screen < self.height:
                transport_type = transport.transport_type
                if self.vehicle_images:
                    vehicle_image = self.vehicle_images.get(transport_type)
                    self.screen.blit(vehicle_image, (x_screen, y_screen))
                else:
                    pygame.draw.rect(self.screen, transport.color,
                                     (x_screen, y_screen, self.cell_size, self.cell_size))

                # Обновляем счетчик для данного типа транспорта
                if transport_type in self.transport_types:
                    self.transport_types[transport_type] += 1

        pygame.draw.rect(self.screen, self.button_color, self.button_rect)
        pygame.draw.rect(self.screen, self.colors['black'], self.button_rect, 2)

        mode_text = "Пуск" if self.auto_mode else "Стоп"
        text_surface = self.font.render(f"{self.button_text} ({mode_text})", True, self.colors['black'])
        text_rect = text_surface.get_rect(center=self.button_rect.center)
        self.screen.blit(text_surface, text_rect)

        total_noise = sum(transport.get_noise_level(self.tile_map) for transport in self.transports)
        total_pollution = sum(transport.get_pollution_level(self.tile_map) for transport in self.transports)
        total_passengers = sum(transport.get_passengers(self.tile_map) for transport in self.transports if
                               isinstance(transport, PassengerTransport))
        total_cargo = sum(transport.get_current_cargo(self.tile_map) for transport in self.transports if
                          isinstance(transport, Gruz))

        panel_rect = pygame.Rect(self.width, 0, self.panel_width, self.height + self.button_height)
        pygame.draw.rect(self.screen, self.colors['blue'], panel_rect)

        noise_text = self.font.render(f"Шум: {total_noise}", True, self.colors['black'])
        pollution_text = self.font.render(f"Загрязнение: {total_pollution}", True, self.colors['black'])
        passengers_text = self.font.render(f"Людей: {total_passengers}", True, self.colors['black'])
        cargo_text = self.font.render(f"Груз: {total_cargo} кг", True, self.colors['black'])

        self.screen.blit(noise_text, (self.width + 10, 20))
        self.screen.blit(pollution_text, (self.width + 10, 40))
        self.screen.blit(passengers_text, (self.width + 10, 60))
        self.screen.blit(cargo_text, (self.width + 10, 80))

        y_offset = 100
        for transport_type, count in self.transport_types.items():
            type_text = self.font.render(f"{transport_type}: {count}", True, self.colors['black'])
            self.screen.blit(type_text, (self.width + 10, y_offset))
            y_offset += 20

        if self.selected_transport is not None:
            info_panel_rect = pygame.Rect(self.width, self.height // 2, self.panel_width, 180)
            pygame.draw.rect(self.screen, self.colors[  'white'], info_panel_rect)
            pygame.draw.rect(self.screen, self.colors['black'], info_panel_rect, 2)

            lines = [
                f"Имя: {self.selected_transport.name}",
                f"Тип: {self.selected_transport.transport_type}",
                f"Макс. скорость: {self.selected_transport.max_speed * 60} км/ч",
                f"Уровень шума: {self.selected_transport.get_noise_level(self.tile_map)}",
                f"Уровень загрязнения: {self.selected_transport.get_pollution_level(self.tile_map)}",
                f"Энергия: {self.selected_transport.energy_type}",
            ]

            if isinstance(self.selected_transport, PassengerTransport):
                lines.append(f"Пассажиры: {self.selected_transport.get_passengers(self.tile_map)}")

            if isinstance(self.selected_transport, Gruz):
                lines.append(f"Груз: {self.selected_transport.get_current_cargo(self.tile_map)} кг")

            y_text = self.height // 2 + 10
            for line in lines:
                text_surface = self.info_font.render(line, True, self.colors['black'])
                self.screen.blit(text_surface, (self.width + 10, y_text))
                y_text += 25

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    simulator = CitySimulator()
    simulator.run()