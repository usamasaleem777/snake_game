import pygame
import random
import math
import os

# Initialize pygame
pygame.init()

# Game window dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultra Snake 3D")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (144, 238, 144)

# Game settings
BLOCK_SIZE = 20
FPS = 15  # Base snake speed
ACCELERATION = 0.2  # Speed increases as snake grows

# Fonts
try:
    title_font = pygame.font.SysFont("arialblack", 50)
    score_font = pygame.font.SysFont("comicsansms", 25)
    menu_font = pygame.font.SysFont("arial", 30)
except:
    # Fallback to default font if specific fonts not available
    title_font = pygame.font.Font(None, 60)
    score_font = pygame.font.Font(None, 32)
    menu_font = pygame.font.Font(None, 36)

# Sound effects setup
# Sound effects setup
try:
    # Initialize the mixer
    pygame.mixer.init()
    
    # Load sounds from the assets folder
    eat_sound = pygame.mixer.Sound("assets/eat.wav")
    crash_sound = pygame.mixer.Sound("assets/crash.wav")
    
    sounds_loaded = True
    print("Sound effects loaded successfully.")
except Exception as e:
    print(f"Could not load sound effects. Error: {e}")
    sounds_loaded = False

# Game state
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    PAUSED = 3

class Snake:
    def __init__(self, x, y):
        self.head = [x, y]
        self.body = [[x, y]]
        self.direction = "RIGHT"
        self.length = 1
        self.turns = {}  # Store turning points
        self.speed = FPS
        self.score = 0
        self.high_score = self.load_high_score()
        self.ticks_since_last_move = 0
        self.growth_pending = 0  # For smoother growth animation
        
        # Snake size effects
        self.segment_sizes = {}  # Track size of each segment (index: size)
        for i in range(len(self.body)):
            self.segment_sizes[i] = BLOCK_SIZE
            
        self.grow_effect_active = False
        self.grow_effect_timer = 0
        self.grow_effect_duration = 20  # Duration of growth effect in frames
        self.max_grow_size = BLOCK_SIZE * 1.5  # Maximum size during growth
        
        # Create snake head surface with eyes and details
        self.head_surface = self.create_snake_head()
        self.body_surface = self.create_snake_body()
        
        # Create directional head surfaces
        self.head_right = self.head_surface
        self.head_left = pygame.transform.flip(self.head_surface, True, False)
        self.head_up = pygame.transform.rotate(self.head_surface, 90)
        self.head_down = pygame.transform.rotate(self.head_surface, -90)
    
    def create_snake_head(self):
        """Create a detailed snake head surface"""
        surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        
        # Base head shape (slightly rounded rectangle)
        pygame.draw.rect(surface, DARK_GREEN, [0, 0, BLOCK_SIZE, BLOCK_SIZE], border_radius=3)
        
        # Gradient effect
        for i in range(5):
            pygame.draw.rect(
                surface, 
                (0, 180 - i*15, 0), 
                [i, i, BLOCK_SIZE-i*2, BLOCK_SIZE-i*2], 
                border_radius=3
            )
        
        # Eyes
        eye_size = max(3, BLOCK_SIZE // 6)
        pupil_size = max(1, eye_size // 2)
        
        # Right eye
        pygame.draw.circle(surface, WHITE, (BLOCK_SIZE - eye_size*2, BLOCK_SIZE//3), eye_size)
        pygame.draw.circle(surface, BLACK, (BLOCK_SIZE - eye_size*2, BLOCK_SIZE//3), pupil_size)
        
        # Left eye
        pygame.draw.circle(surface, WHITE, (BLOCK_SIZE - eye_size*2, BLOCK_SIZE - BLOCK_SIZE//3), eye_size)
        pygame.draw.circle(surface, BLACK, (BLOCK_SIZE - eye_size*2, BLOCK_SIZE - BLOCK_SIZE//3), pupil_size)
        
        # Tongue (small red line)
        tongue_len = BLOCK_SIZE // 3
        pygame.draw.line(
            surface, 
            RED, 
            (BLOCK_SIZE, BLOCK_SIZE // 2), 
            (BLOCK_SIZE + tongue_len//2, BLOCK_SIZE // 2), 
            2
        )
        
        return surface
    
    def create_snake_body(self):
        """Create a snake body segment surface"""
        surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        
        # Base body shape
        pygame.draw.rect(surface, DARK_GREEN, [0, 0, BLOCK_SIZE, BLOCK_SIZE], border_radius=3)
        
        # Gradient effect
        for i in range(3):
            color = (0, 160 - i*10, 0)
            pygame.draw.rect(
                surface, 
                color, 
                [i+1, i+1, BLOCK_SIZE-i*2-2, BLOCK_SIZE-i*2-2], 
                border_radius=3
            )
        
        # Add scale pattern
        scale_size = BLOCK_SIZE // 4
        for row in range(2):
            for col in range(2):
                x = col * scale_size + scale_size // 2
                y = row * scale_size + scale_size // 2
                pygame.draw.circle(
                    surface, 
                    LIGHT_GREEN, 
                    (x, y), 
                    scale_size // 3
                )
        
        return surface
    
    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except (FileNotFoundError, ValueError):
            return 0
    
    def save_high_score(self):
        with open("highscore.txt", "w") as f:
            f.write(str(self.high_score))
    
    def reset(self, x, y):
        self.head = [x, y]
        self.body = [[x, y]]
        self.direction = "RIGHT"
        self.length = 1
        self.turns = {}
        self.speed = FPS
        self.score = 0
        self.ticks_since_last_move = 0
        self.growth_pending = 0
        self.segment_sizes = {0: BLOCK_SIZE}
        self.grow_effect_active = False
        self.grow_effect_timer = 0
    
    def move(self):
        # Update position based on direction
        x, y = self.head
        
        if self.direction == "RIGHT":
            x += BLOCK_SIZE
        elif self.direction == "LEFT":
            x -= BLOCK_SIZE
        elif self.direction == "UP":
            y -= BLOCK_SIZE
        elif self.direction == "DOWN":
            y += BLOCK_SIZE
        
        # Update head position
        self.head = [x, y]
        
        # Store the current turn for body segments to follow
        self.turns[tuple(self.head)] = self.direction
        
        # Add new head position to body
        self.body.insert(0, [x, y])
        
        # Update segment sizes dictionary for the new head
        new_segment_sizes = {0: self.segment_sizes.get(0, BLOCK_SIZE)}
        for i in range(1, len(self.body)):
            new_segment_sizes[i] = self.segment_sizes.get(i-1, BLOCK_SIZE)
        self.segment_sizes = new_segment_sizes
        
        # Handle growth or remove tail
        if self.growth_pending > 0:
            self.growth_pending -= 1
        else:
            self.body.pop()
            # Adjust segment_sizes when removing tail
            max_idx = max(self.segment_sizes.keys())
            if max_idx >= len(self.body):
                del self.segment_sizes[max_idx]
        
        # Update body segments based on turns
        i = 1
        while i < len(self.body):
            p = tuple(self.body[i])
            if p in self.turns:
                # Body segments follow the turning points
                if i == len(self.body) - 1:
                    # We can remove this turn point once the tail has passed
                    del self.turns[p]
            i += 1
        
        # Update grow effect
        if self.grow_effect_active:
            self.grow_effect_timer -= 1
            if self.grow_effect_timer <= 0:
                self.grow_effect_active = False
    
    def change_direction(self, direction):
        # Prevent 180-degree turns
        if (direction == "RIGHT" and self.direction != "LEFT" or
            direction == "LEFT" and self.direction != "RIGHT" or
            direction == "UP" and self.direction != "DOWN" or
            direction == "DOWN" and self.direction != "UP"):
            self.direction = direction
    
    def check_collision(self):
        # Check for wall collision
        if (self.head[0] < 0 or self.head[0] >= WIDTH or 
            self.head[1] < 0 or self.head[1] >= HEIGHT):
            return True
        
        # Check for self collision (skip head)
        for segment in self.body[1:]:
            if segment == self.head:
                return True
        
        return False
    
    def grow(self):
        self.length += 1
        self.growth_pending += 1
        self.score += 10
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        
        # Increase speed with each growth
        self.speed = min(FPS + (self.length - 1) * ACCELERATION, 30)  # Cap at 30 FPS
        
        # Activate grow effect for the entire snake
        self.grow_effect_active = True
        self.grow_effect_timer = self.grow_effect_duration
    
    def get_segment_size(self, segment_index):
        # Calculate segment size based on grow effect
        base_size = BLOCK_SIZE
        
        if self.grow_effect_active:
            # Calculate growth factor using sine wave for smooth animation
            progress = self.grow_effect_timer / self.grow_effect_duration
            # Higher at the beginning and lower towards the end
            growth_factor = math.sin(progress * math.pi/2)
            
            # Apply growth factor with distance falloff (head grows most)
            distance_factor = max(0, 1 - segment_index * 0.15)
            size_increase = (self.max_grow_size - BLOCK_SIZE) * growth_factor * distance_factor
            return base_size + size_increase
        else:
            return base_size
    
    def draw(self, surface):
        # Draw the snake (from tail to head for proper overlap)
        for i in range(len(self.body)-1, -1, -1):
            x, y = self.body[i]
            
            # Get the appropriate size for this segment
            segment_size = self.get_segment_size(i)
            
            # Choose the appropriate directional image for head
            if i == 0:  # Head
                if self.direction == "RIGHT":
                    segment_img = self.head_right
                elif self.direction == "LEFT":
                    segment_img = self.head_left
                elif self.direction == "UP":
                    segment_img = self.head_up
                else:  # DOWN
                    segment_img = self.head_down
            else:  # Body segments
                segment_img = self.body_surface
            
            # Scale image according to segment size
            scaled_img = pygame.transform.scale(segment_img, (int(segment_size), int(segment_size)))
            
            # Center the segment (adjust position for growth)
            offset_x = (segment_size - BLOCK_SIZE) / 2
            offset_y = (segment_size - BLOCK_SIZE) / 2
            
            surface.blit(scaled_img, (x - offset_x, y - offset_y))
            
            # Add subtle glow effect when growing
            if self.grow_effect_active:
                glow_size = segment_size * 1.2
                glow_surface = pygame.Surface((int(glow_size), int(glow_size)), pygame.SRCALPHA)
                alpha = int(80 * (self.grow_effect_timer / self.grow_effect_duration))
                pygame.draw.circle(
                    glow_surface, 
                    (0, 255, 0, alpha), 
                    (int(glow_size/2), int(glow_size/2)), 
                    int(glow_size/2)
                )
                surface.blit(
                    glow_surface, 
                    (x + BLOCK_SIZE/2 - glow_size/2, y + BLOCK_SIZE/2 - glow_size/2)
                )

class Food:
    def __init__(self):
        self.position = self.randomize_position()
        self.shimmer_offset = 0
        self.shimmer_direction = 1
        
        # Create food surface with details
        self.food_surface = self.create_food()
    
    def create_food(self):
        """Create a detailed food surface"""
        surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        
        # Apple shape (red circle with gradient)
        pygame.draw.circle(surface, (200, 0, 0), (BLOCK_SIZE//2, BLOCK_SIZE//2), BLOCK_SIZE//2)
        
        # Highlight/shine effect
        highlight_radius = BLOCK_SIZE // 4
        pygame.draw.circle(
            surface, 
            (255, 100, 100), 
            (BLOCK_SIZE//3, BLOCK_SIZE//3), 
            highlight_radius
        )
        
        # Stem on top
        stem_w = BLOCK_SIZE // 6
        stem_h = BLOCK_SIZE // 4
        pygame.draw.rect(
            surface, 
            (100, 50, 0), 
            [BLOCK_SIZE//2 - stem_w//2, 0, stem_w, stem_h]
        )
        
        # Leaf next to stem
        leaf_points = [
            (BLOCK_SIZE//2 + stem_w//2, stem_h),
            (BLOCK_SIZE//2 + stem_w//2 + BLOCK_SIZE//4, stem_h - BLOCK_SIZE//6),
            (BLOCK_SIZE//2 + stem_w//2, stem_h - BLOCK_SIZE//8)
        ]
        pygame.draw.polygon(surface, (0, 150, 0), leaf_points)
        
        return surface
    
    def randomize_position(self):
        # Makes sure food doesn't spawn on grid boundaries
        cols = WIDTH // BLOCK_SIZE
        rows = HEIGHT // BLOCK_SIZE
        x = random.randint(0, cols - 1) * BLOCK_SIZE
        y = random.randint(0, rows - 1) * BLOCK_SIZE
        return [x, y]
    
    def reposition(self, snake_body):
        # Prevent food from spawning on snake
        new_pos = self.randomize_position()
        while new_pos in snake_body:
            new_pos = self.randomize_position()
        self.position = new_pos
    
    def update(self):
        # Add shimmer effect
        self.shimmer_offset += 0.2 * self.shimmer_direction
        if abs(self.shimmer_offset) > 3:
            self.shimmer_direction *= -1
    
    def draw(self, surface):
        x, y = self.position
        
        # Apply shimmer/pulsing effect
        scale_factor = 1.0 + math.sin(pygame.time.get_ticks() * 0.005) * 0.1
        scaled_size = int(BLOCK_SIZE * scale_factor)
        scaled_img = pygame.transform.scale(self.food_surface, (scaled_size, scaled_size))
        
        # Center the scaled image
        offset = (scaled_size - BLOCK_SIZE) // 2
        surface.blit(scaled_img, (x - offset, y - offset))
        
        # Add glow effect
        glow_radius = BLOCK_SIZE + self.shimmer_offset
        glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 100, 100, 30), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surface, (x + BLOCK_SIZE//2 - glow_radius, y + BLOCK_SIZE//2 - glow_radius))

class Game:
    def __init__(self):
        self.state = GameState.MENU
        self.snake = Snake(WIDTH // 2, HEIGHT // 2)
        self.food = Food()
        self.clock = pygame.time.Clock()
        self.last_update_time = pygame.time.get_ticks()
        self.particles = []  # For visual effects
        
        # Create grid and background
        self.background = self.create_background()
        self.grid_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.create_grid_background()
    
    def create_background(self):
        """Create a professional looking background with gradient"""
        background = pygame.Surface((WIDTH, HEIGHT))
        
        # Dark gradient from top to bottom
        for y in range(HEIGHT):
            # Calculate gradient color (darker at bottom)
            gradient_value = max(5, 30 - int(y / HEIGHT * 25))
            color = (gradient_value, gradient_value, gradient_value)
            
            # Draw horizontal line with this color
            pygame.draw.line(background, color, (0, y), (WIDTH, y))
            
        return background
    
    def create_grid_background(self):
        # Create subtle grid pattern
        self.grid_surface.fill((0, 0, 0, 0))  # Clear with transparent
        
        # Draw vertical grid lines
        for x in range(0, WIDTH, BLOCK_SIZE):
            alpha = 30  # Base alpha value for grid
            # Every 5th line is brighter
            if x % (BLOCK_SIZE * 5) == 0:
                alpha = 60
            pygame.draw.line(self.grid_surface, (100, 100, 100, alpha), (x, 0), (x, HEIGHT))
        
        # Draw horizontal grid lines
        for y in range(0, HEIGHT, BLOCK_SIZE):
            alpha = 30  # Base alpha value for grid
            # Every 5th line is brighter
            if y % (BLOCK_SIZE * 5) == 0:
                alpha = 60
            pygame.draw.line(self.grid_surface, (100, 100, 100, alpha), (0, y), (WIDTH, y))
    
    def add_particles(self, x, y, color, count=10):
        for _ in range(count):
            particle = {
                'x': x + BLOCK_SIZE//2,
                'y': y + BLOCK_SIZE//2,
                'vel_x': random.uniform(-2, 2),
                'vel_y': random.uniform(-2, 2),
                'radius': random.randint(2, 5),
                'color': color,
                'life': 30
            }
            self.particles.append(particle)
    
    def update_particles(self):
        particles_to_keep = []
        for particle in self.particles:
            # Update position
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            
            # Apply gravity
            particle['vel_y'] += 0.1
            
            # Reduce life
            particle['life'] -= 1
            
            if particle['life'] > 0:
                particles_to_keep.append(particle)
        
        self.particles = particles_to_keep
    
    def draw_particles(self, surface):
        for particle in self.particles:
            alpha = min(255, particle['life'] * 8)
            color = (*particle['color'][:3], alpha)
            pygame.draw.circle(
                surface, 
                color, 
                (int(particle['x']), int(particle['y'])), 
                particle['radius']
            )
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_RIGHT:
                        self.snake.change_direction("RIGHT")
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction("LEFT")
                    elif event.key == pygame.K_UP:
                        self.snake.change_direction("UP")
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction("DOWN")
                    elif event.key == pygame.K_p:
                        self.state = GameState.PAUSED
                
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_q:
                        return False
                
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p or event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_q:
                        self.state = GameState.MENU
        
        return True
    
    def update(self):
        if self.state == GameState.PLAYING:
            # Move the snake based on its current speed
            current_time = pygame.time.get_ticks()
            time_since_last_update = current_time - self.last_update_time
            
            if time_since_last_update > 1000 / self.snake.speed:
                self.snake.move()
                self.last_update_time = current_time
                
                # Check for collisions
                if self.snake.check_collision():
                    if sounds_loaded:
                        crash_sound.play()
                    self.add_particles(self.snake.head[0], self.snake.head[1], RED, 30)
                    self.state = GameState.GAME_OVER
                
                # Check if snake ate food
                if self.snake.head == self.food.position:
                    if sounds_loaded:
                        eat_sound.play()
                    self.snake.grow()
                    self.add_particles(self.food.position[0], self.food.position[1], GOLD, 20)
                    self.food.reposition(self.snake.body)
            
            # Update food animation independent of snake movement
            self.food.update()
            
            # Update particles
            self.update_particles()
    
    def draw(self):
        # Clear screen with background
        screen.blit(self.background, (0, 0))
        
        # Draw grid background
        screen.blit(self.grid_surface, (0, 0))
        
        if self.state == GameState.MENU:
            self.draw_menu()
        
        elif self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            # Draw game elements
            self.food.draw(screen)
            self.snake.draw(screen)
            self.draw_particles(screen)
            self.draw_score()
            
            if self.state == GameState.PAUSED:
                self.draw_pause_screen()
        
        elif self.state == GameState.GAME_OVER:
            # Draw game elements
            self.food.draw(screen)
            self.snake.draw(screen)
            self.draw_particles(screen)
            self.draw_score()
            self.draw_game_over()
        
        pygame.display.update()
    
    def draw_menu(self):
        # Draw title with glow effect
        glow_surface = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        glow_radius = 50 + math.sin(pygame.time.get_ticks() * 0.001) * 5
        pygame.draw.ellipse(
            glow_surface, 
            (0, 100, 0, 50), 
            [WIDTH//2 - glow_radius*2, 10, glow_radius*4, glow_radius*2]
        )
        screen.blit(glow_surface, (0, HEIGHT//4 - 20))
        
        # Title with shadow effect
        title_shadow = title_font.render("ULTRA SNAKE 3D", True, (0, 50, 0))
        title = title_font.render("ULTRA SNAKE 3D", True, GREEN)
        screen.blit(title_shadow, (WIDTH//2 - title.get_width()//2 + 2, HEIGHT//4 + 2))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        
        # Draw high score
        high_score_text = score_font.render(f"High Score: {self.snake.high_score}", True, GOLD)
        screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, HEIGHT//2))
        
        # Draw instructions
        start_text = menu_font.render("Press SPACE to Start", True, WHITE)
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT * 3//4))
        
        # Animating snake on menu screen
        t = pygame.time.get_ticks() / 1000
        for i in range(5):
            x = WIDTH//2 + math.cos(t + i/2) * 100 - BLOCK_SIZE//2
            y = HEIGHT//2 + math.sin(t + i/2) * 50 - BLOCK_SIZE//2
            
            segment_img = self.snake.head_right if i == 0 else self.snake.body_surface
            screen.blit(segment_img, (x, y))
    
    def draw_score(self):
        # Draw score panel with background
        panel_height = 40
        panel_surface = pygame.Surface((WIDTH, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 150))
        
        # Score text with shadow
        score_shadow = score_font.render(f"Score: {self.snake.score}", True, (50, 50, 50))
        score_text = score_font.render(f"Score: {self.snake.score}", True, WHITE)
        
        # High score with shadow
        high_score_shadow = score_font.render(f"High Score: {self.snake.high_score}", True, (100, 100, 0))
        high_score_text = score_font.render(f"High Score: {self.snake.high_score}", True, GOLD)
        
        # Draw panel and text
        screen.blit(panel_surface, (0, 0))
        screen.blit(score_shadow, (12, 7))
        screen.blit(score_text, (10, 5))
        screen.blit(high_score_shadow, (WIDTH - high_score_text.get_width() - 8, 7))
        screen.blit(high_score_text, (WIDTH - high_score_text.get_width() - 10, 5))
    
    def draw_pause_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Pause container
        panel_width, panel_height = 400, 200
        panel_x = WIDTH//2 - panel_width//2
        panel_y = HEIGHT//2 - panel_height//2
        
        # Draw panel with border
        pygame.draw.rect(screen, (40, 40, 40), 
                         [panel_x, panel_y, panel_width, panel_height])
        pygame.draw.rect(screen, GREEN, 
                         [panel_x, panel_y, panel_width, panel_height], 2)
        
        # Pause text with shadow
        pause_shadow = title_font.render("PAUSED", True, (0, 50, 0))
        pause_text = title_font.render("PAUSED", True, GREEN)
        
        screen.blit(pause_shadow, (WIDTH//2 - pause_text.get_width()//2 + 2, panel_y + 20 + 2))
        screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, panel_y + 20))
        
        # Instructions
      # Instructions
        resume_text = menu_font.render("Press SPACE to Resume", True, WHITE)
        screen.blit(resume_text, (WIDTH//2 - resume_text.get_width()//2, panel_y + 80))
        
        quit_text = menu_font.render("Press Q to Main Menu", True, WHITE)
        screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, panel_y + 120))
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Game over container
        panel_width, panel_height = 400, 250
        panel_x = WIDTH//2 - panel_width//2
        panel_y = HEIGHT//2 - panel_height//2
        
        # Draw panel with border
        pygame.draw.rect(screen, (40, 40, 40), 
                         [panel_x, panel_y, panel_width, panel_height])
        pygame.draw.rect(screen, RED, 
                         [panel_x, panel_y, panel_width, panel_height], 2)
        
        # Game over text with shadow
        gameover_shadow = title_font.render("GAME OVER", True, (100, 0, 0))
        gameover_text = title_font.render("GAME OVER", True, RED)
        
        screen.blit(gameover_shadow, (WIDTH//2 - gameover_text.get_width()//2 + 2, panel_y + 20 + 2))
        screen.blit(gameover_text, (WIDTH//2 - gameover_text.get_width()//2, panel_y + 20))
        
        # Score display
        score_text = score_font.render(f"Score: {self.snake.score}", True, WHITE)
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, panel_y + 80))
        
        high_score_text = score_font.render(f"High Score: {self.snake.high_score}", True, GOLD)
        screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, panel_y + 120))
        
        # Instructions
        restart_text = menu_font.render("Press R to Restart", True, WHITE)
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, panel_y + 170))
        
        quit_text = menu_font.render("Press Q to Quit", True, WHITE)
        screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, panel_y + 200))
    
    def reset_game(self):
        self.state = GameState.PLAYING
        self.snake.reset(WIDTH // 2, HEIGHT // 2)
        self.food.reposition(self.snake.body)
        self.particles = []
        self.last_update_time = pygame.time.get_ticks()

def main():
    game = Game()
    running = True
    
    while running:
        game.clock.tick(60)  # Cap framerate at 60 FPS
        
        # Handle events
        running = game.handle_events()
        
        # Update game state
        game.update()
        
        # Draw everything
        game.draw()
    
    pygame.quit()

if __name__ == "__main__":
    main()