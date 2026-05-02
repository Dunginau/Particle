import pygame

# 1. THE PARTICLE PROPERTIES
PARTICLE_COLOR = (0, 255, 0) # Green
PARTICLE_RADIUS = 10
m=1.0

# 1.1. Define the particle properties
x, y = 400.0, 300.0  # Start in the middle
vx, vy = 0.0, 70.0 # Initial velocity (pixels per second)
ax, ay = 0.0, 0.0 # Acceleration (pixels per second squared, e.g., gravity)
Fx, Fy = 0.0, 100.0 # Force (not used in this simple example, but can be used to calculate acceleration)

dt = 0.0 # Time step (in seconds)

# 1.2. Scene setup variables
WIDTH, HEIGHT = 800, 600
FPS =  60 # Frames per second (not used directly, but can be used to control dt)

# 2. Setup the environment
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(FPS) / 1000.0 # Increase > 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 3. THE PHYSICS STEP
    # Update position based on velocity and time passed
    ax = Fx / m
    ay = Fy / m
    
    vx += ax*dt
    vy += ay*dt
    
    x += vx * dt
    y += vy * dt

    if x - PARTICLE_RADIUS < 0: # Left wall collision
        x = PARTICLE_RADIUS
        vx *= -1 # Reverse velocity
    if x + PARTICLE_RADIUS > WIDTH: # Right wall collision
        x = WIDTH - PARTICLE_RADIUS
        vx *= -1 # Reverse velocity
    if y - PARTICLE_RADIUS < 0: # Top wall collision
        y = PARTICLE_RADIUS
        vy *= -1 # Reverse velocity
    if y + PARTICLE_RADIUS > HEIGHT: # Bottom wall collision
        y = HEIGHT - PARTICLE_RADIUS
        vy *= -1 # Reverse velocity

    # 4. RENDER SCENE
    screen.fill((30, 30, 30)) # Clear screen with dark grey
    draw_y = HEIGHT - y

    # 4.1. RENDER OBJECTS
    pygame.draw.circle(screen, PARTICLE_COLOR, (int(x), int(draw_y)), PARTICLE_RADIUS) # Draw green particle
    pygame.display.flip() # Update display

pygame.quit()
