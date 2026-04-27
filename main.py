from __future__ import annotations

import sys
from pathlib import Path

import pygame

WIDTH, HEIGHT = 960, 540
WORLD_WIDTH = 3200
GROUND_Y = 420
FPS = 60
SCALE = 4
PROJECTILE_SCALE = 2
GROUND_DRAW_OFFSET = 24
GRAVITY = 1800
MOVE_SPEED = 180
RUN_SPEED = 300
JUMP_SPEED = -650
MUMMY_MOVE_SPEED = 130
MUMMY_JUMP_SPEED = -560
MUMMY_ATTACK_RANGE = 290
MUMMY_STOP_RANGE = 140
MUMMY_ATTACK_COOLDOWN = 1.9
MUMMY_JUMP_COOLDOWN = 2.7
PROJECTILE_SPEED = 380
BG_COLOR = (20, 18, 30)
GROUND_COLOR = (60, 50, 80)
TEXT_COLOR = (235, 230, 210)
ENEMY_TEXT_COLOR = (175, 228, 214)

ASSETS = Path(__file__).parent / "assets" / "frames"
BACKGROUND_IMAGE = Path(__file__).parent / "assets" / "egypt_background.png"

PLAYER_ANIMATION_FILES = {
    "crouch": [f"crouch_{i}.png" for i in range(4)],
    "idle": [f"idle_{i}.png" for i in range(4)],
    "walk": [f"walk_{i}.png" for i in range(6)],
    "run": [f"run_{i}.png" for i in range(8)],
    "jump": [f"jump_{i}.png" for i in range(4)],
    "attack": [f"attack_{i}.png" for i in range(6)],
    "hurt": [f"hurt_{i}.png" for i in range(3)],
    "die": [f"die_{i}.png" for i in range(6)],
}

PLAYER_FRAME_DURATIONS = {
    "crouch": 0.16,
    "idle": 0.18,
    "walk": 0.10,
    "run": 0.055,
    "jump": 0.12,
    "attack": 0.07,
    "hurt": 0.12,
    "die": 0.14,
}

PLAYER_LOOPING = {
    "crouch": True,
    "idle": True,
    "walk": True,
    "run": True,
    "jump": False,
    "attack": False,
    "hurt": False,
    "die": False,
}

MUMMY_ANIMATION_FILES = {
    "idle": [f"mummy_idle_{i}.png" for i in range(4)],
    "walk": [f"mummy_walk_{i}.png" for i in range(6)],
    "jump": [f"mummy_jump_{i}.png" for i in range(4)],
    "attack": [f"mummy_attack_{i}.png" for i in range(6)],
    "die": [f"mummy_die_{i}.png" for i in range(6)],
    "burn": [f"mummy_burn_{i}.png" for i in range(6)],
}

MUMMY_FRAME_DURATIONS = {
    "idle": 0.18,
    "walk": 0.11,
    "jump": 0.11,
    "attack": 0.08,
    "die": 0.11,
    "burn": 0.10,
}

MUMMY_LOOPING = {
    "idle": True,
    "walk": True,
    "jump": False,
    "attack": False,
    "die": False,
    "burn": False,
}

PROJECTILE_FILES = [f"tp_{i}.png" for i in range(2)]


def load_scaled_image(path: Path, scale: int) -> pygame.Surface:
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))


def load_animations(file_map: dict[str, list[str]], *, scale: int) -> dict[str, list[pygame.Surface]]:
    animations: dict[str, list[pygame.Surface]] = {}
    for name, files in file_map.items():
        animations[name] = [load_scaled_image(ASSETS / filename, scale) for filename in files]
    return animations


def load_frame_list(files: list[str], *, scale: int) -> list[pygame.Surface]:
    return [load_scaled_image(ASSETS / filename, scale) for filename in files]


def load_background() -> pygame.Surface:
    image = pygame.image.load(BACKGROUND_IMAGE).convert()
    scale = HEIGHT / image.get_height()
    scaled_width = max(WIDTH, round(image.get_width() * scale))
    scaled = pygame.transform.scale(image, (scaled_width, HEIGHT))
    panorama = pygame.Surface((scaled_width * 2, HEIGHT)).convert()
    panorama.blit(scaled, (0, 0))
    panorama.blit(pygame.transform.flip(scaled, True, False), (scaled_width, 0))
    return panorama


