import math
import random
import sys
import json
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

try:
    import pygame
except Exception as e:
    print("Требуется pygame: pip install pygame", e)
    raise

# -----------------------------
# Game States & Enums
# -----------------------------
class GameState(Enum):
    MENU = "MENU"
    SETTINGS = "SETTINGS"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    VICTORY = "VICTORY"
    STATS = "STATS"
    TUTORIAL = "TUTORIAL"

class WeaponType(Enum):
    BLASTER = "Blaster"
    SHOTGUN = "Shotgun"
    TRIPLE = "Triple"
    MISSILE = "Missile"
    LASER = "Laser"
    ARC = "Arc"
    GRAVITY = "Gravity"
    ACID = "Acid"
    PLASMA = "Plasma"
    VOID = "Void"

# -----------------------------
# Enhanced SFX System
# -----------------------------
import struct

class SFX:
    def __init__(self):
        self.enabled = False
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except Exception:
            pass

    def init(self):
        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception:
            self.enabled = False

    @staticmethod
    def _make_tone(freq=440.0, ms=120, volume=0.35, wave='sine', attack_ms=5, release_ms=40, stereo=False):
        sample_rate = 44100
        n_samples = int(sample_rate * ms / 1000)
        buf = bytearray()
        two_pi = 2 * math.pi
        attack = int(sample_rate * attack_ms / 1000)
        release = int(sample_rate * release_ms / 1000)
        sustain = max(0, n_samples - attack - release)
        
        for i in range(n_samples):
            t = i / sample_rate
            if wave == 'sine':
                raw = math.sin(two_pi * freq * t)
            elif wave == 'square':
                raw = 1.0 if math.sin(two_pi * freq * t) >= 0 else -1.0
            elif wave == 'triangle':
                raw = 2.0 / math.pi * math.asin(math.sin(two_pi * freq * t))
            elif wave == 'saw':
                raw = 2.0 * (t * freq - math.floor(0.5 + t * freq))
            elif wave == 'noise':
                raw = random.uniform(-1.0, 1.0)
            else:
                raw = math.sin(two_pi * freq * t)
                
            if i < attack:
                env = i / max(1, attack)
            elif i < attack + sustain:
                env = 1.0
            else:
                env = max(0.0, 1.0 - (i - attack - sustain) / max(1, release))
            
            val = int(32767 * volume * env * raw)
            if stereo:
                buf += struct.pack('<hh', val, val)  # Stereo
            else:
                buf += struct.pack('<h', val)  # Mono
        return bytes(buf)

    def build(self):
        if not self.enabled:
            return
        def snd(**kw):
            return pygame.mixer.Sound(buffer=self._make_tone(**kw))
        
        # Enhanced weapon sounds
        self.shoot = snd(freq=720, ms=70, volume=0.25, wave='triangle')
        self.shoot_heavy = snd(freq=480, ms=120, volume=0.3, wave='square')
        self.shoot_laser = snd(freq=1200, ms=200, volume=0.2, wave='sine')
        self.shoot_missile = snd(freq=180, ms=150, volume=0.3, wave='saw')
        
        # Impact sounds
        self.hit = snd(freq=260, ms=60, volume=0.25, wave='sine')
        self.hit_shield = snd(freq=400, ms=80, volume=0.2, wave='triangle')
        self.hit_critical = snd(freq=180, ms=100, volume=0.35, wave='square')
        
        # Explosion and effects
        self.explosion = snd(freq=110, ms=250, volume=0.35, wave='saw', attack_ms=0, release_ms=120)
        self.explosion_large = snd(freq=80, ms=400, volume=0.4, wave='noise', attack_ms=0, release_ms=200)
        self.capture = snd(freq=520, ms=160, volume=0.25, wave='sine')
        self.levelup = snd(freq=880, ms=220, volume=0.25, wave='triangle')
        self.ability = snd(freq=640, ms=140, volume=0.25, wave='square')
        
        # New sounds
        self.powerup = snd(freq=660, ms=180, volume=0.3, wave='triangle')
        self.warning = snd(freq=200, ms=300, volume=0.4, wave='square')
        self.teleport = snd(freq=440, ms=100, volume=0.25, wave='sine')
        self.heal = snd(freq=330, ms=150, volume=0.2, wave='triangle')

    def play(self, sound_name: str):
        if not self.enabled:
            return
        try:
            sound = getattr(self, sound_name, None)
            if sound:
                sound.set_volume(self.sfx_volume * self.master_volume)
                sound.play()
        except Exception:
            pass

sfx = SFX()

# -----------------------------
# Enhanced Config & Constants
# -----------------------------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# Flexible window support
class WindowManager:
    def __init__(self):
        self.base_width = 1280
        self.base_height = 720
        self.min_width = 800
        self.min_height = 600
        self.current_width = SCREEN_W
        self.current_height = SCREEN_H
        self.scale_x = 1.0
        self.scale_y = 1.0
        
    def get_screen_size(self):
        """Get current screen size"""
        return self.current_width, self.current_height
    
    def get_scale_factors(self):
        """Get scale factors for UI scaling"""
        return self.scale_x, self.scale_y
    
    def scale_position(self, x, y):
        """Scale position from base resolution to current"""
        return int(x * self.scale_x), int(y * self.scale_y)
    
    def scale_size(self, width, height):
        """Scale size from base resolution to current"""
        return int(width * self.scale_x), int(height * self.scale_y)
    
    def center_position(self, element_width, element_height):
        """Get centered position for element"""
        return (self.current_width - element_width) // 2, (self.current_height - element_height) // 2
    
    def resize_window(self, width, height):
        """Resize window and update scale factors"""
        self.current_width = max(self.min_width, width)
        self.current_height = max(self.min_height, height)
        self.scale_x = self.current_width / self.base_width
        self.scale_y = self.current_height / self.base_height

ARENA_W, ARENA_H = 8000, 8000  # Увеличенная арена
CAMERA_LERP = 0.12

TEAM_COLORS = [
    (40, 170, 255),   # Синие
    (255, 90, 90),    # Красные
    (80, 220, 140),   # Зелёные
    (180, 120, 255),  # Фиолетовые
    (255, 180, 60),   # Оранжевые
    (255, 100, 200),  # Розовые
]
TEAM_NAMES = ["Синие", "Красные", "Зелёные", "Фиолетовые", "Оранжевые", "Розовые"]

MAX_TEAMS_LIMIT = 6
TEAM_SIZE = 4  # Увеличен размер команды

