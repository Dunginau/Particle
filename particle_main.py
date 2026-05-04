import pygame
import math

# ── SCENE SETUP ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
FPS           = 60
BACKGROUND    = (10, 10, 10)
RADIUS        = 10

# ── PHYSICS CONSTANTS ──────────────────────────────────────────────────────────
K        = 8.99e9   # Coulomb's constant
SOFTENING = 20.0    # minimum distance (px) to avoid division-by-zero
SCALE     = 1e-4    # scales all forces into pixel-space acceleration

# ── PARTICLES ─────────────────────────────────────────────────────────────────
#    Each particle: [x, y, vx, vy, charge, mass]
particles = [
    [480.0, 800.0, 0.0, -70.0,  -1.0, 1.0],
    [420.0, 800.0, 0.0, -70.0,  +1.0, 1.0],
]

# ── PARTICLE TRACES ───────────────────────────────────────────────────────────
MAX_TRACE_LENGTH = 70
traces = [[] for _ in particles]

# ── FIELD ZONES ───────────────────────────────────────────────────────────────
# Zone shapes: "circle"    → cx, cy, r
#              "rectangle" → x, y, w, h   (top-left corner)
#              "polygon"   → points [(x,y), ...]

# Out of the page (Positive Bz)
B_out = [0, 0,  1]

# Into the page (Negative Bz)
B_in  = [0, 0, -1]

electric_zones = [
    {
        "shape"  : "",
        "x": 0, "y": 0, "w": 500, "h": 500,
        "Ex": 5e6, "Ey": 0.0,          # V/m — uniform E field components
    },
]

magnetic_zones = [
    {
        "shape"     : "rectangle",
        "x": 0, "y": 0, "w": WIDTH, "h": 400,
        "B"         : 20000,              # magnitude (T, scaled)
        "direction" : B_in,             # choose B_out or B_in
    },
]

# ── ZONE HELPERS ──────────────────────────────────────────────────────────────
def point_in_circle(x, y, zone):
    dx = x - zone["cx"]
    dy = y - zone["cy"]
    return math.hypot(dx, dy) <= zone["r"]

def point_in_rectangle(x, y, zone):
    return zone["x"] <= x <= zone["x"] + zone["w"] and \
           zone["y"] <= y <= zone["y"] + zone["h"]

def point_in_polygon(x, y, zone):
    """Ray-casting algorithm."""
    pts    = zone["points"]
    n      = len(pts)
    inside = False
    j      = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def point_in_zone(x, y, zone):
    shape = zone["shape"]
    if shape == "circle":
        return point_in_circle(x, y, zone)
    elif shape == "rectangle":
        return point_in_rectangle(x, y, zone)
    elif shape == "polygon":
        return point_in_polygon(x, y, zone)
    return False