def get_camera_x(target_x: float) -> float:
    return max(0.0, min(target_x - WIDTH / 2, WORLD_WIDTH - WIDTH))


class Player:
    def __init__(self, x: int, y: int, animations: dict[str, list[pygame.Surface]]):
        self.animations = animations
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.on_ground = True
        self.state = "idle"
        self.frame_index = 0
        self.frame_timer = 0.0
        self.locked = False
        self.dead = False

    def set_state(self, state: str, *, reset_frame: bool = False):
        if self.state == state and not reset_frame:
            return
        self.state = state
        if reset_frame:
            self.frame_index = 0
            self.frame_timer = 0.0
        else:
            self.frame_index = min(self.frame_index, len(self.animations[state]) - 1)

    def current_frames(self) -> list[pygame.Surface]:
        return self.animations[self.state]

    def current_image(self) -> pygame.Surface:
        frames = self.current_frames()
        self.frame_index = min(self.frame_index, len(frames) - 1)
        image = frames[self.frame_index]
        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)
        return image

    def hitbox(self) -> pygame.Rect:
        rect = self.current_image().get_rect(midbottom=(int(self.x), int(self.y) - GROUND_DRAW_OFFSET))
        return rect.inflate(-rect.width // 3, -rect.height // 5)

    def play_once(self, state: str):
        if self.dead and state != "die":
            return
        self.set_state(state, reset_frame=True)
        self.locked = True
        if state == "die":
            self.dead = True

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper):
        if not self.dead:
            if not self.locked:
                crouching = self.on_ground and (keys[pygame.K_DOWN] or keys[pygame.K_s])
                speed = RUN_SPEED if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else MOVE_SPEED

                moving = False
                self.vx = 0
                if not crouching and (keys[pygame.K_LEFT] or keys[pygame.K_a]):
                    self.vx = -speed
                    self.facing = -1
                    moving = True
                if not crouching and (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                    self.vx = speed
                    self.facing = 1
                    moving = True

                if not crouching and self.on_ground and (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]):
                    self.vy = JUMP_SPEED
                    self.on_ground = False

                if not self.on_ground:
                    self.set_state("jump")
                elif crouching:
                    self.set_state("crouch")
                elif moving and speed == RUN_SPEED:
                    self.set_state("run")
                elif moving:
                    self.set_state("walk")
                else:
                    self.set_state("idle")
            else:
                self.vx = 0

        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(40, min(WORLD_WIDTH - 40, self.x))
        self._animate(dt)

    def _animate(self, dt: float):
        frames = self.current_frames()
        self.frame_timer += dt
        duration = PLAYER_FRAME_DURATIONS[self.state]
        while self.frame_timer >= duration:
            self.frame_timer -= duration
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if PLAYER_LOOPING[self.state]:
                    self.frame_index = 0
                else:
                    self.frame_index = len(frames) - 1
                    self.locked = False
                    if self.state == "jump":
                        self.set_state("idle", reset_frame=True)
                    elif self.state == "attack":
                        self.set_state("idle" if self.on_ground else "jump", reset_frame=True)
                    elif self.state == "hurt":
                        self.set_state("idle" if self.on_ground else "jump", reset_frame=True)
                    elif self.state == "die":
                        self.dead = False
                        self.locked = False
                        self.vx = 0.0
                        self.vy = 0.0
                        self.set_state("idle", reset_frame=True)

    def draw(self, surface: pygame.Surface, camera_x: float):
        image = self.current_image()
        rect = image.get_rect(midbottom=(int(self.x - camera_x), int(self.y) - GROUND_DRAW_OFFSET))
        surface.blit(image, rect)


class ToiletPaperProjectile:
    def __init__(self, x: float, y: float, direction: int, frames: list[pygame.Surface]):
        self.x = x
        self.y = y
        self.vx = PROJECTILE_SPEED * direction
        self.frames = frames
        self.frame_index = 0
        self.frame_timer = 0.0
        self.active = True

    def current_image(self) -> pygame.Surface:
        return self.frames[self.frame_index]

    def rect(self) -> pygame.Rect:
        return self.current_image().get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt: float, player: Player):
        self.x += self.vx * dt
        self.frame_timer += dt
        while self.frame_timer >= 0.08:
            self.frame_timer -= 0.08
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        if self.x < -80 or self.x > WORLD_WIDTH + 80:
            self.active = False
            return

        if self.rect().colliderect(player.hitbox()) and not player.locked and not player.dead:
            player.play_once("hurt")
            self.active = False

    def draw(self, surface: pygame.Surface, camera_x: float):
        rect = self.current_image().get_rect(center=(int(self.x - camera_x), int(self.y)))
        surface.blit(self.current_image(), rect)


