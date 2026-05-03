import pygame
import math

# ── SCENE SETUP ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 500, 800
FPS           = 60
BACKGROUND    = (10, 10, 10)
RADIUS        = 10

# ── PHYSICS CONSTANTS ──────────────────────────────────────────────────────────
K        = 8.99e9   # Coulomb's constant  (scaled below via charge magnitude)
SOFTENING = 20.0    # minimum distance (px) to avoid division-by-zero
SCALE     = 1e-4    # scales raw force into pixel-space acceleration

# ── PARTICLES ─────────────────────────────────────────────────────────────────
#    Each particle: [x, y, vx, vy, charge, mass]
particles = [
    [200.0, 500.0, 80.0, -60.0,  +1.0, 1.0],   # positive (red)
    [700.0, 500.0, -80.0, -60.0,  +1.0, 1.0],   # negative (blue)\
    [200.0, 200.0, 80.0, 70.0,  -1.0, 1.0],   # positive (red)
    [700.0, 200.0, -80.0, 90.0,  -1.0, 1.0],   # negative (blue)
]

# ── COULOMB'S LAW ─────────────────────────────────────────────────────────────
def coulombs_forces(particles):
    """Return a list of (fx, fy) net force for each particle."""
    n      = len(particles)
    forces = [[0.0, 0.0] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            xi, yi, _, _, qi, _ = particles[i]
            xj, yj, _, _, qj, _ = particles[j]

            dx = xj - xi
            dy = yj - yi
            r  = max(math.hypot(dx, dy), SOFTENING)   # softening applied here

            # Coulomb magnitude: F = K * q1 * q2 / r²
            F_mag = K * qi * qj / (r ** 2)

            # Cartesian components (unit vector dx/r, dy/r)
            fx = F_mag * (dx / r)
            fy = F_mag * (dy / r)

            # Newton's third law — equal and opposite
            forces[i][0] -= fx
            forces[i][1] -= fy
            forces[j][0] += fx
            forces[j][1] += fy

    return forces

# ── MOVEMENT ──────────────────────────────────────────────────────────────────
def update_particles(particles, forces, dt):
    """Euler integration: update velocity then position. Bounce on edges."""
    for i, p in enumerate(particles):
        x, y, vx, vy, q, m = p
        fx, fy = forces[i]

        # Acceleration from F = ma  (SCALE brings force into pixel-space)
        ax = (fx * SCALE) / m
        ay = (fy * SCALE) / m

        # Euler step — velocity
        vx += ax * dt
        vy += ay * dt

        # Euler step — position
        x += vx * dt
        y += vy * dt

        # Boundary bounce (elastic)
        if x - RADIUS < 0:
            x  = RADIUS
            vx = abs(vx)
        elif x + RADIUS > WIDTH:
            x  = WIDTH - RADIUS
            vx = -abs(vx)

        if y - RADIUS < 0:
            y  = RADIUS
            vy = abs(vy)
        elif y + RADIUS > HEIGHT:
            y  = HEIGHT - RADIUS
            vy = -abs(vy)

        particles[i] = [x, y, vx, vy, q, m]

# ── DRAW ──────────────────────────────────────────────────────────────────────
def draw(screen, particles):
    screen.fill(BACKGROUND)
    for x, y, _, _, q, _ in particles:
        color = (220, 60, 60) if q > 0 else (60, 100, 220)
        pygame.draw.circle(screen, color, (int(x), int(y)), RADIUS)
    pygame.display.flip()

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Coulomb Simulation")
clock  = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    forces = coulombs_forces(particles)
    update_particles(particles, forces, dt)
    draw(screen, particles)

pygame.quit()