# ── COULOMB'S LAW ─────────────────────────────────────────────────────────────
def compute_coulomb_forces(particles):
    """Return list of (fx, fy) net Coulomb force for each particle."""
    n      = len(particles)
    forces = [[0.0, 0.0] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            xi, yi, _, _, qi, _ = particles[i]
            xj, yj, _, _, qj, _ = particles[j]

            dx = xj - xi
            dy = yj - yi
            r  = max(math.hypot(dx, dy), SOFTENING)

            # Coulomb magnitude: F = K * q1 * q2 / r²
            F_mag = K * qi * qj / (r ** 2)

            # Cartesian components via unit vector
            fx = F_mag * (dx / r)
            fy = F_mag * (dy / r)

            # Newton's third law
            forces[i][0] -= fx
            forces[i][1] -= fy
            forces[j][0] += fx
            forces[j][1] += fy

    return forces

# ── ELECTRIC FIELD FORCE ──────────────────────────────────────────────────────
def electric_field_forces(particles):
    """
    F = qE
    E is a uniform vector field (Ex, Ey) active only inside each zone.
    Cartesian components come directly from multiplying q by each E component.
    Returns list of (fx, fy) for each particle.
    """
    forces = [[0.0, 0.0] for _ in particles]

    for i, p in enumerate(particles):
        x, y, _, _, q, _ = p

        for zone in electric_zones:
            if point_in_zone(x, y, zone):
                Ex = zone["Ex"]
                Ey = zone["Ey"]

                # F = qE — Cartesian components directly
                fx = q * Ex
                fy = q * Ey

                forces[i][0] += fx
                forces[i][1] += fy

    return forces

# ── MAGNETIC FIELD FORCE ──────────────────────────────────────────────────────
def magnetic_field_forces(particles):
    """
    F = q(v x B)
    B is along z only: B_out = [0,0,+|B|]  or  B_in = [0,0,-|B|].

    Cross product v x B with v = [vx, vy, 0] and B = [0, 0, Bz]:
        Fx =  q * vy * Bz     (i-component: vy*Bz - 0*0)
        Fy =  q * (-vx * Bz)  (j-component: 0*0 - vx*Bz)
        Fz = 0                 (inherently zero, ignored)

    Returns list of (fx, fy) for each particle.
    """
    forces = [[0.0, 0.0] for _ in particles]

    for i, p in enumerate(particles):
        x, y, vx, vy, q, _ = p

        for zone in magnetic_zones:
            if point_in_zone(x, y, zone):
                Bz = zone["direction"][2] * zone["B"]   # signed magnitude

                # Cross product v x B — Cartesian components
                fx = q * (vy * Bz)
                fy = q * (-vx * Bz)

                forces[i][0] += fx
                forces[i][1] += fy

    print(forces)
    return forces

# ── MOVEMENT ──────────────────────────────────────────────────────────────────
def update_particles(particles, coulomb_forces, electric_forces, magnetic_forces, dt):
    """
    Sum all force contributions per particle into a resultant (fx, fy).
    Euler-integrate velocity then position. Bounce elastically on screen edges.
    """
    for i, p in enumerate(particles):
        x, y, vx, vy, q, m = p

        # Resultant force — sum all x and y contributions
        fx_total = (coulomb_forces[i][0]  * SCALE +
                    electric_forces[i][0] * SCALE +
                    magnetic_forces[i][0] * SCALE)

        fy_total = (coulomb_forces[i][1]  * SCALE +
                    electric_forces[i][1] * SCALE +
                    magnetic_forces[i][1] * SCALE)

        # Acceleration: a = F / m
        ax = fx_total / m
        ay = fy_total / m

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

        # Store trace
        traces[i].append((x, y))
        if len(traces[i]) > MAX_TRACE_LENGTH:
            traces[i].pop(0)

        particles[i] = [x, y, vx, vy, q, m]

# ── DRAW ──────────────────────────────────────────────────────────────────────
def draw_zone(screen, zone, color):
    """Draw a faint tinted region for each field zone."""
    surf  = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shape = zone["shape"]

    if shape == "circle":
        pygame.draw.circle(surf, (*color, 30), (zone["cx"], zone["cy"]), zone["r"])
        pygame.draw.circle(surf, (*color, 80), (zone["cx"], zone["cy"]), zone["r"], 1)

    elif shape == "rectangle":
        rect = pygame.Rect(zone["x"], zone["y"], zone["w"], zone["h"])
        pygame.draw.rect(surf, (*color, 30), rect)
        pygame.draw.rect(surf, (*color, 80), rect, 1)

    elif shape == "polygon":
        pygame.draw.polygon(surf, (*color, 30), zone["points"])
        pygame.draw.polygon(surf, (*color, 80), zone["points"], 1)

    screen.blit(surf, (0, 0))

def draw(screen, particles):
    screen.fill(BACKGROUND)

    for zone in electric_zones:
        draw_zone(screen, zone, (255, 255, 0))    # yellow tint — E field
    for zone in magnetic_zones:
        draw_zone(screen, zone, (0, 200, 255))    # cyan tint  — B field

    # Draw traces
    for i, trail in enumerate(traces):
        if len(trail) > 1:
            color = (220, 60, 60) if particles[i][4] > 0 else (60, 100, 220)
            pygame.draw.lines(screen, color, False, trail, 2)

    for x, y, _, _, q, _ in particles:
        color = (220, 60, 60) if q > 0 else (60, 100, 220)
        pygame.draw.circle(screen, color, (int(x), int(y)), RADIUS)

    pygame.display.flip()

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Coulomb + E & B Field Simulation")
clock  = pygame.time.Clock()

pause = False
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                pause = not pause

    if not pause:
        c_forces = compute_coulomb_forces(particles)
        e_forces = electric_field_forces(particles)
        b_forces = magnetic_field_forces(particles)

        update_particles(particles, c_forces, e_forces, b_forces, dt)

    draw(screen, particles)

pygame.quit()