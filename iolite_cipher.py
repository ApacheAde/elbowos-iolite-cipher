#!/usr/bin/env python3
"""Iolite Cipher — neon falling-glyph word arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "IOLITE CIPHER"
HANDLE = "x.com/ElbowOS"

VOID = (6, 10, 28)
NAVY = (10, 22, 52)
INK = (16, 32, 68)
IOLITE = (88, 120, 255)
CYAN = (70, 230, 255)
GOLD = (255, 206, 72)
CREAM = (236, 246, 255)
MINT = (110, 255, 190)
ROSE = (255, 92, 140)
AMBER = (255, 160, 70)

COLS = 5
LEFT, RIGHT = 70, W - 70
CATCH_Y = 1580
WORDS = (
    "NEON", "CODE", "FLUX", "ION", "ORBIT", "PRISM", "GLYPH",
    "VAULT", "QUARK", "SPARK", "ELBOW", "REEL", "ARC", "WAVE",
    "BYTE", "NOVA", "PULSE", "GRID", "BEAM", "CORE",
)


def col_x(i: int) -> float:
    return LEFT + (i + 0.5) * (RIGHT - LEFT) / COLS


class Tile:
    def __init__(self, col: int, ch: str, spd: float):
        self.col = col
        self.ch = ch
        self.x = col_x(col)
        self.y = 280.0
        self.spd = spd
        self.spin = random.uniform(0, 6.28)
        self.alive = True
        self.wanted = False


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 78)
        self.font_md = pygame.font.Font(None, 52)
        self.font_sm = pygame.font.Font(None, 36)
        self.font_tile = pygame.font.Font(None, 64)
        self.catch = 2
        self.tiles: list[Tile] = []
        self.sparks: list[list[float]] = []
        self.pops: list[tuple[str, float, float, float]] = []
        self.score = 0
        self.streak = 0
        self.best = 0
        self.words_ok = 0
        self.word = random.choice(WORDS)
        self.idx = 0
        self.spawn_t = 0.2
        self.t = 0.0
        self.flash = 0.0
        self.running = True
        self.screen = None
        if not record:
            self.screen = pygame.display.set_mode((W, H))
            pygame.display.set_caption(TITLE)

    def need(self) -> str:
        return self.word[self.idx]

    def burst(self, x: float, y: float, col: tuple[int, int, int], n: int = 16) -> None:
        for _ in range(n):
            a = random.uniform(0, 6.28)
            self.sparks.append([x, y, math.cos(a) * 360, math.sin(a) * 280, 0.38, *col])

    def next_word(self) -> None:
        nxt = random.choice(WORDS)
        if nxt == self.word:
            nxt = random.choice(WORDS)
        self.word = nxt
        self.idx = 0

    def catch_tile(self, tile: Tile) -> None:
        if tile.ch == self.need():
            self.idx += 1
            self.streak += 1
            self.best = max(self.best, self.streak)
            pts = 80 + self.streak * 12
            self.score += pts
            self.burst(tile.x, CATCH_Y - 20, GOLD, 18)
            self.pops.append((f"+{pts}  {tile.ch}", tile.x, CATCH_Y - 90, 0.7))
            if self.idx >= len(self.word):
                self.words_ok += 1
                bonus = 220 + len(self.word) * 40
                self.score += bonus
                self.pops.append((f"FORGED {self.word}  +{bonus}", W * 0.5, 820, 1.05))
                self.burst(W * 0.5, 900, CYAN, 28)
                self.next_word()
        else:
            self.streak = 0
            self.flash = 0.25
            self.score = max(0, self.score - 20)
            self.burst(tile.x, CATCH_Y - 20, ROSE, 12)
            self.pops.append(("MISS", tile.x, CATCH_Y - 80, 0.55))

    def autoplay(self) -> None:
        want = self.need()
        best = None
        best_y = -1.0
        for tile in self.tiles:
            if tile.ch == want and tile.y > best_y and tile.y < CATCH_Y + 20:
                best, best_y = tile, tile.y
        if best is None:
            for tile in self.tiles:
                if tile.y > best_y:
                    best, best_y = tile, tile.y
        if best is not None:
            if best.col < self.catch:
                self.catch -= 1
            elif best.col > self.catch:
                self.catch += 1

    def spawn(self) -> None:
        want = self.need()
        if random.random() < 0.42:
            ch = want
        else:
            pool = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ch = random.choice(pool)
            if ch == want and random.random() < 0.4:
                ch = random.choice(pool)
        col = random.randrange(COLS)
        if ch == want and random.random() < 0.55:
            col = self.catch if random.random() < 0.45 else random.randrange(COLS)
        spd = 240 + self.t * 9 + random.uniform(-30, 50)
        self.tiles.append(Tile(col, ch, spd))

    def update(self, dt: float) -> None:
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.spawn_t -= dt
        rate = max(0.28, 0.72 - self.t * 0.018)
        if self.spawn_t <= 0:
            self.spawn()
            if random.random() < 0.22:
                self.spawn()
            self.spawn_t = rate
        if self.record:
            self.autoplay()
        for tile in self.tiles:
            tile.y += tile.spd * dt
            tile.spin += dt * 4
            tile.wanted = tile.ch == self.need()
            if tile.y >= CATCH_Y - 18 and abs(tile.col - self.catch) < 0.1:
                tile.alive = False
                self.catch_tile(tile)
            elif tile.y > CATCH_Y + 70:
                tile.alive = False
                if tile.ch == self.need():
                    self.streak = 0
                    self.flash = 0.18
        self.tiles = [t for t in self.tiles if t.alive]
        nxt = []
        for sp in self.sparks:
            sp[0] += sp[2] * dt
            sp[1] += sp[3] * dt
            sp[4] -= dt
            if sp[4] > 0:
                nxt.append(sp)
        self.sparks = nxt
        self.pops = [(a, x, y - 80 * dt, life - dt) for a, x, y, life in self.pops if life - dt > 0]

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        pygame.draw.rect(s, NAVY, (0, 0, LEFT - 6, H))
        pygame.draw.rect(s, NAVY, (RIGHT + 6, 0, W - RIGHT, H))
        pygame.draw.rect(s, IOLITE, (LEFT - 10, 0, 5, H))
        pygame.draw.rect(s, CYAN, (RIGHT + 5, 0, 5, H))
        rng = random.Random(3)
        for i in range(36):
            mx = rng.randint(LEFT, RIGHT)
            my = (rng.randint(0, H) + int(self.t * (14 + i % 16))) % H
            pygame.draw.circle(s, INK, (mx, my), 2 + i % 3)
        cw = (RIGHT - LEFT) / COLS
        for i in range(COLS):
            x0 = int(LEFT + i * cw)
            shade = INK if i % 2 == 0 else NAVY
            pygame.draw.rect(s, shade, (x0 + 8, 300, int(cw) - 16, CATCH_Y - 280), border_radius=22)
            if i == self.catch:
                pygame.draw.rect(s, IOLITE, (x0 + 8, 300, int(cw) - 16, CATCH_Y - 280), 2, border_radius=22)
        built = self.word[: self.idx]
        rest = self.word[self.idx :]
        rail = pygame.Rect(120, 168, W - 240, 92)
        pygame.draw.rect(s, INK, rail, border_radius=18)
        pygame.draw.rect(s, GOLD, rail, 3, border_radius=18)
        label = self.font_md.render(built, True, GOLD)
        need = self.font_md.render(rest, True, CYAN)
        s.blit(label, (rail.x + 28, rail.y + 22))
        s.blit(need, (rail.x + 28 + label.get_width() + 6, rail.y + 22))
        hint = self.font_sm.render("catch the next glyph", True, IOLITE)
        s.blit(hint, hint.get_rect(center=(W // 2, 278)))
        for tile in self.tiles:
            col = GOLD if tile.wanted else (MINT if tile.ch in self.word else CREAM)
            r = 38 + int(3 * math.sin(tile.spin))
            pygame.draw.circle(s, col, (int(tile.x), int(tile.y)), r)
            pygame.draw.circle(s, VOID, (int(tile.x), int(tile.y)), r - 8)
            img = self.font_tile.render(tile.ch, True, col)
            s.blit(img, img.get_rect(center=(int(tile.x), int(tile.y))))
        cx = col_x(self.catch)
        pygame.draw.rect(s, IOLITE, (int(cx - 78), CATCH_Y - 18, 156, 36), border_radius=16)
        pygame.draw.rect(s, CYAN, (int(cx - 62), CATCH_Y - 10, 124, 20), border_radius=10)
        pygame.draw.circle(s, GOLD, (int(cx), CATCH_Y), 10)
        if self.flash > 0:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 40, 80, int(90 * self.flash / 0.25)))
            s.blit(veil, (0, 0))
        for sp in self.sparks:
            pygame.draw.circle(s, (int(sp[5]), int(sp[6]), int(sp[7])), (int(sp[0]), int(sp[1])), 5)
        title = self.font_lg.render(TITLE, True, CYAN)
        s.blit(title, title.get_rect(center=(W // 2, 58)))
        handle = self.font_sm.render(HANDLE, True, GOLD)
        s.blit(handle, handle.get_rect(center=(W // 2, 114)))
        s.blit(self.font_md.render(f"SCORE  {self.score}", True, CREAM), (96, 1760))
        s.blit(self.font_sm.render(f"STREAK {self.streak}   BEST {self.best}   WORDS {self.words_ok}", True, AMBER), (96, 1814))
        for tag, x, y, life in self.pops:
            img = self.font_md.render(tag, True, GOLD)
            s.blit(img, img.get_rect(center=(int(x), int(y))))
        foot = self.font_sm.render("A/D move catcher   SPACE / click same lane", True, (150, 180, 230))
        s.blit(foot, foot.get_rect(center=(W // 2, H - 28)))

    def handle(self, ev) -> None:
        if ev.type == pygame.QUIT:
            self.running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.running = False
            elif ev.key in (pygame.K_a, pygame.K_LEFT):
                self.catch = max(0, self.catch - 1)
            elif ev.key in (pygame.K_d, pygame.K_RIGHT):
                self.catch = min(COLS - 1, self.catch + 1)
            elif ev.key == pygame.K_r:
                rec = self.record
                self.__init__(rec)

    def play(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            self.screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    if record:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record)
    if record:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/IOLITE_CIPHER_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