class EnemyMummy:
    def __init__(
        self,
        x: int,
        y: int,
        animations: dict[str, list[pygame.Surface]],
        projectile_frames: list[pygame.Surface],
    ):
        self.animations = animations
        self.projectile_frames = projectile_frames
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.respawn()

    def respawn(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.facing = -1
        self.on_ground = True
        self.state = "idle"
        self.frame_index = 0
        self.frame_timer = 0.0
        self.locked = False
        self.dead = False
        self.gone = False
        self.attack_cooldown = 0.8
        self.jump_cooldown = 1.2
        self.projectile_spawned = False

    def set_state(self, state: str, *, reset_frame: bool = False):
        if self.state == state and not reset_frame:
            return
        self.state = state
        if reset_frame:
            self.frame_index = 0
            self.frame_timer = 0.0
        else:
            self.frame_index = min(self.frame_index, len(self.animations[state]) - 1)

    def current_frames(self) -> list[pygame.Surface]:
        return self.animations[self.state]

    def current_image(self) -> pygame.Surface:
        frames = self.current_frames()
        self.frame_index = min(self.frame_index, len(frames) - 1)
        image = frames[self.frame_index]
        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)
        return image

    def kill(self):
        if self.dead or self.gone or self.state in {"die", "burn"}:
            return
        self.dead = True
        self.locked = True
        self.vx = 0.0
        self.vy = 0.0
        self.set_state("die", reset_frame=True)

    def start_attack(self):
        self.locked = True
        self.projectile_spawned = False
        self.attack_cooldown = MUMMY_ATTACK_COOLDOWN
        self.set_state("attack", reset_frame=True)

    def spawn_projectile(self, projectiles: list[ToiletPaperProjectile]):
        direction = 1 if self.facing >= 0 else -1
        launch_x = self.x + direction * 36
        launch_y = self.y - 64
        projectiles.append(ToiletPaperProjectile(launch_x, launch_y, direction, self.projectile_frames))
        self.projectile_spawned = True

    def update(self, dt: float, player: Player, projectiles: list[ToiletPaperProjectile]):
        if self.gone:
            return

        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.jump_cooldown = max(0.0, self.jump_cooldown - dt)

        if not self.dead and not self.locked:
            dx = player.x - self.x
            distance = abs(dx)
            self.facing = 1 if dx >= 0 else -1
            self.vx = 0.0

            if self.on_ground and self.jump_cooldown <= 0 and distance > 320:
                self.vy = MUMMY_JUMP_SPEED
                self.on_ground = False
                self.jump_cooldown = MUMMY_JUMP_COOLDOWN

            if not self.on_ground:
                self.set_state("jump")
            elif self.attack_cooldown <= 0 and MUMMY_STOP_RANGE <= distance <= MUMMY_ATTACK_RANGE:
                self.start_attack()
            elif distance > MUMMY_STOP_RANGE:
                self.vx = MUMMY_MOVE_SPEED * self.facing
                self.set_state("walk")
            else:
                self.set_state("idle")
        else:
            self.vx = 0.0

        if self.state != "burn":
            self.vy += GRAVITY * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(60, min(WORLD_WIDTH - 60, self.x))

        if not self.dead and not self.locked and self.on_ground and self.state == "jump":
            self.set_state("idle", reset_frame=True)

        self._animate(dt, projectiles)

    def _animate(self, dt: float, projectiles: list[ToiletPaperProjectile]):
        frames = self.current_frames()
        self.frame_timer += dt
        duration = MUMMY_FRAME_DURATIONS[self.state]
        while self.frame_timer >= duration:
            self.frame_timer -= duration
            self.frame_index += 1

            if self.state == "attack" and not self.projectile_spawned and self.frame_index >= 3:
                self.spawn_projectile(projectiles)

            if self.state == "jump" and self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1
                break

            if self.frame_index >= len(frames):
                if MUMMY_LOOPING[self.state]:
                    self.frame_index = 0
                else:
                    self.frame_index = len(frames) - 1
                    if self.state == "attack":
                        self.locked = False
                        self.set_state("idle", reset_frame=True)
                    elif self.state == "die":
                        self.set_state("burn", reset_frame=True)
                    elif self.state == "burn":
                        self.gone = True
                        break

    def draw(self, surface: pygame.Surface, camera_x: float):
        if self.gone:
            return
        image = self.current_image()
        rect = image.get_rect(midbottom=(int(self.x - camera_x), int(self.y) - GROUND_DRAW_OFFSET))
        surface.blit(image, rect)