SPAWN_ZONES = [
    pygame.Rect(300, 300, 600, 600),
    pygame.Rect(ARENA_W - 900, 300, 600, 600),
    pygame.Rect(300, ARENA_H - 900, 600, 600),
    pygame.Rect(ARENA_W - 900, ARENA_H - 900, 600, 600),
    pygame.Rect(ARENA_W//2 - 300, 300, 600, 600),
    pygame.Rect(ARENA_W//2 - 300, ARENA_H - 900, 600, 600),
]
INVULN_TIME = 3.0

# Захват точек
CAPTURE_TIME = 8.0  # Ускорен захват
NUM_POINTS = 6  # Больше точек
POINT_RADIUS = 150

# Объекты-препятствия
NUM_OBSTACLES = 120  # Больше препятствий

# Прогресс и уровни
SPHERE_BASE_REQUIREMENT = 8     # Меньше сфер на уровень
SPHERE_STEP = 1.5               # Медленнее растет
MAX_LEVEL = 100

# Очки за убийство
KILL_SCORE = 100
CAPTURE_SCORE = 50
ASSIST_SCORE = 25

# Новое оружие
WEAPON_TYPES = [
    'Blaster',        # одиночные пули
    'Shotgun',        # веер дроби
    'Triple',         # тройной выстрел
    'Missile',        # самонаводящиеся ракеты
    'Laser',          # импульсный луч
    'Arc',            # электрическая цепная дуга
    'Gravity',        # гравитационный импульс
    'Acid',           # кислотные снаряды
    'Plasma',         # плазменные снаряды (новое)
    'Void',           # пустотные снаряды (новое)
]

# Ограничения прокачек
MAX_UPGRADE_LEVEL = 15  # Увеличено

# Способности
REINFORCE_CD = 20.0  # Уменьшен КД
REINFORCE_LIFETIME = 20.0
QUANTUM_CD = 25.0
TELEPORT_CD = 15.0  # Новая способность
ULTIMATE_CD = 60.0  # Ультимативная способность

# Классовое древо
CLASS_TIERS_LEVELS = [8, 20, 35, 50, 70]  # Больше тиров

# Расширенные узлы древа классов
CLASS_NODES: Dict[str, Dict] = {
    # Tier 1
    'Twin':      {'name': 'Twin',      'tier': 0, 'requires': [],            'mods': {'firerate_mul': 1.12, 'triple_unlock': True}},
    'Sniper':    {'name': 'Sniper',    'tier': 0, 'requires': [],            'mods': {'laser_damage_mul': 1.2, 'laser_len_add': 160, 'speed_mul': 0.92, 'crit_add': 0.05}},
    'Trapper':   {'name': 'Trapper',   'tier': 0, 'requires': [],            'mods': {'gravity_radius_mul': 1.25, 'arc_chain_add': 1, 'speed_mul': 0.95}},
    'Gunner':    {'name': 'Gunner',    'tier': 0, 'requires': [],            'mods': {'firerate_mul': 1.18, 'shotgun_pellets_add': 2}},
    'Hunter':    {'name': 'Hunter',    'tier': 0, 'requires': [],            'mods': {'missile_damage_mul': 1.15, 'acid_dps_mul': 1.2}},
    'Mage':      {'name': 'Mage',      'tier': 0, 'requires': [],            'mods': {'plasma_damage_mul': 1.25, 'void_range_mul': 1.3}},
    
    # Tier 2
    'TripleTwin':{'name': 'Triple Twin','tier': 1, 'requires': ['Twin'],     'mods': {'firerate_mul': 1.10, 'damage_mul': 1.08}},
    'Ranger':    {'name': 'Ranger',    'tier': 1, 'requires': ['Sniper'],   'mods': {'laser_len_add': 220, 'crit_add': 0.04}},
    'MegaTrap':  {'name': 'Mega Trap', 'tier': 1, 'requires': ['Trapper'],  'mods': {'gravity_radius_mul': 1.25, 'gravity_strength_mul': 1.15}},
    'Streamliner':{'name':'Streamliner','tier':1,'requires':['Gunner'],      'mods': {'firerate_mul': 1.20}},
    'Predator':  {'name': 'Predator',  'tier': 1, 'requires': ['Hunter'],   'mods': {'missile_turn_mul': 1.25, 'speed_mul': 1.05}},
    'Warlock':   {'name': 'Warlock',   'tier': 1, 'requires': ['Mage'],     'mods': {'plasma_explosion_mul': 1.3, 'void_damage_mul': 1.2}},
    
    # Tier 3
    'Battleship':{'name': 'Battleship','tier': 2, 'requires': ['TripleTwin'],'mods': {'hp_mul': 1.12, 'shield_mul': 1.12, 'speed_mul': 0.92}},
    'Assassin':  {'name': 'Assassin',  'tier': 2, 'requires': ['Ranger'],   'mods': {'damage_mul': 1.15, 'crit_add': 0.08, 'hp_mul': 0.92}},
    'Overtrapper':{'name':'Overtrapper','tier':2, 'requires':['MegaTrap'],  'mods': {'arc_chain_add': 2, 'arc_range_add': 120}},
    'Skimmer':   {'name': 'Skimmer',   'tier': 2, 'requires': ['Streamliner'],'mods': {'damage_mul': 1.10, 'firerate_mul': 1.08}},
    'Annihilator':{'name':'Annihilator','tier':2,'requires':['Predator'],   'mods': {'missile_damage_mul': 1.25, 'firerate_mul': 0.85}},
    'Archmage':  {'name': 'Archmage',  'tier': 2, 'requires': ['Warlock'],  'mods': {'plasma_damage_mul': 1.2, 'void_radius_mul': 1.4}},
    
    # Tier 4
    'Titan':     {'name': 'Titan',     'tier': 3, 'requires': ['Battleship'],'mods': {'hp_mul': 1.25, 'shield_mul': 1.25, 'damage_mul': 1.1}},
    'Shadow':    {'name': 'Shadow',    'tier': 3, 'requires': ['Assassin'], 'mods': {'speed_mul': 1.15, 'crit_add': 0.12, 'stealth': True}},
    'Overlord':  {'name': 'Overlord',  'tier': 3, 'requires': ['Overtrapper'],'mods': {'gravity_radius_mul': 1.5, 'arc_chain_add': 3}},
    'Destroyer': {'name': 'Destroyer', 'tier': 3, 'requires': ['Skimmer'],  'mods': {'damage_mul': 1.25, 'firerate_mul': 1.15}},
    'Doomsday':  {'name': 'Doomsday',  'tier': 3, 'requires': ['Annihilator'],'mods': {'missile_damage_mul': 1.4, 'missile_count_add': 2}},
    'Elder':     {'name': 'Elder',     'tier': 3, 'requires': ['Archmage'], 'mods': {'plasma_damage_mul': 1.3, 'void_damage_mul': 1.4}},
    
    # Tier 5 (Легендарные)
    'Legend':    {'name': 'Legend',    'tier': 4, 'requires': ['Titan', 'Shadow'],'mods': {'all_stats_mul': 1.2, 'ultimate_unlock': True}},
    'VoidLord':  {'name': 'Void Lord', 'tier': 4, 'requires': ['Overlord', 'Elder'],'mods': {'void_mastery': True, 'gravity_void_synergy': True}},
    'Omega':     {'name': 'Omega',     'tier': 4, 'requires': ['Destroyer', 'Doomsday'],'mods': {'omega_mode': True, 'damage_mul': 1.5}},
}

# -----------------------------
# Enhanced Helpers
# -----------------------------

def clamp(v, a, b):
    return max(a, min(b, v))

def vec_len(x, y):
    return math.hypot(x, y)

def normalize(x, y):
    l = vec_len(x, y)
    if l == 0:
        return 0.0, 0.0
    return x / l, y / l

def lerp(a, b, t):
    return a + (b - a) * t

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# -----------------------------
# Enhanced Camera with Effects
# -----------------------------
class Camera:
    def __init__(self, w, h):
        self.x = 0
        self.y = 0
        self.w = w
        self.h = h
        self.shake_time = 0.0
        self.shake_intensity = 0.0
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.game = None  # Reference to game for window manager

    def set_game_reference(self, game):
        """Set reference to game for accessing window manager"""
        self.game = game

    def get_screen_size(self):
        """Get current screen size from window manager"""
        if self.game and hasattr(self.game, 'window_manager'):
            return self.game.window_manager.get_screen_size()
        return SCREEN_W, SCREEN_H

    def center_on(self, target_x, target_y):
        screen_w, screen_h = self.get_screen_size()
        self.x = clamp(target_x - screen_w // 2, 0, self.w - screen_w)
        self.y = clamp(target_y - screen_h // 2, 0, self.h - screen_h)

    def lerp_to(self, target_x, target_y, amt=CAMERA_LERP):
        screen_w, screen_h = self.get_screen_size()
        cx = clamp(target_x - screen_w // 2, 0, self.w - screen_w)
        cy = clamp(target_y - screen_h // 2, 0, self.h - screen_h)
        self.x += (cx - self.x) * amt
        self.y += (cy - self.y) * amt

    def world_to_screen(self, pos):
        screen_w, screen_h = self.get_screen_size()
        # Apply zoom and shake
        shake_x = random.uniform(-self.shake_intensity, self.shake_intensity) if self.shake_time > 0 else 0
        shake_y = random.uniform(-self.shake_intensity, self.shake_intensity) if self.shake_time > 0 else 0
        
        screen_x = (pos[0] - self.x) * self.zoom + screen_w // 2 * (1 - self.zoom) + shake_x
        screen_y = (pos[1] - self.y) * self.zoom + screen_h // 2 * (1 - self.zoom) + shake_y
        
        return (int(screen_x), int(screen_y))

    def rect_on_screen(self, rect: pygame.Rect):
        screen_w, screen_h = self.get_screen_size()
        return rect.move(-self.x, -self.y).colliderect(pygame.Rect(0, 0, screen_w, screen_h))

    def shake(self, intensity: float, duration: float):
        self.shake_intensity = intensity
        self.shake_time = duration

    def update(self, dt):
        if self.shake_time > 0:
            self.shake_time -= dt
            if self.shake_time <= 0:
                self.shake_intensity = 0.0
        
        # Smooth zoom
        self.zoom += (self.target_zoom - self.zoom) * 0.1

    def set_zoom(self, zoom: float):
        self.target_zoom = clamp(zoom, 0.5, 2.0)

# -----------------------------
# Enhanced Visual Effects
# -----------------------------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: Tuple[int, int, int]
    size: float
    particle_type: str = "normal"
    gravity: float = 0.0
    fade: bool = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt

    def draw(self, surf, cam: Camera):
        if self.life <= 0: return
        px, py = cam.world_to_screen((self.x, self.y))
        alpha = max(0.2, self.life) if self.fade else 1.0
        r = max(1, int(self.size * alpha))
        
        if self.particle_type == "spark":
            # Spark effect
            end_x = px + self.vx * 0.1
            end_y = py + self.vy * 0.1
            pygame.draw.line(surf, self.color, (px, py), (end_x, end_y), 2)
        elif self.particle_type == "ring":
            # Ring effect
            pygame.draw.circle(surf, self.color, (px, py), r, 2)
        else:
            # Normal particle
            pygame.draw.circle(surf, self.color, (px, py), r)

@dataclass
class DamageText:
    x: float
    y: float
    text: str
    life: float
    crit: bool = False
    color: Optional[Tuple[int, int, int]] = None

    def update(self, dt):
        self.y -= 40 * dt
        self.life -= dt

    def draw(self, surf, cam: Camera, font):
        if self.life <= 0: return
        px, py = cam.world_to_screen((self.x, self.y))
        
        if self.color:
            col = self.color
        else:
            col = (255, 230, 90) if self.crit else (240, 240, 240)
        
        # Add glow effect for crits
        if self.crit:
            glow_surf = font.render(self.text, True, (255, 100, 100))
            surf.blit(glow_surf, (px - glow_surf.get_width()//2 + 1, py - glow_surf.get_height()//2 + 1))
        
        label = font.render(self.text, True, col)
        surf.blit(label, (px - label.get_width()//2, py - label.get_height()//2))

@dataclass
class ScreenEffect:
    effect_type: str
    duration: float
    intensity: float
    color: Tuple[int, int, int] = (255, 255, 255)
    
    def update(self, dt):
        self.duration -= dt
        return self.duration > 0

# -----------------------------
# Enhanced Projectiles
# -----------------------------
class Bullet:
    def __init__(self, x, y, dx, dy, team, owner, damage=12, speed=900, life=1.6, color=(255,255,255), 
                 acid=False, crit_chance=0.0, plasma=False, void=False, size=4):
        self.x = x
        self.y = y
        ndx, ndy = normalize(dx, dy)
        self.vx = ndx * speed
        self.vy = ndy * speed
        self.team = team
        self.owner = owner
        self.damage = damage
        self.life = life
        self.color = color
        self.radius = size
        self.acid = acid
        self.plasma = plasma
        self.void = void
        self.crit_chance = crit_chance
        self.trail = []

    def update(self, dt):
        # Add trail effect
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
            
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surf, cam: Camera):
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail)
            trail_color = tuple(int(c * alpha) for c in self.color)
            px, py = cam.world_to_screen((tx, ty))
            pygame.draw.circle(surf, trail_color, (px, py), max(1, int(self.radius * alpha)))
        
        px, py = cam.world_to_screen((self.x, self.y))
        
        if self.plasma:
            # Plasma effect
            pygame.draw.circle(surf, (100, 200, 255), (px, py), self.radius + 2)
            pygame.draw.circle(surf, self.color, (px, py), self.radius)
        elif self.void:
            # Void effect
            pygame.draw.circle(surf, (80, 40, 120), (px, py), self.radius + 3)
            pygame.draw.circle(surf, self.color, (px, py), self.radius)
        else:
            pygame.draw.circle(surf, self.color, (px, py), self.radius)

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)


class HomingMissile:
    def __init__(self, x, y, team, owner, target=None):
        self.x, self.y = x, y
        self.team = team
        self.owner = owner
        self.target = target
        self.speed = 400
        self.turn_rate = 3.2  # rad/s
        self.life = 4.0
        self.damage = 35
        self.color = (250, 210, 120)
        self.vx, self.vy = 1, 0
        self.radius = 6
        self.trail = []
        self.engine_particles = []

    def update(self, dt, ships: List['Ship']):
        self.life -= dt
        
        # Add trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        
        # Engine particles
        if random.random() < 0.3:
            self.engine_particles.append(Particle(
                self.x - self.vx * 10, self.y - self.vy * 10,
                -self.vx * 0.5 + random.uniform(-20, 20),
                -self.vy * 0.5 + random.uniform(-20, 20),
                0.5, (255, 200, 100), 3, "spark"
            ))
        
        if self.target is None or self.target.dead:
            enemies = [s for s in ships if s.team != self.team and not s.dead]
            if enemies:
                self.target = min(enemies, key=lambda e: (e.x - self.x)**2 + (e.y - self.y)**2)
        
        if self.target is not None:
            dx, dy = self.target.x - self.x, self.target.y - self.y
            ndx, ndy = normalize(dx, dy)
            cur = math.atan2(self.vy, self.vx)
            tgt = math.atan2(ndy, ndx)
            diff = (tgt - cur + math.pi) % (2*math.pi) - math.pi
            diff = clamp(diff, -self.turn_rate*dt, self.turn_rate*dt)
            cur += diff
            self.vx, self.vy = math.cos(cur), math.sin(cur)
        
        self.x += self.vx * self.speed * dt
        self.y += self.vy * self.speed * dt

    def draw(self, surf, cam: Camera):
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail)
            trail_color = tuple(int(c * alpha) for c in self.color)
            px, py = cam.world_to_screen((tx, ty))
            pygame.draw.circle(surf, trail_color, (px, py), max(1, int(self.radius * alpha * 0.7)))
        
        px, py = cam.world_to_screen((self.x, self.y))
        pygame.draw.circle(surf, self.color, (px, py), self.radius)
        pygame.draw.circle(surf, (255,255,255), (px, py), self.radius+2, 1)
        
        # Draw engine glow
        engine_x, engine_y = cam.world_to_screen((self.x - self.vx * 8, self.y - self.vy * 8))
        pygame.draw.circle(surf, (255, 150, 50), (engine_x, engine_y), 4)

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)


class LaserBeam:
    def __init__(self, x, y, dx, dy, team, owner, damage=20, length=820, time=0.45, color=(255,255,255)):
        self.x, self.y = x, y
        nx, ny = normalize(dx, dy)
        self.dx, self.dy = nx, ny
        self.team = team
        self.owner = owner
        self.damage = damage
        self.length = length
        self.time = time
        self.color = color
        self.max_time = time
        self.particles = []

    def update(self, dt):
        self.time -= dt
        
        # Generate particles along the beam
        if random.random() < 0.3:
            t = random.random()
            px = self.x + self.dx * self.length * t
            py = self.y + self.dy * self.length * t
            self.particles.append(Particle(
                px, py,
                random.uniform(-30, 30), random.uniform(-30, 30),
                0.3, self.color, 2, "spark"
            ))

    def draw(self, surf, cam: Camera):
        sx, sy = self.x - cam.x, self.y - cam.y
        ex, ey = sx + self.dx * self.length, sy + self.dy * self.length
        
        # Draw glow effect
        alpha = self.time / self.max_time
        glow_color = tuple(int(c * alpha) for c in self.color)
        pygame.draw.line(surf, glow_color, (sx, sy), (ex, ey), 8)
        pygame.draw.line(surf, self.color, (sx, sy), (ex, ey), 4)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surf, cam)

    def segment(self):
        return (self.x, self.y, self.x + self.dx * self.length, self.y + self.dy * self.length)

class PlasmaBall:
    def __init__(self, x, y, dx, dy, team, owner, damage=25, speed=750, life=2.0):
        self.x, self.y = x, y
        ndx, ndy = normalize(dx, dy)
        self.vx = ndx * speed
        self.vy = ndy * speed
        self.team = team
        self.owner = owner
        self.damage = damage
        self.life = life
        self.max_life = life
        self.radius = 8
        self.particles = []
        self.pulse_time = 0.0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.pulse_time += dt * 8
        
        # Generate plasma particles
        if random.random() < 0.4:
            self.particles.append(Particle(
                self.x + random.uniform(-10, 10), self.y + random.uniform(-10, 10),
                random.uniform(-20, 20), random.uniform(-20, 20),
                0.6, (100, 200, 255), 3, "spark"
            ))

    def draw(self, surf, cam: Camera):
        px, py = cam.world_to_screen((self.x, self.y))
        
        # Draw pulse effect
        pulse_size = int(self.radius + math.sin(self.pulse_time) * 3)
        pygame.draw.circle(surf, (150, 220, 255), (px, py), pulse_size + 4)
        pygame.draw.circle(surf, (100, 200, 255), (px, py), pulse_size + 2)
        pygame.draw.circle(surf, (50, 150, 255), (px, py), pulse_size)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surf, cam)

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)

class VoidProjectile:
    def __init__(self, x, y, dx, dy, team, owner, damage=30, speed=650, life=2.5):
        self.x, self.y = x, y
        ndx, ndy = normalize(dx, dy)
        self.vx = ndx * speed
        self.vy = ndy * speed
        self.team = team
        self.owner = owner
        self.damage = damage
        self.life = life
        self.radius = 10
        self.void_time = 0.0
        self.distortion_radius = 0.0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.void_time += dt * 6
        self.distortion_radius = 15 + math.sin(self.void_time) * 5

    def draw(self, surf, cam: Camera):
        px, py = cam.world_to_screen((self.x, self.y))
        
        # Draw void distortion
        pygame.draw.circle(surf, (40, 20, 60), (px, py), int(self.distortion_radius))
        pygame.draw.circle(surf, (80, 40, 120), (px, py), int(self.distortion_radius * 0.7))
        pygame.draw.circle(surf, (120, 60, 180), (px, py), self.radius)
        
        # Draw void core
        core_size = int(self.radius * 0.6)
        pygame.draw.circle(surf, (200, 100, 255), (px, py), core_size)

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)


class ElectricArc:
    def __init__(self, path: List[Tuple[float,float]], damage: float, team: int, owner: 'Ship', time=0.22):
        self.path = path
        self.damage = damage
        self.team = team
        self.owner = owner
        self.time = time

    def update(self, dt):
        self.time -= dt

    def draw(self, surf, cam: Camera):
        for i in range(len(self.path)-1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i+1]
            pygame.draw.line(surf, (180, 230, 255), (x1 - cam.x, y1 - cam.y), (x2 - cam.x, y2 - cam.y), 2)


class GravityPulse:
    def __init__(self, x, y, team, owner, radius=240, strength=900, time=0.45):
        self.x, self.y = x, y
        self.team = team
        self.owner = owner
        self.radius = radius
        self.strength = strength
        self.time = time

    def update(self, dt, ships, bullets):
        self.time -= dt
        for sh in ships:
            if sh.team == self.team or sh.dead:
                continue
            dx, dy = sh.x - self.x, sh.y - self.y
            d = vec_len(dx, dy)
            if d < self.radius and d > 1:
                nx, ny = dx / d, dy / d
                force = self.strength * (1 - d/self.radius)
                sh.vx += nx * force * dt
                sh.vy += ny * force * dt
                sh.damage(1.0 * dt, attacker=self.owner)  # лёгкий урон
        for b in list(bullets):
            if b.team == self.team:
                continue
            dx, dy = b.x - self.x, b.y - self.y
            d = vec_len(dx, dy)
            if d < self.radius and d > 1:
                nx, ny = dx / d, dy / d
                b.vx += nx * self.strength * 0.5 * dt
                b.vy += ny * self.strength * 0.5 * dt

    def draw(self, surf, cam: Camera):
        pygame.draw.circle(surf, (180, 160, 255), (int(self.x - cam.x), int(self.y - cam.y)), int(self.radius), 2)


@dataclass
class TrailSeg:
    x: float
    y: float
    r: float
    life: float
    team: int

    def update(self, dt):
        self.life -= dt

    def draw(self, surf, cam: Camera):
        if self.life <= 0: return
        pygame.draw.circle(surf, (230, 200, 90), (int(self.x - cam.x), int(self.y - cam.y)), int(self.r), 1)


# -----------------------------
# Map entities
# -----------------------------
class Obstacle:
    def __init__(self, shape: str, rect: pygame.Rect, color=(90, 90, 110), spiked=False, kill=False):
        self.shape = shape  # 'rect', 'tri', 'circle'
        self.rect = rect
        self.color = color
        self.spiked = spiked
        self.kill = kill
        if self.shape == 'tri':
            x, y, w, h = rect
            self.tri = [(x, y+h), (x+w//2, y), (x+w, y+h)]

    def draw(self, surf, cam: Camera):
        r = self.rect.move(-cam.x, -cam.y)
        col = self.color
        if self.shape == 'rect':
            pygame.draw.rect(surf, col, r, border_radius=6)
        elif self.shape == 'tri':
            pts = [(px - cam.x, py - cam.y) for (px, py) in self.tri]
            pygame.draw.polygon(surf, col, pts)
        else:
            pygame.draw.circle(surf, col, r.center, r.w // 2)
        if self.spiked:
            cx, cy = r.center
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                l = r.w // 2 + 10
                ex = int(cx + math.cos(rad) * l)
                ey = int(cy + math.sin(rad) * l)
                pygame.draw.line(surf, (230, 200, 40), (cx, cy), (ex, ey), 2)


class Pickup:
    def __init__(self, x, y, value=1, color=(230, 230, 60)):
        self.x, self.y = x, y
        self.value = value
        self.color = color
        self.life = 25.0
        self.radius = 8

    def update(self, dt):
        self.life -= dt

    def draw(self, surf, cam: Camera):
        px, py = cam.world_to_screen((self.x, self.y))
        pygame.draw.circle(surf, self.color, (px, py), self.radius)
        pygame.draw.circle(surf, (255,255,255), (px, py), self.radius+2, 1)

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)


class CapturePoint:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = POINT_RADIUS
        self.owner: Optional[int] = None
        self.progress: Dict[int, float] = {i: 0.0 for i in range(MAX_TEAMS_LIMIT)}

    def update(self, dt, ships: List['Ship']):
        teams_inside = set()
        for sh in ships:
            if sh.dead: continue
            if (sh.x - self.x)**2 + (sh.y - self.y)**2 <= self.radius**2:
                teams_inside.add(sh.team)
        if len(teams_inside) == 1:
            team = list(teams_inside)[0]
            self.progress[team] += dt
            for t in range(MAX_TEAMS_LIMIT):
                if t != team:
                    self.progress[t] = max(0.0, self.progress[t] - dt*0.8)
            if self.progress[team] >= CAPTURE_TIME:
                self.owner = team
                for t in range(MAX_TEAMS_LIMIT):
                    self.progress[t] = 0.0
                if sfx.enabled:
                    try: sfx.capture.play()
                    except Exception: pass
        elif len(teams_inside) == 0:
            for t in range(MAX_TEAMS_LIMIT):
                self.progress[t] = max(0.0, self.progress[t] - dt*0.5)
        else:
            for t in range(MAX_TEAMS_LIMIT):
                self.progress[t] = max(0.0, self.progress[t] - dt*0.2)

    def draw(self, surf, cam: Camera):
        cx, cy = cam.world_to_screen((self.x, self.y))
        base_color = (255, 255, 255) if self.owner is None else TEAM_COLORS[self.owner]
        pygame.draw.circle(surf, (255,255,255), (cx, cy), self.radius+4, 2)
        surf_alpha = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf_alpha, (*base_color, 70), (self.radius, self.radius), self.radius)
        surf.blit(surf_alpha, (cx - self.radius, cy - self.radius))
        for team, prog in self.progress.items():
            if prog <= 0.01: continue
            frac = clamp(prog / CAPTURE_TIME, 0.0, 1.0)
            color = TEAM_COLORS[team]
            steps = int(40 * frac) + 2
            pts = [(cx, cy)]
            for i in range(steps):
                ang = -math.pi/2 + i * (2*math.pi*frac)/(steps-1)
                pts.append((cx + math.cos(ang) * (self.radius-6), cy + math.sin(ang) * (self.radius-6)))
            pygame.draw.polygon(surf, (*color, 110), pts)


# -----------------------------
# Ship
# -----------------------------
class Ship:
    def __init__(self, x, y, team: int, is_player=False, reinforcement=False):
        self.x, self.y = x, y
        self.vx, self.vy = 0.0, 0.0
        self.team = team
        self.is_player = is_player
        self.is_reinforcement = reinforcement
        self.size = 34
        self.max_hp = 100
        self.hp = self.max_hp
        self.max_shield = 60
        self.shield = self.max_shield
        self.shield_regen = 8.0
        self.invuln = INVULN_TIME
        self.dead = False
        self.delete_me = False

        # Combat / weapons
        self.weapon = 0  # индекс в WEAPON_TYPES
        self.weapon_levels: Dict[str, int] = {w: 1 for w in WEAPON_TYPES}
        self.unlocked: Dict[str, bool] = {w: False for w in WEAPON_TYPES}
        self.unlocked['Blaster'] = True
        self.fire_cd = 0.0
        self.base_fire_rate = 4.0

        # Enhanced upgrades
        self.up_speed = 1
        self.up_firerate = 1
        self.up_damage = 1
        self.up_armor = 1
        self.up_trail = 0
        self.up_resource = 0
        self.up_crit = 0
        self.up_reinforce = 0
        self.up_quantum = 0
        self.up_teleport = 0  # Новая способность
        self.up_ultimate = 0  # Ультимативная способность

        # Class system
        self.class_nodes: set = set()
        self.class_points: int = 0
        self.class_tiers_taken: set = set()
        self.class_mods_cache: Dict[str, float] = {}

        # Enhanced Status/Effects
        self.status_acid: List[Tuple[float,float]] = []
        self.status_burn: List[Tuple[float,float]] = []  # Плазма
        self.status_void: List[Tuple[float,float]] = []  # Пустота
        self.status_slow: float = 0.0  # Замедление
        self.status_stun: float = 0.0  # Оглушение
        self.stealth: bool = False  # Скрытность
        self.stealth_timer: float = 0.0

        # Progression
        self.level = 1
        self.upgrade_points = 0
        self.spheres_this_level = 0
        self.total_spheres = 0
        self.score = 0
        self.kills = 0
        self.assists = 0
        self.captures = 0
        self.deaths = 0

        # AI
        self.target: Optional[Ship] = None
        self.aggro = False
        self.aggro_timer = 0.0
        self.goal_point: Optional[CapturePoint] = None
        self.ai_state = "patrol"  # patrol, attack, retreat, capture
        self.ai_timer = 0.0

        # Spawn origin
        self.spawn_rect = None

        # Enhanced Timers
        self.reinforce_cd = 0.0
        self.quantum_cd = 0.0
        self.teleport_cd = 0.0
        self.ultimate_cd = 0.0
        self.reinforce_life = 0.0
        
        # Visual effects
        self.engine_particles = []
        self.damage_flash = 0.0
        self.level_up_flash = 0.0
        self.ability_charge = 0.0
        
        # Performance tracking
        self.last_damage_time = 0.0
        self.damage_dealt = 0
        self.damage_taken = 0

    # ---- Utility ----
    def set_spawn_rect(self, rect: pygame.Rect):
        self.spawn_rect = rect

    def accelerate(self, ax, ay, dt):
        speed_mul = self.get_class('speed_mul', 1.0)
        self.vx += ax * dt * speed_mul
        self.vy += ay * dt * speed_mul
        speed = vec_len(self.vx, self.vy)
        max_speed = 300 + (self.level - 1) * 6
        max_speed *= (1.0 + 0.08 * (self.up_speed - 1))
        max_speed *= speed_mul
        if speed > max_speed:
            k = max_speed / speed
            self.vx *= k
            self.vy *= k

    def get_weapon_level(self, name: str) -> int:
        return clamp(self.weapon_levels.get(name, 1), 1, MAX_UPGRADE_LEVEL)

    def dmg_mult(self) -> float:
        return (1.0 + 0.06 * (self.up_damage - 1)) * self.get_class('damage_mul', 1.0)

    def base_crit_chance(self) -> float:
        return 0.02 + 0.01 * self.up_crit + self.get_class('crit_add', 0.0)

    def resource_mult(self) -> float:
        return (1.0 + 0.1 * self.up_resource)

    # ---- Class system helpers ----
    def grant_class_points_if_needed(self):
        for i, lvl in enumerate(CLASS_TIERS_LEVELS):
            if self.level >= lvl and i not in self.class_tiers_taken:
                self.class_points += 1
                self.class_tiers_taken.add(i)

    def get_class(self, key: str, default: float=0.0) -> float:
        # кешируем вычисления
        if not self.class_mods_cache:
            mods = {
                'speed_mul': 1.0,
                'damage_mul': 1.0,
                'firerate_mul': 1.0,
                'hp_mul': 1.0,
                'shield_mul': 1.0,
                'laser_damage_mul': 1.0,
                'laser_len_add': 0.0,
                'arc_chain_add': 0,
                'arc_range_add': 0.0,
                'gravity_radius_mul': 1.0,
                'gravity_strength_mul': 1.0,
                'missile_damage_mul': 1.0,
                'missile_turn_mul': 1.0,
                'shotgun_pellets_add': 0,
                'acid_dps_mul': 1.0,
                'crit_add': 0.0,
                'triple_unlock': False,
            }
            for nid in self.class_nodes:
                nd = CLASS_NODES.get(nid)
                if not nd: continue
                for k, v in nd['mods'].items():
                    if isinstance(v, (int, float)):
                        if k.endswith('_mul'):
                            mods[k] = mods.get(k, 1.0) * float(v)
                        elif k.endswith('_add'):
                            mods[k] = mods.get(k, 0.0) + float(v)
                        else:
                            mods[k] = v
                    elif isinstance(v, bool):
                        mods[k] = mods.get(k, False) or v
            self.class_mods_cache = mods
        return self.class_mods_cache.get(key, default)

    def add_class_node(self, node_id: str):
        if node_id in self.class_nodes:
            return
        self.class_nodes.add(node_id)
        # invalidate cache
        self.class_mods_cache = {}
        # мгновенные изменения макс. стат
        self.max_hp = int(self.max_hp * self.get_class('hp_mul', 1.0))
        self.max_shield = int(self.max_shield * self.get_class('shield_mul', 1.0))
        self.hp = min(self.hp, self.max_hp)
        self.shield = min(self.shield, self.max_shield)
        # бонус: Twin даёт доступ к Triple
        if self.get_class('triple_unlock', False):
            self.unlocked['Triple'] = True

    # ---- Progression ----
    def need_spheres(self) -> int:
        return SPHERE_BASE_REQUIREMENT + SPHERE_STEP * (self.level - 1)

    def try_level_up(self):
        # чисто по сферам
        leveled = False
        while self.level < MAX_LEVEL and self.spheres_this_level >= self.need_spheres():
            self.spheres_this_level -= self.need_spheres()
            self.level += 1
            self.upgrade_points += 1
            leveled = True
            self.grant_class_points_if_needed()
            if sfx.enabled:
                try: sfx.levelup.play()
                except Exception: pass
        if leveled:
            # сброс кеша классов (на случай порогов)
            self.class_mods_cache = {}

    def award_kill(self):
        self.score += KILL_SCORE

    def award_spheres(self, n: int):
        gain = int(n * self.resource_mult())
        self.spheres_this_level += gain
        self.total_spheres += gain
        self.try_level_up()

    # ---- Combat ----
    def damage(self, amount, attacker: Optional['Ship']=None, ignore_invuln=False, crit=False, damage_type="normal"):
        if self.dead:
            return
        if self.invuln > 0 and not ignore_invuln:
            return
        
        # Damage tracking
        self.damage_taken += amount
        self.last_damage_time = time.time()
        
        # Visual feedback
        self.damage_flash = 0.3
        
        # Camera shake for player
        if self.is_player and amount > 15:
            Game.instance.camera.shake(amount * 0.5, 0.2)
        
        rem = amount
        if self.shield > 0:
            absorbed = min(self.shield, rem)
            self.shield -= absorbed
            rem -= absorbed
            if absorbed > 0:
                sfx.play("hit_shield")
        
        if rem > 0:
            self.hp -= rem
            if crit:
                sfx.play("hit_critical")
            else:
                sfx.play("hit")
        
        # Damage text with color coding
        color = None
        if damage_type == "plasma":
            color = (100, 200, 255)
        elif damage_type == "void":
            color = (200, 100, 255)
        elif damage_type == "acid":
            color = (120, 255, 140)
        
        Game.instance.dmgtexts.append(DamageText(self.x, self.y - 20, f"{int(amount)}", 0.5, crit=crit, color=color))
        
        if self.hp <= 0:
            self.die(attacker)

    def add_acid(self, dps: float, dur: float):
        dps *= self.get_class('acid_dps_mul', 1.0)
        self.status_acid.append((dur, dps))

    def die(self, attacker: Optional['Ship']):
        if self.dead: return
        self.dead = True
        for _ in range(40):
            ang = random.random() * 2*math.pi
            sp = random.uniform(80, 320)
            vx, vy = math.cos(ang)*sp, math.sin(ang)*sp
            Game.instance.particles.append(Particle(self.x, self.y, vx, vy, 0.8, TEAM_COLORS[self.team], 3))
        # подкрепления не дропают
        if not self.is_reinforcement:
            drop = max(1, self.level // 3)
            for _ in range(drop):
                ox = random.uniform(-20, 20)
                oy = random.uniform(-20, 20)
                Game.instance.pickups.append(Pickup(self.x + ox, self.y + oy, value=1))
        if attacker is not None:
            attacker.award_kill()
        if self.is_reinforcement:
            self.delete_me = True
        if sfx.enabled:
            try: sfx.explosion.play()
            except Exception: pass

    def respawn(self):
        self.dead = False
        self.hp = self.max_hp
        self.shield = self.max_shield
        self.invuln = INVULN_TIME
        def safe_pos(rect: pygame.Rect):
            for _ in range(20):
                x = random.uniform(rect.left+40, rect.right-40)
                y = random.uniform(rect.top+40, rect.bottom-40)
                ok = True
                for ob in Game.instance.obstacles:
                    if ob.kill or ob.spiked:
                        cx, cy = ob.rect.center
                        if (x - cx)**2 + (y - cy)**2 < (ob.rect.w//2 + self.size*0.7)**2:
                            ok = False; break
                    elif ob.shape in ('rect','tri') and pygame.Rect(int(x - self.size*0.5), int(y - self.size*0.5), int(self.size), int(self.size)).colliderect(ob.rect):
                        ok = False; break
                if ok:
                    return x, y
            return random.uniform(rect.left+40, rect.right-40), random.uniform(rect.top+40, rect.bottom-40)
        if self.spawn_rect:
            self.x, self.y = safe_pos(self.spawn_rect)
        else:
            self.x, self.y = random.uniform(100, ARENA_W-100), random.uniform(100, ARENA_H-100)
        self.vx = self.vy = 0

    def update(self, dt, game: 'Game'):
        if self.dead:
            return
        
        # Update timers
        if self.invuln > 0: self.invuln -= dt
        if self.fire_cd > 0: self.fire_cd -= dt
        if self.reinforce_cd > 0: self.reinforce_cd -= dt
        if self.quantum_cd > 0: self.quantum_cd -= dt
        if self.teleport_cd > 0: self.teleport_cd -= dt
        if self.ultimate_cd > 0: self.ultimate_cd -= dt
        
        # Update visual effects
        if self.damage_flash > 0: self.damage_flash -= dt
        if self.level_up_flash > 0: self.level_up_flash -= dt
        if self.ability_charge > 0: self.ability_charge -= dt
        
        # Status effects
        self._update_status_effects(dt)
        
        # Shield regen
        if self.invuln <= 0:
            self.shield = clamp(self.shield + self.shield_regen * dt, 0, self.max_shield)
        
        # Movement with status effects
        speed_mult = 1.0
        if self.status_slow > 0:
            speed_mult *= 0.6
            self.status_slow -= dt
        
        if self.status_stun > 0:
            speed_mult *= 0.0
            self.status_stun -= dt
        
        # Apply movement
        self.x += self.vx * dt * speed_mult
        self.y += self.vy * dt * speed_mult
        self.x = clamp(self.x, 0, ARENA_W)
        self.y = clamp(self.y, 0, ARENA_H)
        self.vx *= 0.98
        self.vy *= 0.98
        
        # Reinforcement life
        if self.is_reinforcement:
            self.reinforce_life -= dt
            if self.reinforce_life <= 0:
                self.die(attacker=None)
        
        # Stealth system
        if self.stealth:
            self.stealth_timer -= dt
            if self.stealth_timer <= 0:
                self.stealth = False
        
        # AI
        if not self.is_player:
            self.ai_update(dt, game)
        
        # Visual effects
        self._update_visual_effects(dt, game)
        
        # Engine particles
        if random.random() < 0.3:
            self.engine_particles.append(Particle(
                self.x - self.vx * 0.1, self.y - self.vy * 0.1,
                -self.vx * 0.3 + random.uniform(-10, 10),
                -self.vy * 0.3 + random.uniform(-10, 10),
                0.4, TEAM_COLORS[self.team], 2, "spark"
            ))

    def _update_status_effects(self, dt):
        # Acid DoT
        new_status = []
        for t, dps in self.status_acid:
            self.hp -= dps * dt
            new_status.append((t - dt, dps))
        self.status_acid = [(t,d) for (t,d) in new_status if t > 0 and self.hp > 0]
        
        # Plasma burn
        new_burn = []
        for t, dps in self.status_burn:
            self.hp -= dps * dt
            new_burn.append((t - dt, dps))
        self.status_burn = [(t,d) for (t,d) in new_burn if t > 0 and self.hp > 0]
        
        # Void corruption
        new_void = []
        for t, dps in self.status_void:
            self.hp -= dps * dt
            self.shield = max(0, self.shield - dps * 0.5 * dt)
            new_void.append((t - dt, dps))
        self.status_void = [(t,d) for (t,d) in new_void if t > 0 and self.hp > 0]
        
        if self.hp <= 0:
            self.die(attacker=None)

    def _update_visual_effects(self, dt, game):
        # Energy trail
        if self.up_trail > 0 and (random.random() < 0.9):
            game.trails.append(TrailSeg(
                self.x, self.y, 
                r=6 + 2*self.up_trail, 
                life=0.35 + 0.03*self.up_trail, 
                team=self.team
            ))
        
        # Update engine particles
        for particle in list(self.engine_particles):
            particle.update(dt)
            if particle.life <= 0:
                self.engine_particles.remove(particle)

    # ---- Shooting ----
    def shoot(self, tx, ty):
        if self.dead: return []
        out = []
        level_mult = 1.0 + 0.05 * (self.up_firerate - 1)
        level_mult *= self.get_class('firerate_mul', 1.0)
        dmg_mult = self.dmg_mult()
        min_cd = 0.08
        name = WEAPON_TYPES[self.weapon]
        if not self.unlocked.get(name, False):
            return out
        if name == 'Blaster':
            rate = self.base_fire_rate * level_mult
            cd = max(min_cd, 1.0 / rate)
            if self.fire_cd <= 0:
                dx, dy = tx - self.x, ty - self.y
                dmg = (12 + 2*(self.get_weapon_level('Blaster')-1)) * dmg_mult
                out.append(Bullet(self.x, self.y, dx, dy, self.team, self, damage=dmg, speed=950, color=TEAM_COLORS[self.team], crit_chance=self.base_crit_chance()))
                self.fire_cd = cd
        elif name == 'Shotgun':
            rate = 1.6 + 0.1*(self.get_weapon_level('Shotgun')-1)
            rate *= level_mult
            cd = max(min_cd, 1.0 / rate)
            if self.fire_cd <= 0:
                pellets = 6 + self.get_weapon_level('Shotgun') + int(self.get_class('shotgun_pellets_add', 0))
                for _ in range(pellets):
                    spread = random.uniform(-0.28, 0.28)
                    ang = math.atan2(ty - self.y, tx - self.x) + spread
                    dx, dy = math.cos(ang), math.sin(ang)
                    out.append(Bullet(self.x, self.y, dx, dy, self.team, self, damage=7*dmg_mult, speed=820, life=0.7, color=TEAM_COLORS[self.team], crit_chance=self.base_crit_chance()))
                self.fire_cd = cd
        elif name == 'Triple':
            rate = 3.0 * level_mult
            cd = max(min_cd, 1.0 / rate)
            if self.fire_cd <= 0:
                base = math.atan2(ty - self.y, tx - self.x)
                for off in (-0.12, 0, 0.12):
                    ang = base + off
                    dx, dy = math.cos(ang), math.sin(ang)
                    out.append(Bullet(self.x, self.y, dx, dy, self.team, self, damage=10*dmg_mult, speed=900, color=TEAM_COLORS[self.team], crit_chance=self.base_crit_chance()))
                self.fire_cd = cd
        elif name == 'Missile':
            rate = 1.2 * (1.0 + 0.05*(self.get_weapon_level('Missile')-1)) * level_mult
            cd = max(0.25, 1.0 / rate)
            if self.fire_cd <= 0:
                m = HomingMissile(self.x, self.y, self.team, self)
                # классовые бонусы
                m.damage = int(m.damage * self.get_class('missile_damage_mul', 1.0))
                m.turn_rate *= self.get_class('missile_turn_mul', 1.0)
                out.append(m)
                self.fire_cd = cd
        elif name == 'Laser':
            base_cd = 4.0
            cd = max(2.5, base_cd * (1.0 - 0.03*(self.up_firerate-1)))
            if self.fire_cd <= 0:
                dx, dy = tx - self.x, ty - self.y
                dmg = (16 + 2*(self.get_weapon_level('Laser')-1)) * dmg_mult * self.get_class('laser_damage_mul', 1.0)
                length = 820 + 20*(self.get_weapon_level('Laser')-1) + self.get_class('laser_len_add', 0.0)
                out.append(LaserBeam(self.x, self.y, dx, dy, self.team, self, damage=dmg, length=length, color=TEAM_COLORS[self.team]))
                self.fire_cd = cd
        elif name == 'Arc':
            rate = 2.2 * level_mult
            cd = max(0.18, 1.0 / rate)
            if self.fire_cd <= 0:
                lvl = self.get_weapon_level('Arc')
                chain = 2 + lvl + int(self.get_class('arc_chain_add', 0))
                base_rng = 420 + 25 * lvl + self.get_class('arc_range_add', 0.0)
                dmg = (16 + 2 * lvl) * dmg_mult
                enemies = [s for s in Game.instance.ships if s.team != self.team and not s.dead]
                if enemies:
                    if self.is_player:
                        cand = [(e, (e.x - tx)**2 + (e.y - ty)**2) for e in enemies]
                    else:
                        cand = [(e, (e.x - self.x)**2 + (e.y - self.y)**2) for e in enemies]
                    cand = [c for c in cand if c[1] <= base_rng * base_rng]
                    if cand:
                        first, _ = min(cand, key=lambda t: t[1])
                        path = [(self.x, self.y), (first.x, first.y)]
                        first.damage(dmg, attacker=self)
                        used = {first}
                        curx, cury = first.x, first.y
                        for _ in range(chain - 1):
                            nexts = [(e, (e.x - curx)**2 + (e.y - cury)**2) for e in enemies if e not in used]
                            nexts = [c for c in nexts if c[1] <= base_rng * base_rng]
                            if not nexts:
                                break
                            nxt, _ = min(nexts, key=lambda t: t[1])
                            path.append((nxt.x, nxt.y))
                            nxt.damage(dmg, attacker=self)
                            used.add(nxt)
                            curx, cury = nxt.x, nxt.y
                        if len(path) >= 2:
                            Game.instance.arcs.append(ElectricArc(path, dmg, self.team, self))
                            if sfx.enabled:
                                try: sfx.ability.play()
                                except Exception: pass
                            self.fire_cd = cd
        elif name == 'Gravity':
            rate = 1.6 * level_mult
            cd = max(0.4, 1.0 / rate)
            if self.fire_cd <= 0:
                radius = 240 * self.get_class('gravity_radius_mul', 1.0)
                pulse = GravityPulse(self.x, self.y, self.team, self, radius=radius, strength=900 * self.get_class('gravity_strength_mul',1.0))
                Game.instance.pulses.append(pulse)
                self.fire_cd = cd
        elif name == 'Acid':
            rate = 3.2 * level_mult
            cd = max(min_cd, 1.0 / rate)
            if self.fire_cd <= 0:
                dx, dy = tx - self.x, ty - self.y
                out.append(Bullet(self.x, self.y, dx, dy, self.team, self, damage=8*dmg_mult, speed=880, color=(120, 255, 140), acid=True, crit_chance=self.base_crit_chance()))
                self.fire_cd = cd
        elif name == 'Plasma':
            rate = 2.8 * level_mult
            cd = max(min_cd, 1.0 / rate)
            if self.fire_cd <= 0:
                dx, dy = tx - self.x, ty - self.y
                dmg = (18 + 2*(self.get_weapon_level('Plasma')-1)) * dmg_mult * self.get_class('plasma_damage_mul', 1.0)
                plasma = PlasmaBall(self.x, self.y, dx, dy, self.team, self, damage=dmg)
                Game.instance.plasma_balls.append(plasma)
                self.fire_cd = cd
        elif name == 'Void':
            rate = 2.0 * level_mult
            cd = max(0.3, 1.0 / rate)
            if self.fire_cd <= 0:
                dx, dy = tx - self.x, ty - self.y
                dmg = (25 + 3*(self.get_weapon_level('Void')-1)) * dmg_mult * self.get_class('void_damage_mul', 1.0)
                void = VoidProjectile(self.x, self.y, dx, dy, self.team, self, damage=dmg)
                Game.instance.void_projectiles.append(void)
                self.fire_cd = cd
        
        if out or any(name in ['Plasma', 'Void'] for name in [WEAPON_TYPES[self.weapon]]):
            if WEAPON_TYPES[self.weapon] == 'Laser':
                sfx.play("shoot_laser")
            elif WEAPON_TYPES[self.weapon] == 'Missile':
                sfx.play("shoot_missile")
            elif WEAPON_TYPES[self.weapon] in ['Plasma', 'Void']:
                sfx.play("shoot_heavy")
            else:
                sfx.play("shoot")
        
        return out

    # ---- Abilities ----
    def can_reinforce(self) -> bool:
        return self.reinforce_cd <= 0

    def can_quantum(self) -> bool:
        return self.quantum_cd <= 0

    def can_teleport(self) -> bool:
        return self.teleport_cd <= 0

    def can_ultimate(self) -> bool:
        return self.ultimate_cd <= 0 and self.get_class('ultimate_unlock', False)

    def use_reinforce(self):
        if not self.can_reinforce():
            return
        ally = Ship(self.x + 40, self.y + 40, self.team, is_player=False, reinforcement=True)
        ally.reinforce_life = REINFORCE_LIFETIME * (1.0 + 0.08*self.up_reinforce)
        ally.set_spawn_rect(self.spawn_rect)
        ally.unlocked['Blaster'] = True
        ally.weapon = 0
        Game.instance.ships.append(ally)
        self.reinforce_cd = max(4.0, REINFORCE_CD * (1.0 - 0.05*self.up_reinforce))
        sfx.play("ability")

    def use_quantum(self):
        if not self.can_quantum():
            return
        roll = random.random()
        if roll < 0.33:
            self.hp = clamp(self.hp + 40 + 6*self.up_quantum, 0, self.max_hp)
            sfx.play("heal")
        elif roll < 0.66:
            self.shield = clamp(self.shield + 40 + 6*self.up_quantum, 0, self.max_shield)
            sfx.play("powerup")
        else:
            self.invuln = max(self.invuln, 1.0 + 0.2*self.up_quantum)
            sfx.play("ability")
        self.quantum_cd = max(4.0, QUANTUM_CD * (1.0 - 0.05*self.up_quantum))

    def use_teleport(self, target_x: float, target_y: float):
        if not self.can_teleport():
            return
        
        # Check if target position is valid
        if target_x < 50 or target_x > ARENA_W - 50 or target_y < 50 or target_y > ARENA_H - 50:
            return
        
        # Create teleport effect
        for _ in range(20):
            Game.instance.particles.append(Particle(
                self.x, self.y,
                random.uniform(-100, 100), random.uniform(-100, 100),
                0.5, TEAM_COLORS[self.team], 4, "spark"
            ))
        
        # Teleport
        self.x, self.y = target_x, target_y
        self.vx = self.vy = 0
        
        # Create arrival effect
        for _ in range(20):
            Game.instance.particles.append(Particle(
                self.x, self.y,
                random.uniform(-100, 100), random.uniform(-100, 100),
                0.5, TEAM_COLORS[self.team], 4, "spark"
            ))
        
        self.teleport_cd = max(3.0, TELEPORT_CD * (1.0 - 0.05*self.up_teleport))
        sfx.play("teleport")

    def use_ultimate(self):
        if not self.can_ultimate():
            return
        
        # Different ultimates based on class
        if 'Legend' in self.class_nodes:
            # Legend ultimate: Massive damage burst
            for _ in range(8):
                ang = random.uniform(0, 2*math.pi)
                dx, dy = math.cos(ang), math.sin(ang)
                Game.instance.bullets.append(Bullet(
                    self.x, self.y, dx, dy, self.team, self,
                    damage=50, speed=1200, life=2.0, color=(255, 255, 100), size=8
                ))
        
        elif 'VoidLord' in self.class_nodes:
            # Void Lord ultimate: Void explosion
            for sh in Game.instance.ships:
                if sh.team != self.team and not sh.dead:
                    dist = distance((self.x, self.y), (sh.x, sh.y))
                    if dist < 400:
                        sh.damage(30, attacker=self)
                        sh.status_void.append((3.0, 8.0))
        
        elif 'Omega' in self.class_nodes:
            # Omega ultimate: Time slow
            for sh in Game.instance.ships:
                if sh.team != self.team and not sh.dead:
                    dist = distance((self.x, self.y), (sh.x, sh.y))
                    if dist < 500:
                        sh.status_slow = max(sh.status_slow, 5.0)
        
        self.ultimate_cd = ULTIMATE_CD
        sfx.play("explosion_large")

    # ---- AI ----
    def ai_update(self, dt, game: 'Game'):
        cam = game.camera
        my_rect = pygame.Rect(self.x-20, self.y-20, 40, 40)
        on_screen = cam.rect_on_screen(my_rect)
        if on_screen and not self.aggro:
            self.aggro = True
            self.aggro_timer = random.uniform(2.0, 4.0)
        # Точки
        needy = [cp for cp in game.capture_points if (cp.owner is None or cp.owner != self.team)]
        self.goal_point = min(needy, key=lambda cp: (cp.x - self.x)**2 + (cp.y - self.y)**2) if needy else None
        ax = ay = 0.0
        if self.goal_point is not None:
            dx, dy = self.goal_point.x - self.x, self.goal_point.y - self.y
            ndx, ndy = normalize(dx, dy)
            ax += ndx * 420; ay += ndy * 420
        enemies = [s for s in game.ships if s.team != self.team and not s.dead]
        if enemies:
            nearest = min(enemies, key=lambda e: (e.x-self.x)**2 + (e.y-self.y)**2)
            d2 = (nearest.x-self.x)**2 + (nearest.y-self.y)**2
            if d2 < (700*700):
                self.target = nearest
        if self.target is not None and not self.target.dead:
            dx, dy = self.target.x - self.x, self.target.y - self.y
            ndx, ndy = normalize(dx, dy)
            ax += ndx * 120; ay += ndy * 120
            if random.random() < 0.9:
                game.spawn_projectiles(self.shoot(self.target.x, self.target.y))
        self.accelerate(ax, ay, dt)
        # Классовые поинты тратим иногда
        self.grant_class_points_if_needed()
        if self.class_points > 0:
            # выберем случайный доступный узел из текущего тира
            avail = game.available_class_nodes(self)
            if avail:
                nid = random.choice(avail)
                self.add_class_node(nid)
                self.class_points -= 1
        # Смена оружия — среди открытых
        if random.random() < 0.0025:
            unlocked = [i for i,w in enumerate(WEAPON_TYPES) if self.unlocked.get(w, False)]
            if unlocked:
                self.weapon = random.choice(unlocked)
        # Бот иногда получает и тратит апгрейды
        if random.random() < 0.003 and self.upgrade_points < 6:
            self.upgrade_points += 1
            game.apply_random_upgrade(self)

    # ---- Draw ----
    def draw(self, surf, cam: Camera):
        px, py = cam.world_to_screen((self.x, self.y))
        
        # Stealth effect
        if self.stealth:
            alpha = 0.3 + 0.4 * math.sin(time.time() * 8)
            col = tuple(int(c * alpha) for c in TEAM_COLORS[self.team])
        else:
            col = TEAM_COLORS[self.team]
        
        # Damage flash effect
        if self.damage_flash > 0:
            flash_intensity = self.damage_flash / 0.3
            col = tuple(int(c + (255 - c) * flash_intensity * 0.5) for c in col)
        
        # Level up flash
        if self.level_up_flash > 0:
            flash_intensity = self.level_up_flash / 0.5
            col = tuple(int(c + (255 - c) * flash_intensity * 0.7) for c in col)
        
        # Calculate ship angle
        ang = math.atan2(self.vy if (abs(self.vx)+abs(self.vy))>5 else 0, self.vx if (abs(self.vx)+abs(self.vy))>5 else 1)
        if self.is_player:
            mx, my = pygame.mouse.get_pos()
            ax, ay = mx + cam.x - self.x, my + cam.y - self.y
            ang = math.atan2(ay, ax)
        
        # Draw ship body
        pts = []
        size = self.size
        for a in (0, 140, -140):
            ra = ang + math.radians(a)
            pts.append((px + math.cos(ra)*size*0.9, py + math.sin(ra)*size*0.9))
        
        # Draw ship with effects
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (255,255,255), pts, 2)
        
        # Invulnerability effect
        if self.invuln > 0:
            invuln_alpha = 0.5 + 0.5 * math.sin(time.time() * 10)
            invuln_color = tuple(int(c * invuln_alpha) for c in (255, 255, 255))
            pygame.draw.circle(surf, invuln_color, (px, py), int(size*0.7), 2)
        
        # Status effect indicators
        if self.status_acid:
            pygame.draw.circle(surf, (120, 255, 140), (px - 15, py - 15), 3)
        if self.status_burn:
            pygame.draw.circle(surf, (100, 200, 255), (px + 15, py - 15), 3)
        if self.status_void:
            pygame.draw.circle(surf, (200, 100, 255), (px, py - 20), 3)
        if self.status_slow > 0:
            pygame.draw.circle(surf, (255, 200, 100), (px + 15, py + 15), 3)
        
        # Draw engine particles
        for particle in self.engine_particles:
            particle.draw(surf, cam)
        
        # Health and shield bars
        bw = 44; bh = 5; base_x = px - bw//2
        pygame.draw.rect(surf, (30,30,36), (base_x, py + size*0.9, bw, bh), border_radius=3)
        
        if self.hp > 0:
            hpw = int(bw * self.hp / self.max_hp)
            hp_color = (240,70,80) if self.hp < self.max_hp * 0.3 else (240,70,80)
            pygame.draw.rect(surf, hp_color, (base_x, py + size*0.9, hpw, bh), border_radius=3)
        
        if self.shield > 0:
            shw = int(bw * self.shield / self.max_shield)
            pygame.draw.rect(surf, (90,160,255), (base_x, py + size*0.9 + bh+2, shw, bh), border_radius=3)
        
        # Ability charge indicator
        if self.ability_charge > 0:
            charge_w = int(bw * self.ability_charge / 1.0)
            pygame.draw.rect(surf, (255, 200, 100), (base_x, py + size*0.9 + (bh+2)*2, charge_w, bh), border_radius=3)


# -----------------------------
# UI Elements
# -----------------------------
class Button:
    def __init__(self, rect, text, onclick=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.onclick = onclick
        self.hover = False

    def draw(self, surf, font):
        col = (60, 60, 70) if not self.hover else (80, 80, 96)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, (255,255,255), self.rect, 2, border_radius=10)
        label = font.render(self.text, True, (255,255,255))
        surf.blit(label, (self.rect.centerx - label.get_width()//2, self.rect.centery - label.get_height()//2))

    def handle(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            if self.onclick:
                self.onclick()


class Slider:
    def __init__(self, rect, minv, maxv, value):
        self.rect = pygame.Rect(rect)
        self.minv = minv
        self.maxv = maxv
        self.value = value
        self.drag = False

    def draw(self, surf):
        pygame.draw.rect(surf, (70,70,84), self.rect, border_radius=8)
        pygame.draw.rect(surf, (30,30,36), (self.rect.x+6, self.rect.y + self.rect.h//2 - 3, self.rect.w-12, 6), border_radius=3)
        t = (self.value - self.minv) / (self.maxv - self.minv)
        x = int(self.rect.x + 6 + t * (self.rect.w - 12))
        pygame.draw.circle(surf, (255,255,255), (x, self.rect.y + self.rect.h//2), 10)

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            self.drag = True
            self._set_from_pos(ev.pos[0])
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.drag = False
        elif ev.type == pygame.MOUSEMOTION and self.drag:
            self._set_from_pos(ev.pos[0])

    def _set_from_pos(self, x):
        t = clamp((x - (self.rect.x+6)) / (self.rect.w - 12), 0.0, 1.0)
        self.value = self.minv + t * (self.maxv - self.minv)


# -----------------------------
# Game Orchestrator
# -----------------------------
class Game:
    instance: 'Game' = None

    def __init__(self):
        Game.instance = self
        pygame.init()
        pygame.display.set_caption("Space Arena — командные космобои")
        
        # Initialize window manager
        self.window_manager = WindowManager()
        
        # Create resizable window
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        # Initialize fonts with scaling
        self._init_fonts()
        
        # Update window manager with current size
        self.window_manager.resize_window(SCREEN_W, SCREEN_H)

        sfx.init(); sfx.build()
        if sfx.enabled:
            pygame.mixer.music.set_volume(0.35)

        # Settings
        self.num_teams = 2
        self.volume = 0.7

        # World
        self.camera = Camera(ARENA_W, ARENA_H)
        self.camera.set_game_reference(self)
        self.ships: List[Ship] = []
        self.player: Optional[Ship] = None
        self.obstacles: List[Obstacle] = []
        self.capture_points: List[CapturePoint] = []
        self.pickups: List[Pickup] = []
        self.particles: List[Particle] = []
        self.dmgtexts: List[DamageText] = []
        self.trails: List[TrailSeg] = []

        # Projectiles/effects
        self.bullets: List[Bullet] = []
        self.missiles: List[HomingMissile] = []
        self.lasers: List[LaserBeam] = []
        self.arcs: List[ElectricArc] = []
        self.pulses: List[GravityPulse] = []
        self.plasma_balls: List[PlasmaBall] = []
        self.void_projectiles: List[VoidProjectile] = []

        # UI state
        self.state = GameState.MENU
        self.buttons: List[Button] = []
        self.sliders: List[Slider] = []
        self.show_upgrades = False
        self.show_classes = False
        self.show_stats = False
        self.show_tutorial = False

        # Game statistics
        self.game_start_time = 0.0
        self.game_duration = 0.0
        self.total_kills = 0
        self.total_captures = 0
        self.team_scores = {i: 0 for i in range(MAX_TEAMS_LIMIT)}

        # Dev helpers
        self.dev_anti_repeat = 0.0
        
        # Screen effects
        self.screen_effects: List[ScreenEffect] = []
        
        # Tutorial system
        self.tutorial_step = 0
        self.tutorial_completed = False

        self.setup_menu()

    def _init_fonts(self):
        """Initialize fonts with proper scaling"""
        scale_x, scale_y = self.window_manager.get_scale_factors()
        base_font_size = int(20 * min(scale_x, scale_y))
        base_font_size = max(12, min(base_font_size, 32))  # Clamp between 12 and 32
        
        big_font_size = int(48 * min(scale_x, scale_y))
        big_font_size = max(24, min(big_font_size, 72))
        
        mid_font_size = int(28 * min(scale_x, scale_y))
        mid_font_size = max(16, min(mid_font_size, 48))
        
        self.font = pygame.font.SysFont("Segoe UI", base_font_size)
        self.big = pygame.font.SysFont("Segoe UI Semibold", big_font_size)
        self.mid = pygame.font.SysFont("Segoe UI", mid_font_size)

    def _handle_resize(self, width, height):
        """Handle window resize event"""
        self.window_manager.resize_window(width, height)
        self._init_fonts()
        
        # Recreate screen with new size
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        
        # Recreate UI elements for current state
        if self.state == GameState.MENU:
            self.setup_menu()
        elif self.state == GameState.SETTINGS:
            self.goto_settings()

    # ---------- State setups ----------
    def setup_menu(self):
        self.buttons = []
        cx, cy = self.window_manager.center_position(280, 54)
        button_y_start = int(280 * self.window_manager.scale_y)
        button_spacing = int(70 * self.window_manager.scale_y)
        
        self.buttons.append(Button((cx, button_y_start, 280, 54), "Играть", self.start_game))
        self.buttons.append(Button((cx, button_y_start + button_spacing, 280, 54), "Настройки", self.goto_settings))
        self.buttons.append(Button((cx, button_y_start + button_spacing * 2, 280, 54), "Туториал", self.show_tutorial_menu))
        self.buttons.append(Button((cx, button_y_start + button_spacing * 3, 280, 54), "Выход", self.exit_game))

    def show_tutorial_menu(self):
        self.show_tutorial = True
        self.state = GameState.PLAY
        self.reset_world()
        self.game_start_time = time.time()
        self.game_duration = 0.0

    def goto_settings(self):
        self.state = GameState.SETTINGS
        self.buttons = []
        self.sliders = []
        cx, cy = self.window_manager.center_position(320, 50)
        slider_cx, slider_cy = self.window_manager.center_position(400, 40)
        
        # Scale positions
        back_y = int(560 * self.window_manager.scale_y)
        slider1_y = int(200 * self.window_manager.scale_y)
        slider2_y = int(300 * self.window_manager.scale_y)
        
        self.buttons.append(Button((cx, back_y, 320, 50), "Назад", self.back_to_menu))
        self.sliders.append(Slider((slider_cx, slider1_y, 400, 40), 0.0, 1.0, self.volume))
        self.sliders.append(Slider((slider_cx, slider2_y, 400, 40), 2, 6, self.num_teams))
        
        # Add SFX volume slider
        slider3_y = int(400 * self.window_manager.scale_y)
        self.sliders.append(Slider((slider_cx, slider3_y, 400, 40), 0.0, 1.0, sfx.sfx_volume))

    def back_to_menu(self):
        self.volume = self.sliders[0].value
        self.num_teams = int(round(self.sliders[1].value))
        sfx.sfx_volume = self.sliders[2].value
        pygame.mixer.music.set_volume(self.volume if sfx.enabled else 0)
        self.state = GameState.MENU
        self.setup_menu()

    def exit_game(self):
        pygame.quit(); sys.exit()

    def start_game(self):
        self.reset_world()
        self.state = GameState.PLAY
        self.game_start_time = time.time()
        self.game_duration = 0.0

    def reset_world(self):
        # Clear all game objects
        self.ships.clear()
        self.bullets.clear()
        self.missiles.clear()
        self.lasers.clear()
        self.arcs.clear()
        self.pulses.clear()
        self.plasma_balls.clear()
        self.void_projectiles.clear()
        self.obstacles.clear()
        self.capture_points.clear()
        self.pickups.clear()
        self.particles.clear()
        self.dmgtexts.clear()
        self.trails.clear()
        self.screen_effects.clear()
        
        # Reset camera
        self.camera.zoom = 1.0
        self.camera.target_zoom = 1.0
        
        # Obstacles random
        for _ in range(NUM_OBSTACLES):
            shape = random.choice(['rect', 'tri'])
            w = random.randint(40, 120)
            h = random.randint(40, 120)
            x = random.randint(300, ARENA_W-300)
            y = random.randint(300, ARENA_H-300)
            col = (80, 90, 110)
            self.obstacles.append(Obstacle(shape, pygame.Rect(x, y, w, h), col))
        
        # Spiked killers: corners + center cluster
        yellow = (250, 210, 60)
        for rx, ry in [(80, 80), (ARENA_W-80, 80), (80, ARENA_H-80), (ARENA_W-80, ARENA_H-80)]:
            self.obstacles.append(Obstacle('circle', pygame.Rect(rx-22, ry-22, 44, 44), yellow, spiked=True, kill=True))
        for _ in range(4):
            cx = ARENA_W//2 + random.randint(-300, 300)
            cy = ARENA_H//2 + random.randint(-300, 300)
            self.obstacles.append(Obstacle('circle', pygame.Rect(cx-22, cy-22, 44, 44), yellow, spiked=True, kill=True))
        
        # Capture points (more points for more teams)
        if self.num_teams <= 2:
            offsets = [(-700, -700), (700, -700), (-700, 700), (700, 700)]
        else:
            offsets = [(-700, -700), (700, -700), (-700, 700), (700, 700), (0, -700), (0, 700)]
        
        for ox, oy in offsets:
            self.capture_points.append(CapturePoint(ARENA_W//2 + ox, ARENA_H//2 + oy))
        
        # Ships per team
        for t in range(self.num_teams):
            for i in range(TEAM_SIZE):
                sx = random.uniform(SPAWN_ZONES[t].left+60, SPAWN_ZONES[t].right-60)
                sy = random.uniform(SPAWN_ZONES[t].top+60, SPAWN_ZONES[t].bottom-60)
                is_player = (t == 0 and i == 0)
                ship = Ship(sx, sy, t, is_player=is_player)
                ship.set_spawn_rect(SPAWN_ZONES[t])
                ship.unlocked['Blaster'] = True
                ship.weapon = 0
                if is_player:
                    self.player = ship
                self.ships.append(ship)
        
        if self.player:
            self.camera.center_on(self.player.x, self.player.y)

    # ---------- Class Tree helpers ----------
    def available_class_nodes(self, ship: Ship) -> List[str]:
        # допустимые к покупке сейчас (поинт есть, уровень достигнут, пререквизиты выполнены, ещё не взяты)
        avail = []
        # разрешён только текущий tier (равный количеству уже взятых поинтов)
        tier_allowed = len(ship.class_nodes)
        for nid, nd in CLASS_NODES.items():
            if nid in ship.class_nodes:
                continue
            tier = nd['tier']
            if tier != tier_allowed:
                continue
            # уровень проверки
            need_lvl = CLASS_TIERS_LEVELS[tier] if tier < len(CLASS_TIERS_LEVELS) else 999
            if ship.level < need_lvl:
                continue
            reqs = nd.get('requires', [])
            if any(r not in ship.class_nodes for r in reqs):
                continue
            avail.append(nid)
        return avail

    # ---------- Events ----------
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.exit_game()
            elif ev.type == pygame.VIDEORESIZE:
                self._handle_resize(ev.w, ev.h)
            if self.state in (GameState.MENU, GameState.SETTINGS):
                for b in self.buttons:
                    b.handle(ev)
                if self.state == GameState.SETTINGS:
                    for s in self.sliders:
                        s.handle(ev)
            elif self.state == GameState.PLAY:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSE
                # Dev cheats
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F6:
                    self.dev_add_level(1)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F7:
                    self.dev_add_level(5)
                if ev.type == pygame.KEYDOWN:
                    if pygame.K_1 <= ev.key <= pygame.K_9:
                        idx = ev.key - pygame.K_1
                        if 0 <= idx < len(WEAPON_TYPES):
                            wname = WEAPON_TYPES[idx]
                            if self.player.unlocked.get(wname, False):
                                self.player.weapon = idx
                    if ev.key == pygame.K_r:
                        self.use_player_reinforce()
                    if ev.key == pygame.K_q:
                        self.use_player_quantum()
                    if ev.key == pygame.K_t:
                        if self.player.can_teleport():
                            mx, my = pygame.mouse.get_pos()
                            self.player.use_teleport(mx + self.camera.x, my + self.camera.y)
                    if ev.key == pygame.K_SPACE:
                        if self.player.can_ultimate():
                            self.player.use_ultimate()
                    if ev.key == pygame.K_u:
                        self.show_upgrades = not self.show_upgrades
                    if ev.key == pygame.K_j:
                        self.show_classes = not self.show_classes
                    if ev.key == pygame.K_i:
                        self.show_stats = not self.show_stats
                    if ev.key == pygame.K_h:
                        self.show_tutorial = not self.show_tutorial
                    if ev.key == pygame.K_z:
                        self.camera.set_zoom(0.8)
                    if ev.key == pygame.K_x:
                        self.camera.set_zoom(1.2)
                    if ev.key == pygame.K_c:
                        self.camera.set_zoom(1.0)
            elif self.state == GameState.PAUSE:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.state = GameState.PLAY
            elif self.state == GameState.VICTORY:
                if ev.type == pygame.KEYDOWN:
                    self.state = GameState.MENU
                    self.setup_menu()

    def use_player_reinforce(self):
        if self.player and self.player.can_reinforce():
            self.player.use_reinforce()

    def use_player_quantum(self):
        if self.player and self.player.can_quantum():
            self.player.use_quantum()

    # ---------- Update ----------
    def update(self, dt):
        if self.state != GameState.PLAY:
            return
        
        # Update game time
        if self.game_start_time > 0:
            self.game_duration = time.time() - self.game_start_time
        
        # Update camera
        self.camera.update(dt)
        
        if self.dev_anti_repeat > 0:
            self.dev_anti_repeat -= dt
        
        # Player input
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        if self.player and not self.player.dead:
            ax = (keys[pygame.K_d] - keys[pygame.K_a]) * 900
            ay = (keys[pygame.K_s] - keys[pygame.K_w]) * 900
            self.player.accelerate(ax, ay, dt)
            
            # Shooting
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                world_mx, world_my = mx + self.camera.x, my + self.camera.y
                self.spawn_projectiles(self.player.shoot(world_mx, world_my))
            
            # Teleport ability
            if keys[pygame.K_t] and self.player.can_teleport():
                self.player.use_teleport(mx + self.camera.x, my + self.camera.y)
            
            # Ultimate ability
            if keys[pygame.K_SPACE] and self.player.can_ultimate():
                self.player.use_ultimate()
        
        # Update ships
        for sh in self.ships:
            if not sh.dead:
                sh.update(dt, self)
        
        # Respawn / cleanup
        to_remove = []
        for sh in self.ships:
            if sh.dead:
                if sh.is_reinforcement or sh.delete_me:
                    to_remove.append(sh)
                else:
                    sh.respawn()
        if to_remove:
            self.ships = [s for s in self.ships if s not in to_remove]
        
        # Update projectiles/effects
        self._update_projectiles(dt)
        self._update_effects(dt)
        
        # Update collisions
        self.handle_combat(dt)
        self.handle_obstacles(dt)
        self.update_capture_points(dt)
        
        # Update camera target
        if self.player:
            self.camera.lerp_to(self.player.x, self.player.y)
        
        # Check victory
        self.check_victory()
        
        # Update screen effects
        for effect in list(self.screen_effects):
            if not effect.update(dt):
                self.screen_effects.remove(effect)

    def _update_projectiles(self, dt):
        # Bullets
        for b in list(self.bullets):
            b.update(dt)
            if b.life <= 0:
                self.bullets.remove(b)
        
        # Missiles
        for m in list(self.missiles):
            m.update(dt, self.ships)
            if m.life <= 0:
                self.missiles.remove(m)
        
        # Lasers
        for lz in list(self.lasers):
            lz.update(dt)
            if lz.time <= 0:
                self.lasers.remove(lz)
        
        # Arcs
        for arc in list(self.arcs):
            arc.update(dt)
            if arc.time <= 0:
                self.arcs.remove(arc)
        
        # Pulses
        for pulse in list(self.pulses):
            pulse.update(dt, self.ships, self.bullets)
            if pulse.time <= 0:
                self.pulses.remove(pulse)
        
        # Plasma balls
        for pb in list(self.plasma_balls):
            pb.update(dt)
            if pb.life <= 0:
                self.plasma_balls.remove(pb)
        
        # Void projectiles
        for vp in list(self.void_projectiles):
            vp.update(dt)
            if vp.life <= 0:
                self.void_projectiles.remove(vp)

    def _update_effects(self, dt):
        # Pickups
        for p in list(self.pickups):
            p.update(dt)
            if p.life <= 0:
                self.pickups.remove(p)
        
        # Particles
        for prt in list(self.particles):
            prt.update(dt)
            if prt.life <= 0:
                self.particles.remove(prt)
        
        # Trails
        for tr in list(self.trails):
            tr.update(dt)
            if tr.life <= 0:
                self.trails.remove(tr)
        
        # Damage texts
        for dtxt in list(self.dmgtexts):
            dtxt.update(dt)
            if dtxt.life <= 0:
                self.dmgtexts.remove(dtxt)

    def spawn_projectiles(self, projs: List):
        for p in projs:
            if isinstance(p, Bullet):
                self.bullets.append(p)
            elif isinstance(p, HomingMissile):
                self.missiles.append(p)
            elif isinstance(p, LaserBeam):
                self.lasers.append(p)
            elif isinstance(p, PlasmaBall):
                self.plasma_balls.append(p)
            elif isinstance(p, VoidProjectile):
                self.void_projectiles.append(p)

    def handle_combat(self, dt):
        # Laser: щит снимается быстрее, HP — слабее
        for lz in self.lasers:
            x1, y1, x2, y2 = lz.segment()
            for sh in self.ships:
                if sh.dead or sh.team == lz.team:
                    continue
                px, py = sh.x, sh.y
                vx, vy = x2 - x1, y2 - y1
                l2 = vx*vx + vy*vy
                if l2 == 0: continue
                t = max(0.0, min(1.0, ((px - x1)*vx + (py - y1)*vy) / l2))
                projx = x1 + t*vx; projy = y1 + t*vy
                d2 = (px - projx)**2 + (py - projy)**2
                if d2 < (sh.size*0.7)**2:
                    base = lz.damage * 0.9 * dt
                    if sh.invuln <= 0:
                        if sh.shield > 0:
                            sh.shield = max(0.0, sh.shield - base * 1.7)
                            sh.hp -= base * 0.25
                        else:
                            sh.hp -= base * 0.7
                        sfx.play("hit")
                        if sh.hp <= 0:
                            sh.die(attacker=lz.owner)
        
        # Bullets
        for b in list(self.bullets):
            br = b.rect()
            for sh in self.ships:
                if sh.dead or sh.team == b.team:
                    continue
                sr = pygame.Rect(int(sh.x - sh.size*0.6), int(sh.y - sh.size*0.6), int(sh.size*1.2), int(sh.size*1.2))
                if br.colliderect(sr):
                    dmg = b.damage
                    crit = False
                    if random.random() < b.crit_chance:
                        dmg *= 2.0; crit = True
                    
                    damage_type = "normal"
                    if b.acid:
                        sh.add_acid(dps=6.0, dur=2.2)
                        damage_type = "acid"
                    elif b.plasma:
                        sh.status_burn.append((3.0, 4.0))
                        damage_type = "plasma"
                    elif b.void:
                        sh.status_void.append((2.5, 3.0))
                        damage_type = "void"
                    
                    sh.damage(dmg, attacker=b.owner, crit=crit, damage_type=damage_type)
                    try: self.bullets.remove(b)
                    except ValueError: pass
                    break
        
        # Missiles
        for m in list(self.missiles):
            mr = m.rect()
            hit = False
            for sh in self.ships:
                if sh.dead or sh.team == m.team:
                    continue
                sr = pygame.Rect(int(sh.x - sh.size*0.6), int(sh.y - sh.size*0.6), int(sh.size*1.2), int(sh.size*1.2))
                if mr.colliderect(sr):
                    sh.damage(m.damage, attacker=m.owner)
                    hit = True
                    break
            if hit:
                try: self.missiles.remove(m)
                except ValueError: pass
        
        # Plasma balls
        for pb in list(self.plasma_balls):
            pbr = pb.rect()
            for sh in self.ships:
                if sh.dead or sh.team == pb.team:
                    continue
                sr = pygame.Rect(int(sh.x - sh.size*0.6), int(sh.y - sh.size*0.6), int(sh.size*1.2), int(sh.size*1.2))
                if pbr.colliderect(sr):
                    sh.damage(pb.damage, attacker=pb.owner, damage_type="plasma")
                    sh.status_burn.append((3.0, 5.0))
                    try: self.plasma_balls.remove(pb)
                    except ValueError: pass
                    break
        
        # Void projectiles
        for vp in list(self.void_projectiles):
            vpr = vp.rect()
            for sh in self.ships:
                if sh.dead or sh.team == vp.team:
                    continue
                sr = pygame.Rect(int(sh.x - sh.size*0.6), int(sh.y - sh.size*0.6), int(sh.size*1.2), int(sh.size*1.2))
                if vpr.colliderect(sr):
                    sh.damage(vp.damage, attacker=vp.owner, damage_type="void")
                    sh.status_void.append((4.0, 6.0))
                    sh.status_slow = max(sh.status_slow, 2.0)
                    try: self.void_projectiles.remove(vp)
                    except ValueError: pass
                    break
        
        # Trails damage
        for tr in self.trails:
            for sh in self.ships:
                if sh.dead or sh.team == tr.team:
                    continue
                if (sh.x - tr.x)**2 + (sh.y - tr.y)**2 < (tr.r + sh.size*0.3)**2:
                    sh.damage(12.0 * dt, attacker=None)

    def handle_obstacles(self, dt):
        for sh in self.ships:
            if sh.dead: continue
            sr = pygame.Rect(int(sh.x - sh.size*0.5), int(sh.y - sh.size*0.5), int(sh.size), int(sh.size))
            for ob in self.obstacles:
                orr = ob.rect
                collide = False
                if ob.shape in ('rect','tri'):
                    collide = sr.colliderect(orr)
                else:
                    cx, cy = orr.center
                    if (sh.x - cx)**2 + (sh.y - cy)**2 < (orr.w//2 + sh.size*0.4)**2:
                        collide = True
                if collide:
                    speed = vec_len(sh.vx, sh.vy)
                    if ob.kill or ob.spiked:
                        sh.damage(9999, attacker=None, ignore_invuln=True)
                    else:
                        base = 1.0 if speed < 180 else (2.0 if speed < 280 else (5.0 if speed < 380 else 10.0))
                        sh.damage(base, attacker=None)
                        sh.x += random.uniform(-6, 6)
                        sh.y += random.uniform(-6, 6)
            # Pickups
            for p in list(self.pickups):
                if sr.colliderect(p.rect()):
                    owner = sh
                    owner.award_spheres(p.value)
                    try: self.pickups.remove(p)
                    except ValueError: pass

    def update_capture_points(self, dt):
        for cp in self.capture_points:
            cp.update(dt, self.ships)

    def check_victory(self):
        owners = {t: 0 for t in range(self.num_teams)}
        for cp in self.capture_points:
            if cp.owner is not None and cp.owner < self.num_teams:
                owners[cp.owner] += 1
        
        for t, cnt in owners.items():
            if cnt >= NUM_POINTS:
                self.winner = t
                self.state = GameState.VICTORY
                
                # Victory effects
                for _ in range(50):
                    x = random.uniform(0, SCREEN_W)
                    y = random.uniform(0, SCREEN_H)
                    Game.instance.particles.append(Particle(
                        x, y,
                        random.uniform(-100, 100), random.uniform(-100, 100),
                        2.0, TEAM_COLORS[t], 5, "spark"
                    ))
                
                # Victory screen effect
                self.screen_effects.append(ScreenEffect("flash", 0.5, 0.3, TEAM_COLORS[t]))
                break

    def apply_upgrade(self, ship: Ship, key: str):
        if ship.upgrade_points <= 0: return
        
        def inc(attr):
            lvl = getattr(ship, attr)
            if lvl < MAX_UPGRADE_LEVEL:
                setattr(ship, attr, lvl+1)
                ship.upgrade_points -= 1
                return True
            return False
        
        success = False
        
        if key == 'speed': 
            success = inc('up_speed')
        elif key == 'firerate': 
            success = inc('up_firerate')
        elif key == 'damage': 
            success = inc('up_damage')
        elif key == 'armor':
            if ship.up_armor < MAX_UPGRADE_LEVEL:
                ship.max_shield += 6
                ship.shield_regen += 0.6
                ship.max_hp += 6
                ship.hp = min(ship.hp + 6, ship.max_hp)
                ship.shield = min(ship.shield + 6, ship.max_shield)
                ship.up_armor += 1
                ship.upgrade_points -= 1
                success = True
        elif key in WEAPON_TYPES:
            if not ship.unlocked.get(key, False):
                ship.unlocked[key] = True
                ship.upgrade_points -= 1
                if ship.is_player:
                    try:
                        ship.weapon = WEAPON_TYPES.index(key)
                    except ValueError:
                        pass
                success = True
            else:
                cur = ship.get_weapon_level(key)
                if cur < MAX_UPGRADE_LEVEL:
                    ship.weapon_levels[key] = cur + 1
                    ship.upgrade_points -= 1
                    success = True
        elif key == 'trail': 
            success = inc('up_trail')
        elif key == 'resource': 
            success = inc('up_resource')
        elif key == 'crit': 
            success = inc('up_crit')
        elif key == 'reinforce': 
            success = inc('up_reinforce')
        elif key == 'quantum': 
            success = inc('up_quantum')
        elif key == 'teleport': 
            success = inc('up_teleport')
        elif key == 'ultimate': 
            success = inc('up_ultimate')
        
        if success and ship.is_player:
            sfx.play("powerup")
            ship.level_up_flash = 0.5

    def apply_random_upgrade(self, ship: Ship):
        pool = ['speed','firerate','damage','armor','trail','resource','crit','reinforce','quantum'] + WEAPON_TYPES
        random.shuffle(pool)
        for k in pool:
            before = ship.upgrade_points
            self.apply_upgrade(ship, k)
            if ship.upgrade_points < before:
                break

    # ---------- Dev tools ----------
    def dev_add_level(self, levels=1):
        if not self.player:
            return
        for _ in range(levels):
            if self.player.level >= MAX_LEVEL:
                break
            mult = max(1.0, self.player.resource_mult())
            need = max(1, int(math.ceil((self.player.need_spheres() - self.player.spheres_this_level) / mult)))
            self.player.award_spheres(need)

    # ---------- Draw ----------
    def draw(self):
        self.screen.fill((12, 14, 22))
        if self.state == GameState.MENU:
            self.draw_title()
            [b.draw(self.screen, self.mid) for b in self.buttons]
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
        elif self.state in (GameState.PLAY, GameState.PAUSE, GameState.VICTORY):
            self.draw_world()
            self.draw_hud()
            if self.state == GameState.PAUSE:
                self.draw_pause()
            if self.state == GameState.VICTORY:
                self.draw_victory()
            if self.show_stats:
                self.draw_stats_overlay()
            if self.show_tutorial:
                self.draw_tutorial_overlay()
        pygame.display.flip()

    def draw_title(self):
        title = self.big.render("SPACE ARENA", True, (255,255,255))
        title_x, title_y = self.window_manager.center_position(title.get_width(), title.get_height())
        title_y = int(120 * self.window_manager.scale_y)
        self.screen.blit(title, (title_x, title_y))
        
        sub = self.mid.render("Командные космобои с захватом точек", True, (180, 190, 210))
        sub_x, sub_y = self.window_manager.center_position(sub.get_width(), sub.get_height())
        sub_y = int(190 * self.window_manager.scale_y)
        self.screen.blit(sub, (sub_x, sub_y))
        
        version = self.font.render("v2.0 - Enhanced Edition", True, (150, 160, 180))
        version_x, version_y = self.window_manager.center_position(version.get_width(), version.get_height())
        version_y = int(220 * self.window_manager.scale_y)
        self.screen.blit(version, (version_x, version_y))

    def draw_settings(self):
        self.draw_title()
        
        # Scale positions
        label_x = int((self.window_manager.current_width // 2 - 200) * self.window_manager.scale_x)
        label1_y = int(160 * self.window_manager.scale_y)
        label2_y = int(260 * self.window_manager.scale_y)
        label3_y = int(360 * self.window_manager.scale_y)
        
        label1 = self.mid.render("Громкость музыки", True, (220, 230, 240))
        self.screen.blit(label1, (label_x, label1_y))
        self.sliders[0].draw(self.screen)
        
        label2 = self.mid.render("Число команд (2–6)", True, (220, 230, 240))
        self.screen.blit(label2, (label_x, label2_y))
        self.sliders[1].draw(self.screen)
        
        label3 = self.mid.render("Громкость эффектов", True, (220, 230, 240))
        self.screen.blit(label3, (label_x, label3_y))
        self.sliders[2].draw(self.screen)
        
        for b in self.buttons:
            b.draw(self.screen, self.mid)

    def draw_world(self):
        # Get current screen size
        screen_w, screen_h = self.window_manager.get_screen_size()
        
        # Grid with zoom
        grid_step = int(100 * self.camera.zoom)
        ox, oy = -self.camera.x % grid_step, -self.camera.y % grid_step
        for x in range(int(ox), screen_w, grid_step):
            pygame.draw.line(self.screen, (24, 28, 42), (x, 0), (x, screen_h))
        for y in range(int(oy), screen_h, grid_step):
            pygame.draw.line(self.screen, (24, 28, 42), (0, y), (screen_w, y))
        
        # Spawn zones
        for i in range(self.num_teams):
            r = SPAWN_ZONES[i].move(-self.camera.x, -self.camera.y)
            alpha = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            c = TEAM_COLORS[i]
            pygame.draw.rect(alpha, (*c, 50), (0, 0, r.w, r.h), border_radius=16)
            self.screen.blit(alpha, r.topleft)
            pygame.draw.rect(self.screen, c, r, 2, border_radius=16)
        
        # Capture points
        for cp in self.capture_points:
            cp.draw(self.screen, self.camera)
        
        # Obstacles & effects
        for ob in self.obstacles:
            if self.camera.rect_on_screen(ob.rect):
                ob.draw(self.screen, self.camera)
        
        # Particles and trails
        for prt in self.particles:
            prt.draw(self.screen, self.camera)
        for tr in self.trails:
            tr.draw(self.screen, self.camera)
        
        # Projectiles
        for arc in self.arcs:
            arc.draw(self.screen, self.camera)
        for pulse in self.pulses:
            pulse.draw(self.screen, self.camera)
        for lz in self.lasers:
            lz.draw(self.screen, self.camera)
        for b in self.bullets:
            b.draw(self.screen, self.camera)
        for m in self.missiles:
            m.draw(self.screen, self.camera)
        for pb in self.plasma_balls:
            pb.draw(self.screen, self.camera)
        for vp in self.void_projectiles:
            vp.draw(self.screen, self.camera)
        
        # Ships & pickups
        for sh in self.ships:
            if not sh.dead:
                sh.draw(self.screen, self.camera)
        for p in self.pickups:
            p.draw(self.screen, self.camera)
        for dtxt in self.dmgtexts:
            dtxt.draw(self.screen, self.camera, self.font)
        
        # Screen effects overlay
        for effect in self.screen_effects:
            if effect.effect_type == "flash":
                screen_w, screen_h = self.window_manager.get_screen_size()
                overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
                alpha = int(255 * effect.intensity * (effect.duration / 0.3))
                overlay.fill((*effect.color, alpha))
                self.screen.blit(overlay, (0, 0))

    def draw_hud(self):
        if not self.player: return
        
        # Scale positions
        px = int(30 * self.window_manager.scale_x)
        py = int(20 * self.window_manager.scale_y)
        bw = int(280 * self.window_manager.scale_x)
        
        pygame.draw.rect(self.screen, (28,32,44), (px-4, py-4, bw+8, 44), border_radius=10)
        # HP/Shield
        pygame.draw.rect(self.screen, (60,18,24), (px, py, bw, 14), border_radius=6)
        hpw = int(bw * self.player.hp / self.player.max_hp)
        pygame.draw.rect(self.screen, (240,70,80), (px, py, hpw, 14), border_radius=6)
        pygame.draw.rect(self.screen, (20,30,50), (px, py+18, bw, 14), border_radius=6)
        shw = int(bw * self.player.shield / self.player.max_shield)
        pygame.draw.rect(self.screen, (90,160,255), (px, py+18, shw, 14), border_radius=6)
        # XP bar (сферы)
        need_s = self.player.need_spheres()
        bw2 = int(420 * self.window_manager.scale_x)
        bx, by = self.window_manager.center_position(bw2, 14)
        by = int((self.window_manager.current_height - 26) * self.window_manager.scale_y)
        frac = clamp(self.player.spheres_this_level / max(1, need_s), 0.0, 1.0)
        pygame.draw.rect(self.screen, (28,32,44), (bx-4, by-4, bw2+8, 22), border_radius=10)
        pygame.draw.rect(self.screen, (30,36,52), (bx, by, bw2, 14), border_radius=6)
        pygame.draw.rect(self.screen, (230, 200, 80), (bx, by, int(bw2*frac), 14), border_radius=6)
        info = f"LV {self.player.level} | сферы: {self.player.spheres_this_level}/{need_s} | очки: {self.player.upgrade_points} | классы: {self.player.class_points}"
        t = self.font.render(info, True, (240,240,240))
        self.screen.blit(t, (bx + bw2//2 - t.get_width()//2, by - 22))
        # Weapon strip (locked/available)
        wx = int((self.window_manager.current_width - 900) * self.window_manager.scale_x)
        wy = int((self.window_manager.current_height - 80) * self.window_manager.scale_y)
        for i, name in enumerate(WEAPON_TYPES):
            r = pygame.Rect(wx + i*70, wy, 65, 50)
            unlocked = self.player.unlocked.get(name, False)
            col = (40,40,52)
            if unlocked:
                col = (60,60,76) if i != self.player.weapon else (90, 100, 140)
            pygame.draw.rect(self.screen, col, r, border_radius=10)
            pygame.draw.rect(self.screen, (255,255,255), r, 2, border_radius=10)
            label = name if len(name)<=6 else name[:5]
            t2 = self.font.render(label, True, (255,255,255) if unlocked else (150,150,160))
            self.screen.blit(t2, (r.centerx - t2.get_width()//2, r.centery - t2.get_height()//2))
            
            # Show weapon level
            if unlocked and self.player.weapon_levels.get(name, 1) > 1:
                level_text = str(self.player.weapon_levels.get(name, 1))
                level_surf = self.font.render(level_text, True, (255, 200, 100))
                self.screen.blit(level_surf, (r.right - level_surf.get_width() - 2, r.top + 2))
        
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            for i in range(len(WEAPON_TYPES)):
                r = pygame.Rect(wx + i*70, wy, 65, 50)
                if r.collidepoint((mx,my)):
                    name = WEAPON_TYPES[i]
                    if self.player.unlocked.get(name, False):
                        self.player.weapon = i
        # Abilities buttons
        ax = int(30 * self.window_manager.scale_x)
        ay = int((self.window_manager.current_height - 80) * self.window_manager.scale_y)
        r1 = pygame.Rect(ax, ay, 120, 50)
        r2 = pygame.Rect(ax+140, ay, 160, 50)
        r3 = pygame.Rect(ax+320, ay, 120, 50)
        r4 = pygame.Rect(ax+460, ay, 160, 50)
        
        self.draw_ability_button(r1, "Подкрепл. (R)", self.player.reinforce_cd)
        self.draw_ability_button(r2, "Квантум (Q)", self.player.quantum_cd)
        self.draw_ability_button(r3, "Телепорт (T)", self.player.teleport_cd)
        
        # Ultimate button
        if self.player.can_ultimate():
            col = (120, 80, 40)
        else:
            col = (80, 80, 96)
        pygame.draw.rect(self.screen, col, r4, border_radius=10)
        pygame.draw.rect(self.screen, (255,255,255), r4, 2, border_radius=10)
        lbl = self.font.render("УЛЬТИМАТ (SPACE)", True, (255,255,255))
        self.screen.blit(lbl, (r4.centerx - lbl.get_width()//2, r4.centery - lbl.get_height()//2))
        
        # Dev button: +1 уровень
        r5 = pygame.Rect(ax+640, ay, 130, 50)
        pygame.draw.rect(self.screen, (96, 70, 70), r5, border_radius=10)
        pygame.draw.rect(self.screen, (255,255,255), r5, 2, border_radius=10)
        lbl = self.font.render("DEV +LVL", True, (255,255,255))
        self.screen.blit(lbl, (r5.centerx - lbl.get_width()//2, r5.centery - lbl.get_height()//2))
        
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if r1.collidepoint((mx,my)):
                self.use_player_reinforce()
            if r2.collidepoint((mx,my)):
                self.use_player_quantum()
            if r3.collidepoint((mx,my)):
                self.player.use_teleport(mx + self.camera.x, my + self.camera.y)
            if r4.collidepoint((mx,my)):
                self.player.use_ultimate()
            if self.dev_anti_repeat <= 0 and r5.collidepoint((mx,my)):
                self.dev_add_level(1)
                self.dev_anti_repeat = 0.25
        # Team ownership display
        owners = {t: 0 for t in range(self.num_teams)}
        for cp in self.capture_points:
            if cp.owner is not None and cp.owner < self.num_teams:
                owners[cp.owner] += 1
        info2 = "  ".join([f"{TEAM_NAMES[t]}: {owners[t]} / {NUM_POINTS}" for t in range(self.num_teams)])
        t2 = self.mid.render(info2, True, (220, 230, 240))
        t2_x, t2_y = self.window_manager.center_position(t2.get_width(), t2.get_height())
        t2_y = int(12 * self.window_manager.scale_y)
        self.screen.blit(t2, (t2_x, t2_y))
        
        # Game time
        time_text = f"Время: {int(self.game_duration)}с"
        time_surf = self.font.render(time_text, True, (200, 210, 225))
        time_x = int((self.window_manager.current_width - time_surf.get_width() - 20) * self.window_manager.scale_x)
        time_y = int(12 * self.window_manager.scale_y)
        self.screen.blit(time_surf, (time_x, time_y))
        
        # Buttons for overlays
        btn = self.font.render("U — Прокачка  |  J — Древо классов  |  I — Статистика  |  H — Туториал", True, (200,210,225))
        btn_x = int(30 * self.window_manager.scale_x)
        btn_y = int(90 * self.window_manager.scale_y)
        self.screen.blit(btn, (btn_x, btn_y))
        
        # Zoom indicator
        zoom_text = f"Зум: {self.camera.zoom:.1f}x"
        zoom_surf = self.font.render(zoom_text, True, (200, 210, 225))
        zoom_x = int(30 * self.window_manager.scale_x)
        zoom_y = int(120 * self.window_manager.scale_y)
        self.screen.blit(zoom_surf, (zoom_x, zoom_y))
        # Overlays
        if self.show_upgrades or self.player.upgrade_points > 0:
            self.draw_upgrade_overlay()
        if self.show_classes or self.player.class_points > 0:
            self.draw_class_overlay()

    def draw_ability_button(self, r: pygame.Rect, text: str, cd: float):
        col = (60,60,76) if cd <= 0 else (80,80,96)
        pygame.draw.rect(self.screen, col, r, border_radius=10)
        pygame.draw.rect(self.screen, (255,255,255), r, 2, border_radius=10)
        label = self.font.render(text, True, (255,255,255))
        self.screen.blit(label, (r.centerx - label.get_width()//2, r.centery - label.get_height()//2))
        if cd > 0:
            cdtxt = self.font.render(f"{cd:.0f}s", True, (230,230,230))
            self.screen.blit(cdtxt, (r.right - cdtxt.get_width() - 8, r.bottom - cdtxt.get_height() - 6))

    def draw_upgrade_overlay(self):
        bw, bh = int(820 * self.window_manager.scale_x), int(420 * self.window_manager.scale_y)
        bx, by = self.window_manager.center_position(bw, bh)
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((16, 18, 28, 230))
        pygame.draw.rect(panel, (255,255,255), (0,0,bw,bh), 2, border_radius=14)
        title = self.mid.render("Прокачка — очки: %d"%self.player.upgrade_points, True, (240, 240, 255))
        panel.blit(title, (bw//2 - title.get_width()//2, 14))
        self.screen.blit(panel, (bx, by))
        options = [
            ("Скорость", 'speed'), ("Темп", 'firerate'), ("Урон", 'damage'), ("Броня", 'armor'),
            ("Trail", 'trail'), ("Ресурсы", 'resource'), ("Крит", 'crit'), ("Reinf", 'reinforce'), ("Quantum", 'quantum'),
            ("Телепорт", 'teleport'), ("Ультимат", 'ultimate'),
        ]
        for w in WEAPON_TYPES:
            label = (f"Unlock {w}" if not self.player.unlocked.get(w, False) else f"{w} +")
            options.append((label, w))
        mx, my = pygame.mouse.get_pos()
        cols = 4
        btns = []
        for idx, (label, key) in enumerate(options):
            cx = idx % cols; cy = idx // cols
            r = pygame.Rect(bx + 20 + cx* (bw//cols - 30), by + 60 + cy*70, bw//cols - 40, 56)
            btns.append((r, key))
            hover = r.collidepoint((mx,my))
            col = (60,70,96) if not hover else (90, 110, 150)
            pygame.draw.rect(self.screen, col, r, border_radius=10)
            pygame.draw.rect(self.screen, (255,255,255), r, 2, border_radius=10)
            self.screen.blit(self.font.render(label, True, (255,255,255)), (r.x + 12, r.y + 10))
        if pygame.mouse.get_pressed()[0] and self.player.upgrade_points > 0:
            for r, key in btns:
                if r.collidepoint((mx,my)):
                    self.apply_upgrade(self.player, key)
                    break

    def draw_class_overlay(self):
        bw, bh = int(900 * self.window_manager.scale_x), int(460 * self.window_manager.scale_y)
        bx, by = self.window_manager.center_position(bw, bh)
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((16, 18, 28, 230))
        pygame.draw.rect(panel, (255,255,255), (0,0,bw,bh), 2, border_radius=14)
        title = self.mid.render(f"Древо классов — поинтов: {self.player.class_points}", True, (240, 240, 255))
        panel.blit(title, (bw//2 - title.get_width()//2, 14))
        self.screen.blit(panel, (bx, by))
        # Рисуем по тиру столбцы
        max_tier = max(nd['tier'] for nd in CLASS_NODES.values()) if CLASS_NODES else 0
        columns: List[List[Tuple[str,Dict]]] = [[] for _ in range(max_tier + 1)]
        for nid, nd in CLASS_NODES.items():
            columns[nd['tier']].append((nid, nd))
        for col in columns:
            col.sort(key=lambda x: x[1]['name'])
        mx, my = pygame.mouse.get_pos()
        btns = []
        col_w = bw // len(columns) if columns else bw
        for ti, col in enumerate(columns):
            for i, (nid, nd) in enumerate(col):
                r = pygame.Rect(bx + 10 + ti*col_w + 10, by + 60 + i*60, col_w - 40, 48)
                taken = (nid in self.player.class_nodes)
                allowed_nodes = self.available_class_nodes(self.player)
                can_buy = (nid in allowed_nodes and self.player.class_points > 0)
                colr = (40,48,66)
                if taken:
                    colr = (70,110,90)
                elif can_buy:
                    colr = (70,90,130)
                pygame.draw.rect(self.screen, colr, r, border_radius=8)
                pygame.draw.rect(self.screen, (255,255,255), r, 2, border_radius=8)
                label = self.font.render(nd['name'], True, (255,255,255))
                self.screen.blit(label, (r.x + 10, r.y + 12))
                req = ", ".join(nd.get('requires', []))
                if req:
                    s = self.font.render(f"req: {req}", True, (190,190,200))
                    self.screen.blit(s, (r.right - s.get_width() - 8, r.y + 12))
                btns.append((r, nid, can_buy))
        if pygame.mouse.get_pressed()[0] and self.player.class_points > 0:
            for r, nid, can_buy in btns:
                if can_buy and r.collidepoint((mx,my)):
                    self.player.add_class_node(nid)
                    self.player.class_points -= 1
                    break

    def draw_pause(self):
        screen_w, screen_h = self.window_manager.get_screen_size()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 180))
        self.screen.blit(overlay, (0,0))
        
        t = self.big.render("Пауза", True, (255,255,255))
        t_x, t_y = self.window_manager.center_position(t.get_width(), t.get_height())
        t_y = int((screen_h // 2 - 100) * self.window_manager.scale_y)
        self.screen.blit(t, (t_x, t_y))
        
        t2 = self.mid.render("ESC — продолжить", True, (210, 220, 230))
        t2_x, t2_y = self.window_manager.center_position(t2.get_width(), t2.get_height())
        t2_y = int((screen_h // 2 - 40) * self.window_manager.scale_y)
        self.screen.blit(t2, (t2_x, t2_y))
        
        t3 = self.font.render("U — Прокачка  |  J — Древо классов  |  I — Статистика  |  H — Туториал", True, (200, 210, 225))
        t3_x, t3_y = self.window_manager.center_position(t3.get_width(), t3.get_height())
        t3_y = int((screen_h // 2 + 20) * self.window_manager.scale_y)
        self.screen.blit(t3, (t3_x, t3_y))
        
        t4 = self.font.render("Z/X/C — зум камеры  |  T — телепорт  |  SPACE — ультимат", True, (200, 210, 225))
        t4_x, t4_y = self.window_manager.center_position(t4.get_width(), t4.get_height())
        t4_y = int((screen_h // 2 + 45) * self.window_manager.scale_y)
        self.screen.blit(t4, (t4_x, t4_y))

    def draw_victory(self):
        screen_w, screen_h = self.window_manager.get_screen_size()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 200))
        self.screen.blit(overlay, (0,0))
        
        c = TEAM_COLORS[self.winner]
        t = self.big.render(f"Победили: {TEAM_NAMES[self.winner]}", True, c)
        t_x, t_y = self.window_manager.center_position(t.get_width(), t.get_height())
        t_y = int((screen_h // 2 - 40) * self.window_manager.scale_y)
        self.screen.blit(t, (t_x, t_y))
        
        t2 = self.mid.render("Нажмите любую клавишу — в меню", True, (230, 235, 240))
        t2_x, t2_y = self.window_manager.center_position(t2.get_width(), t2.get_height())
        t2_y = int((screen_h // 2 + 10) * self.window_manager.scale_y)
        self.screen.blit(t2, (t2_x, t2_y))

    def draw_stats_overlay(self):
        bw, bh = int(600 * self.window_manager.scale_x), int(400 * self.window_manager.scale_y)
        bx, by = self.window_manager.center_position(bw, bh)
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((16, 18, 28, 230))
        pygame.draw.rect(panel, (255,255,255), (0,0,bw,bh), 2, border_radius=14)
        
        title = self.mid.render("Статистика игры", True, (240, 240, 255))
        panel.blit(title, (bw//2 - title.get_width()//2, 14))
        
        if self.player:
            stats = [
                f"Время игры: {int(self.game_duration)}с",
                f"Уровень: {self.player.level}",
                f"Убийства: {self.player.kills}",
                f"Помощь: {self.player.assists}",
                f"Захваты: {self.player.captures}",
                f"Смерти: {self.player.deaths}",
                f"Урон нанесено: {self.player.damage_dealt}",
                f"Урон получено: {self.player.damage_taken}",
                f"Сферы собрано: {self.player.total_spheres}",
                f"Очки: {self.player.score}",
            ]
            
            for i, stat in enumerate(stats):
                text = self.font.render(stat, True, (240, 240, 240))
                panel.blit(text, (20, 60 + i * 25))
        
        # Close button
        close_text = self.font.render("Нажмите I для закрытия", True, (200, 200, 220))
        panel.blit(close_text, (bw//2 - close_text.get_width()//2, bh - 30))
        
        self.screen.blit(panel, (bx, by))

    def draw_tutorial_overlay(self):
        bw, bh = int(700 * self.window_manager.scale_x), int(600 * self.window_manager.scale_y)
        bx, by = self.window_manager.center_position(bw, bh)
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((16, 18, 28, 230))
        pygame.draw.rect(panel, (255,255,255), (0,0,bw,bh), 2, border_radius=14)
        
        title = self.mid.render("Управление и геймплей", True, (240, 240, 255))
        panel.blit(title, (bw//2 - title.get_width()//2, 14))
        
        tutorial_text = [
            "УПРАВЛЕНИЕ:",
            "WASD - движение",
            "Мышь - стрельба",
            "1-9 - смена оружия",
            "R - подкрепление",
            "Q - квантум",
            "T - телепорт",
            "SPACE - ультимат",
            "",
            "ГЕЙМПЛЕЙ:",
            "• Собирайте сферы для прокачки",
            "• Захватывайте точки командой",
            "• Выбирайте классы в древе",
            "• Используйте разные типы оружия",
            "• Комбинируйте способности",
            "• Новое оружие: Плазма и Пустота",
            "• Новые эффекты: ожоги, коррупция",
            "",
            "ГОРЯЧИЕ КЛАВИШИ:",
            "U - прокачка",
            "J - древо классов",
            "I - статистика",
            "H - туториал",
            "Z/X/C - зум камеры",
            "",
            "НОВЫЕ ФУНКЦИИ:",
            "• Улучшенная камера с зумом",
            "• Система статистики",
            "• Новые способности",
            "• Улучшенные эффекты",
            "• Больше команд (до 6)",
        ]
        
        for i, text in enumerate(tutorial_text):
            color = (255, 200, 100) if text.endswith(":") else (240, 240, 240)
            text_surf = self.font.render(text, True, color)
            panel.blit(text_surf, (20, 60 + i * 20))
        
        # Close button
        close_text = self.font.render("Нажмите I для закрытия", True, (200, 200, 220))
        panel.blit(close_text, (bw//2 - close_text.get_width()//2, bh - 30))
        
        self.screen.blit(panel, (bx, by))

    # ---------- Main loop ----------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()


if __name__ == '__main__':
    try:
        Game().run()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        with open('error_log.txt', 'w', encoding='utf-8') as f:
            f.write(tb)
        print(tb)
        raise
