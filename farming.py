import pygame
import random
import math
import heapq
from collections import deque

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
NIGHT_COLOR = (0, 0, 30)
DAY_COLOR = (135, 206, 250)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)

pygame.init()

WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crop Plantation Simulation")

time_of_day = 0.0
day_length = 500
temperature = 25.0

GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

class Crop:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.growth_rate = 0.0001
        self.scale = 1.0
        self.matured = False
        self.grid_x = x // GRID_SIZE
        self.grid_y = y // GRID_SIZE

    def grow(self):
        self.scale += self.growth_rate
        if self.scale >= 2.0:
            self.matured = True

class Weed(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super(Weed, self).__init__(*groups)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLACK, (10, 10), 10)  
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.growth_rate = 0.0002
        self.scale = 1.0
        self.grid_x = x // GRID_SIZE
        self.grid_y = y // GRID_SIZE

    def grow(self):
        self.scale += self.growth_rate
        if self.scale >= 1.5:  
            self.remove()

class Drone(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super(Drone, self).__init__(*groups)
        self.image = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.rect(self.image, RED, (0, 0, 40, 20))  
        pygame.draw.circle(self.image, BLACK, (10, 18), 6)  
        pygame.draw.circle(self.image, BLACK, (30, 18), 6)  
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.task = None  
        self.target_index = 0  

    def update(self):
        if self.task == "water":
            self.water_crops()
        elif self.task == "monitor":
            self.monitor_crops()

        self.move_along_path()

    def move_along_path(self):
        x_values = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        y_values = [0, 100, 200, 300, 400, 500, 600, 700]
        waypoints = []  

        for i in x_values:
            for j in y_values:
                waypoints.append((i, j))

        if self.target_index < len(waypoints):
            target_x, target_y = waypoints[self.target_index]
            dx = target_x - self.rect.x
            dy = target_y - self.rect.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance > 0:
                dx /= distance
                dy /= distance

            self.rect.x += int(dx * 5)
            self.rect.y += int(dy * 5)

            if distance < 10:
                self.target_index += 1
        else:
            self.target_index = 0

    def water_crops(self):
        for crop in crops:
            if (
                abs(self.rect.x - crop.x) < 30
                and abs(self.rect.y - crop.y) < 30
            ):
                crop.growth_rate += 0.000010

    def monitor_crops(self):
        print("Drone is monitoring crops.")

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.g = 0  
        self.h = 0  
        self.f = 0  
        self.parent = None

    def __lt__(self, other):
        return self.f < other.f

class Tractor(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super(Tractor, self).__init__(*groups)
        self.image = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.rect(self.image, ORANGE, (0, 0, 40, 20)) 
        pygame.draw.circle(self.image, BLACK, (10, 18), 6)  
        pygame.draw.circle(self.image, BLACK, (30, 18), 6)  
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH)
        self.rect.y = random.randint(0, HEIGHT)
        self.task = None
        self.target_crops = []
        self.path = []
        self.current_target = None
        self.speed = 3
        self.obstacles = set() 

    def update(self):
        self.update_obstacles()
        
        if self.task == "harvest" and self.target_crops:
            if not self.current_target:
                self.current_target = self.find_nearest_crop()
                if self.current_target:
                    start = (self.rect.x // GRID_SIZE, self.rect.y // GRID_SIZE)
                    end = (self.current_target.x // GRID_SIZE, self.current_target.y // GRID_SIZE)
                    self.path = self.a_star_search(start, end)
            
            if self.current_target and self.path:
                self.follow_path()
            elif self.current_target:
                self.move_directly_to_target()
        
        elif random.random() < 0.02:  
            self.rect.x += random.randint(-5, 5)
            self.rect.y += random.randint(-5, 5)
        
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))

    def update_obstacles(self):
        self.obstacles = set()
        
        for weed in weeds_group:
            self.obstacles.add((weed.grid_x, weed.grid_y))
        
        for x in range(GRID_WIDTH):
            self.obstacles.add((x, 0))
            self.obstacles.add((x, GRID_HEIGHT - 1))
        for y in range(GRID_HEIGHT):
            self.obstacles.add((0, y))
            self.obstacles.add((GRID_WIDTH - 1, y))

    def find_nearest_crop(self):
        if not self.target_crops:
            return None
        
        min_dist = float('inf')
        nearest_crop = None
        tx, ty = self.rect.x, self.rect.y
        
        for crop in self.target_crops:
            dist = (crop.x - tx)**2 + (crop.y - ty)**2
            if dist < min_dist:
                min_dist = dist
                nearest_crop = crop
                
        return nearest_crop

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_star_search(self, start, end):
        start_node = Node(start[0], start[1])
        end_node = Node(end[0], end[1])

        open_list = []
        closed_list = set()

        heapq.heappush(open_list, (0, start_node))
        
        open_dict = {start_node: start_node.f}

        while open_list:
            current_node = heapq.heappop(open_list)[1]
            closed_list.add((current_node.x, current_node.y))

            if current_node.x == end_node.x and current_node.y == end_node.y:
                path = []
                current = current_node
                while current is not None:
                    path.append((current.x * GRID_SIZE + GRID_SIZE//2, 
                                current.y * GRID_SIZE + GRID_SIZE//2))
                    current = current.parent
                return path[::-1]  

            children = []
            for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  
                node_x = current_node.x + new_position[0]
                node_y = current_node.y + new_position[1]

                if node_x < 0 or node_x >= GRID_WIDTH or node_y < 0 or node_y >= GRID_HEIGHT:
                    continue

                if (node_x, node_y) in self.obstacles:
                    continue

                new_node = Node(node_x, node_y)
                new_node.parent = current_node
                children.append(new_node)

            for child in children:
                if (child.x, child.y) in closed_list:
                    continue

                child.g = current_node.g + 1
                child.h = self.heuristic((child.x, child.y), (end_node.x, end_node.y))
                child.f = child.g + child.h

                if child in open_dict and open_dict[child] <= child.f:
                    continue

                heapq.heappush(open_list, (child.f, child))
                open_dict[child] = child.f


        return []

    def follow_path(self):
        if not self.path:
            return
            
        target_x, target_y = self.path[0]
        dx = target_x - self.rect.x
        dy = target_y - self.rect.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 5:  
            self.path.pop(0)
            if not self.path:
                if self.current_target in crops:
                    crops.remove(self.current_target)
                    self.target_crops.remove(self.current_target)
                self.current_target = None
                return
        else:
            if distance > 0:
                dx /= distance
                dy /= distance
            
            self.rect.x += int(dx * self.speed)
            self.rect.y += int(dy * self.speed)

    def move_directly_to_target(self):
        if not self.current_target:
            return
            
        dx = self.current_target.x - self.rect.x
        dy = self.current_target.y - self.rect.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 10:  
            if self.current_target in crops:
                crops.remove(self.current_target)
                self.target_crops.remove(self.current_target)
            self.current_target = None
        else:
            if distance > 0:
                dx /= distance
                dy /= distance
            
            self.rect.x += int(dx * self.speed)
            self.rect.y += int(dy * self.speed)

    def harvest_crops(self):
        matured_crops = [crop for crop in crops if crop.matured]
        self.target_crops = matured_crops
        self.task = "harvest"

def generate_crops(spacing):
    crops = []
    for x in range(0, WIDTH, 2 * spacing):
        for y in range(0, HEIGHT, 2 * spacing):
            crops.append(Crop(x, y))
    return crops

def generate_weeds(num_weeds):
    weeds = pygame.sprite.Group()
    for _ in range(num_weeds):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        weeds.add(Weed(x, y))
    return weeds

crops = generate_crops(50) 

weeds = generate_weeds(5) 

all_sprites = pygame.sprite.Group()
drones = pygame.sprite.Group()
tractors = pygame.sprite.Group()
weeds_group = pygame.sprite.Group(weeds)  

drone1 = Drone(WIDTH // 2, HEIGHT // 2, all_sprites, drones)
all_sprites.add(drone1)

tractor1 = Tractor(all_sprites, tractors)
all_sprites.add(tractor1)

font = pygame.font.Font(None, 36)

def reset_drone():
    drone1.task = None
    drone1.target_index = 0

clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                time_of_day -= 10  
            elif event.key == pygame.K_DOWN:
                time_of_day += 10 
            elif event.key == pygame.K_w:
                reset_drone()  
                drone1.task = "water"
            elif event.key == pygame.K_m:
                reset_drone() 
                drone1.task = "monitor"
            elif event.key == pygame.K_h:
                tractor1.task = "harvest"
                tractor1.target_crops = [crop for crop in crops if crop.matured]

    time_of_day = (time_of_day + 1) % day_length

    if time_of_day < day_length / 2:
        screen.fill(DAY_COLOR)
    else:
        screen.fill(NIGHT_COLOR)

    temperature = 30.0 if time_of_day < day_length / 2 else 15.0

    for crop in crops:
        crop.grow()

    weeds_group.update()

    for weed in weeds_group:
        weed.grow()
        if weed.scale >= 1.5:  
            weeds_group.remove(weed)
            tractor1.task = "remove_weeds"
            tractor1.target_weeds = [weed]

    all_sprites.update()

    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y), 1)

    for crop in crops:
        custom_tree_shape = [(0, 0), (10, 0), (5, -20), (0, 0), (-5, -20), (-10, 0), (0, 0)]

        scaled_tree_shape = [(p[0] * crop.scale + crop.x, p[1] * crop.scale + crop.y) for p in custom_tree_shape]

        pygame.draw.polygon(screen, GREEN, scaled_tree_shape)

    weeds_group.draw(screen)

    for drone in drones:
        custom_car_shape = [(-15, -10), (15, -10), (15, 10), (-15, 10)]

        scaled_car_shape = [(p[0] + drone.rect.x, p[1] + drone.rect.y) for p in custom_car_shape]

        pygame.draw.polygon(screen, RED, scaled_car_shape)

    for tractor in tractors:
        custom_tractor_shape = [(-15, -10), (15, -10), (20, 0), (15, 10), (-15, 10)]

        scaled_tractor_shape = [(p[0] + tractor.rect.x, p[1] + tractor.rect.y) for p in custom_tractor_shape]

        pygame.draw.polygon(screen, ORANGE, scaled_tractor_shape)

        if tractor.path:
            for i in range(len(tractor.path) - 1):
                pygame.draw.line(screen, BLUE, tractor.path[i], tractor.path[i+1], 2)

    text = font.render(f"Time of Day: {int(time_of_day)} Temperature: {int(temperature)}", True, WHITE)
    screen.blit(text, (10, 10))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()