def draw_scene(
    screen: pygame.Surface,
    background: pygame.Surface,
    camera_x: float,
    player: Player,
    enemy: EnemyMummy,
    projectiles: list[ToiletPaperProjectile],
    font: pygame.font.Font,
):
    if background.get_width() <= WIDTH:
        screen.blit(background, (0, 0))
    else:
        max_bg_offset = background.get_width() - WIDTH
        bg_offset = int((camera_x / max(1, WORLD_WIDTH - WIDTH)) * max_bg_offset)
        screen.blit(background, (-bg_offset, 0))

    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    tile_offset = int(camera_x) % 64
    for i in range(-tile_offset, WIDTH + 64, 64):
        pygame.draw.rect(screen, (80, 70, 110), (i, GROUND_Y + 22, 32, 12), border_radius=3)

    title = font.render("Demo Pygame - Sprite animado", True, TEXT_COLOR)
    controls_1 = font.render(
        "Mover: A/D o flechas | Shift: correr | S/abajo: agachar | Espacio: saltar",
        True,
        TEXT_COLOR,
    )
    controls_2 = font.render(
        "J: atacar | H: dano | K: morir | M: matar momia | T: respawn momia | R: reiniciar todo",
        True,
        TEXT_COLOR,
    )
    player_state = font.render(f"Jugador: {player.state}", True, TEXT_COLOR)
    enemy_state = font.render(
        f"Momia: {'consumida' if enemy.gone else enemy.state} | Proyectiles: {len(projectiles)}",
        True,
        ENEMY_TEXT_COLOR,
    )
    world_state = font.render(
        f"Posicion: {int(player.x)} / {WORLD_WIDTH} | Camara: {int(camera_x)}",
        True,
        TEXT_COLOR,
    )

    screen.blit(title, (24, 20))
    screen.blit(controls_1, (24, 52))
    screen.blit(controls_2, (24, 84))
    screen.blit(player_state, (24, 116))
    screen.blit(enemy_state, (24, 148))
    screen.blit(world_state, (24, 180))

    enemy.draw(screen, camera_x)
    player.draw(screen, camera_x)
    for projectile in projectiles:
        projectile.draw(screen, camera_x)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Sprite Demo")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    background = load_background()
    player_animations = load_animations(PLAYER_ANIMATION_FILES, scale=SCALE)
    mummy_animations = load_animations(MUMMY_ANIMATION_FILES, scale=SCALE)
    projectile_frames = load_frame_list(PROJECTILE_FILES, scale=PROJECTILE_SCALE)

    player = Player(240, GROUND_Y, player_animations)
    enemy = EnemyMummy(980, GROUND_Y, mummy_animations, projectile_frames)
    projectiles: list[ToiletPaperProjectile] = []

    while True:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_j and not player.locked and not player.dead:
                    player.play_once("attack")
                if event.key == pygame.K_h and not player.locked and not player.dead:
                    player.play_once("hurt")
                if event.key == pygame.K_k and not player.dead:
                    player.play_once("die")
                if event.key == pygame.K_m:
                    enemy.kill()
                if event.key == pygame.K_t:
                    enemy.respawn()
                    projectiles.clear()
                if event.key == pygame.K_r:
                    player = Player(240, GROUND_Y, player_animations)
                    enemy = EnemyMummy(980, GROUND_Y, mummy_animations, projectile_frames)
                    projectiles.clear()

        keys = pygame.key.get_pressed()
        player.update(dt, keys)
        enemy.update(dt, player, projectiles)

        for projectile in projectiles:
            projectile.update(dt, player)
        projectiles = [projectile for projectile in projectiles if projectile.active]

        camera_x = get_camera_x(player.x)
        draw_scene(screen, background, camera_x, player, enemy, projectiles, font)
        pygame.display.flip()


if __name__ == "__main__":
    main()
