import pygame
import random
import sys
import time
import json
import os
import math
import numpy as np

# Предварительная инициализация микшера для стабильного воспроизведения звука
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# --- Процедурная библиотека звуков через NumPy ---
SFX = {}

def make_sfx(kind, duration=0.12, volume=0.5):
    sr = 44100
    n = max(1, int(sr * duration))
    t = np.arange(n, dtype=np.float32) / sr

    if kind == "button":
        f = 180 + 900 * np.exp(-t * 35)
        wave = np.sin(2 * np.pi * f * t)
        env = np.exp(-t * 28)
    elif kind == "collect":
        f1, f2 = 880, 1320
        wave = 0.65 * np.sin(2 * np.pi * f1 * t) + 0.35 * np.sin(2 * np.pi * f2 * t)
        env = np.exp(-t * 16)
    elif kind == "bomb":
        noise = np.random.uniform(-1, 1, n).astype(np.float32)
        low = np.sin(2 * np.pi * 75 * t)
        wave = 0.78 * noise + 0.42 * low
        env = np.exp(-t * 10)
    elif kind == "purchase":
        split = int(n * 0.38)
        wave = np.zeros(n, dtype=np.float32)
        if split > 0:
            t1 = t[:split]
            wave[:split] = np.sin(2 * np.pi * 520 * t1) * np.exp(-t1 * 30)
        t2 = t[split:] - t[split]
        wave[split:] = (
            0.7 * np.sin(2 * np.pi * 1046 * t2)
            + 0.3 * np.sin(2 * np.pi * 1568 * t2)
        ) * np.exp(-t2 * 12)
        env = np.ones(n, dtype=np.float32)
    elif kind == "select":
        wave = np.sin(2 * np.pi * 620 * t)
        env = np.exp(-t * 32)
    elif kind == "error":
        wave = np.sin(2 * np.pi * 170 * t)
        env = np.exp(-t * 14)
    elif kind == "spin":
        f = 300 + 900 * (t / max(duration, 0.001))
        wave = np.sin(2 * np.pi * f * t)
        env = np.exp(-t * 5)
    elif kind == "reward":
        wave = (
            0.5 * np.sin(2 * np.pi * 660 * t)
            + 0.35 * np.sin(2 * np.pi * 880 * t)
            + 0.2 * np.sin(2 * np.pi * 1320 * t)
        )
        env = np.exp(-t * 5)
    elif kind == "shield":
        f = 420 + 1000 * t / max(duration, 0.001)
        wave = np.sin(2 * np.pi * f * t)
        env = np.exp(-t * 8)
    elif kind == "game_over":
        f = 500 - 330 * (t / max(duration, 0.001))
        wave = np.sin(2 * np.pi * f * t)
        env = np.exp(-t * 4)
    elif kind == "bounce":
        f = 350 + 200 * np.exp(-t * 40)
        wave = np.sin(2 * np.pi * f * t)
        env = np.exp(-t * 30)
    elif kind == "loss_life":
        f = 220 - 120 * (t / max(duration, 0.001))
        wave = np.sin(2 * np.pi * f * t)
        env = np.exp(-t * 10)
    else:
        wave = np.zeros(n, dtype=np.float32)
        env = np.ones(n, dtype=np.float32)

    audio = np.clip(wave * env * volume, -1, 1)
    stereo = np.column_stack((audio, audio))
    pcm = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(pcm)

# Относительные пути (для ПК и Android Buildozer)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIRS = [
    os.path.join(BASE_DIR, "all_music_and_SFX"),
    os.path.join(BASE_DIR, "data"),
    BASE_DIR,
]

# Функция для безопасного сохранения данных на Android
def get_save_path():
    try:
        from android.storage import app_storage_path
        return os.path.join(app_storage_path(), "save_data.json")
    except ImportError:
        return os.path.join(BASE_DIR, "save_data.json")

SAVE_FILE = get_save_path()

SFX_FILES = {
    "button":    "button",
    "select":    "button",
    "collect":   "collect",
    "bomb":      "bomb",
    "purchase":  "purchase",
    "error":     "error",
    "spin":      "spin",
    "reward":    "reward",
    "shield":    "shield",
    "game_over": "game_over",
    "bounce":    "bounce",
    "loss_life": "loss_life",
}

AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")
SFX_BASENAMES = set(SFX_FILES.values())

def find_audio_file(basename):
    for folder in AUDIO_DIRS:
        if not os.path.exists(folder):
            continue
        for ext in AUDIO_EXTENSIONS:
            path = os.path.join(folder, basename + ext)
            if os.path.isfile(path):
                return path
    return None

def init_sfx():
    global SFX

    SFX = {
        "button": make_sfx("button", 0.09, 0.42),
        "collect": make_sfx("collect", 0.18, 0.48),
        "bomb": make_sfx("bomb", 0.32, 0.58),
        "purchase": make_sfx("purchase", 0.30, 0.50),
        "select": make_sfx("select", 0.10, 0.35),
        "error": make_sfx("error", 0.18, 0.40),
        "spin": make_sfx("spin", 0.30, 0.25),
        "reward": make_sfx("reward", 0.45, 0.42),
        "shield": make_sfx("shield", 0.25, 0.42),
        "game_over": make_sfx("game_over", 0.55, 0.45),
        "bounce": make_sfx("bounce", 0.10, 0.40),
        "loss_life": make_sfx("loss_life", 0.25, 0.50),
    }

    cache = {}
    loaded, missing = [], []
    for event_name, basename in SFX_FILES.items():
        path = find_audio_file(basename)
        if not path:
            missing.append(basename)
            continue
        try:
            if path not in cache:
                cache[path] = pygame.mixer.Sound(path)
            SFX[event_name] = cache[path]
            loaded.append(f"{os.path.basename(path)} -> {event_name}")
        except Exception as e:
            print(f"Не удалось загрузить {path}: {e}")

init_sfx()

def play_sfx(name):
    if sound_volume <= 0:
        return
    sound = SFX.get(name)
    if sound:
        sound.set_volume(sound_volume)
        sound.play()

SCREEN_WIDTH = 520
SCREEN_HEIGHT = 1000
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bounce It Out")

def load_logo():
    possible_paths = [
        "logo.png",
        os.path.join("data", "logo.png"),
        os.path.join("all_music_and_SFX", "logo.png"),
        os.path.join(BASE_DIR, "logo.png"),
        os.path.join(BASE_DIR, "data", "logo.png"),
        os.path.join(BASE_DIR, "all_music_and_SFX", "logo.png")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                bounding_rect = img.get_bounding_rect()
                if bounding_rect.width > 0 and bounding_rect.height > 0:
                    img = img.subsurface(bounding_rect)
                w, h = img.get_size()
                target_w = 300
                target_h = int(h * (target_w / w))
                return pygame.transform.smoothscale(img, (target_w, target_h))
            except Exception as e:
                print(f"Ошибка загрузки логотипа {path}: {e}")
    return None

logo_image = load_logo()

def play_background_music():
    music_names = ["music_theme_3", "music_theme"]
    music_file = None
    for folder in AUDIO_DIRS:
        if not os.path.exists(folder):
            continue
        for name in music_names:
            for ext in AUDIO_EXTENSIONS:
                path = os.path.join(folder, name + ext)
                if os.path.isfile(path):
                    music_file = path
                    break
            if music_file:
                break
        if music_file:
            break

    if not music_file:
        for folder in AUDIO_DIRS:
            if not os.path.isdir(folder):
                continue
            for f in sorted(os.listdir(folder)):
                base, ext = os.path.splitext(f)
                if ext.lower() in AUDIO_EXTENSIONS and base.lower() not in SFX_BASENAMES:
                    music_file = os.path.join(folder, f)
                    break
            if music_file:
                break

    if music_file:
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Ошибка воспроизведения музыки: {e}")

play_background_music()

def get_emoji_font(size):
    for font_name in ["segoe ui emoji", "apple color emoji", "noto color emoji", "arial"]:
        try:
            f = pygame.font.SysFont(font_name, size)
            if f:
                return f
        except:
            continue
    return pygame.font.SysFont(None, size)

font_s = pygame.font.SysFont(None, 24)
font_m = pygame.font.SysFont(None, 32)
font_l = pygame.font.SysFont(None, 48)
font_emoji = get_emoji_font(38)

def draw_coin_icon(x, y, radius=14):
    pygame.draw.circle(screen, (255, 215, 0), (x, y), radius)
    pygame.draw.circle(screen, (218, 165, 32), (x, y), radius, 2)
    txt = font_s.render("$", True, (139, 69, 0))
    screen.blit(txt, (x - txt.get_width()//2, y - txt.get_height()//2))

def load_background_image(filename):
    possible_paths = [
        filename,
        os.path.join("data", filename),
        os.path.join("all_music_and_SFX", filename),
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "data", filename),
        os.path.join(BASE_DIR, "all_music_and_SFX", filename),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")
    return None

BACKGROUNDS = [
    {"name": "Классика", "name_en": "Classic", "image": load_background_image("main_theme.png"), "bg": (20, 20, 30), "coin": (255, 215, 0), "price": 0, "unlocked": True},
    {"name": "Неон", "name_en": "Neon", "image": load_background_image("neon_theme.png"), "bg": (10, 5, 20), "coin": (0, 255, 200), "price": 50, "unlocked": False},
    {"name": "Лес", "name_en": "Forest", "image": load_background_image("forest_theme.png"), "bg": (15, 30, 15), "coin": (255, 140, 0), "price": 100, "unlocked": False},
    {"name": "Космос", "name_en": "Space", "image": load_background_image("space_theme.png"), "bg": (5, 5, 10), "coin": (230, 230, 250), "price": 150, "unlocked": False},
    {"name": "Киберпанк", "name_en": "Cyberpunk", "image": load_background_image("cyber_punk_theme.png"), "bg": (35, 10, 25), "coin": (255, 0, 128), "price": 200, "unlocked": False},
    {"name": "Закат", "name_en": "Sunset", "image": load_background_image("zakat_theme.png"), "bg": (40, 20, 10), "coin": (255, 165, 0), "price": 250, "unlocked": False},
    {"name": "Золотая лихорадка", "name_en": "Gold Rush", "image": load_background_image("gold_theme.png"), "bg": (45, 32, 5), "coin": (255, 230, 120), "price": 0, "unlocked": False, "ach": True},
    {"name": "Платина", "name_en": "Platinum", "image": load_background_image("platinum_theme.png"), "bg": (30, 32, 42), "coin": (225, 230, 255), "price": 0, "unlocked": False, "ach": True},
]

PLATFORM_GRADIENTS = [
    {"name": "Неон-Блю", "name_en": "Neon Blue", "c1": (0, 200, 255), "c2": (0, 100, 200)},
    {"name": "Кибер-Рок", "name_en": "Cyber Rock", "c1": (255, 0, 128), "c2": (128, 0, 255)},
    {"name": "Эко-Грин", "name_en": "Eco Green", "c1": (100, 200, 50), "c2": (34, 139, 34)},
    {"name": "Золотой", "name_en": "Golden", "c1": (255, 215, 0), "c2": (255, 140, 0)},
    {"name": "Лава", "name_en": "Lava", "c1": (255, 90, 0), "c2": (170, 0, 0)},
    {"name": "Лёд", "name_en": "Ice", "c1": (190, 240, 255), "c2": (70, 150, 220)},
    {"name": "Сакура", "name_en": "Sakura", "c1": (255, 170, 210), "c2": (210, 80, 150)},
    {"name": "Изумруд", "name_en": "Emerald", "c1": (60, 255, 170), "c2": (0, 130, 85)},
    {"name": "Тьма", "name_en": "Void", "c1": (110, 110, 140), "c2": (25, 25, 45)},
    {"name": "Платина", "name_en": "Platinum", "c1": (240, 240, 255), "c2": (150, 150, 195)},
]
DEFAULT_UNLOCKED_PLATFORMS = [0, 1, 2, 3]
DEFAULT_BOOSTERS = {"shield": 1, "double_shield": 0, "speed": 0, "double_speed": 0, "extra_life": 0, "double_coins": 0}
DEFAULT_STATS = {
    "balls_caught": 0, "special_caught": 0, "bombs_blocked": 0,
    "best_classic": 0, "best_survival": 0, "survival_bounces": 0,
    "purchases": 0, "spins": 0, "magnets": 0,
    "games_played": 0, "play_time": 0.0, "coins_earned": 0,
}

def load_game_data():
    default_data = {
        "coins": 500,
        "high_score": 0,
        "survival_high_score": 0,
        "bg_idx": 0,
        "platform_idx": 0,
        "lang": "ru",
        "sound_vol": 1.0,
        "music_vol": 1.0,
        "last_spin": 0.0,
        "unlocked_bgs": [0],
        "boosters": dict(DEFAULT_BOOSTERS),
        "stats": dict(DEFAULT_STATS),
        "achievements": [],
        "unlocked_platforms": list(DEFAULT_UNLOCKED_PLATFORMS),
    }
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default_data.items():
                    if k not in data:
                        data[k] = v
                for sk, sv in default_data["stats"].items():
                    data["stats"].setdefault(sk, sv)
                for bk, bv in default_data["boosters"].items():
                    data["boosters"].setdefault(bk, bv)
                if "magnet" in data.get("boosters", {}):
                    del data["boosters"]["magnet"]
                unlocked_indices = data.get("unlocked_bgs", [0])
                for idx in unlocked_indices:
                    if 0 <= idx < len(BACKGROUNDS):
                        BACKGROUNDS[idx]["unlocked"] = True
                return data
        except Exception:
            return default_data
    return default_data

def save_game_data():
    unlocked_indices = [i for i, bg in enumerate(BACKGROUNDS) if bg["unlocked"]]
    data = {
        "coins": total_coins,
        "high_score": high_score,
        "survival_high_score": survival_high_score,
        "bg_idx": current_bg_idx,
        "platform_idx": current_platform_idx,
        "lang": current_lang,
        "sound_vol": sound_volume,
        "music_vol": music_volume,
        "last_spin": last_spin_time,
        "unlocked_bgs": unlocked_indices,
        "boosters": player_boosters,
        "stats": stats,
        "achievements": sorted(unlocked_achievements),
        "unlocked_platforms": sorted(unlocked_platforms),
    }
    try:
        os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Ошибка сохранения:", e)

saved_data = load_game_data()
total_coins = saved_data["coins"]
high_score = saved_data["high_score"]
survival_high_score = saved_data.get("survival_high_score", 0)
current_bg_idx = saved_data["bg_idx"]
current_platform_idx = saved_data["platform_idx"]
current_lang = saved_data["lang"]
sound_volume = saved_data["sound_vol"]
music_volume = saved_data["music_vol"]
last_spin_time = saved_data["last_spin"]
player_boosters = saved_data["boosters"]
stats = saved_data["stats"]
unlocked_achievements = set(saved_data["achievements"])
unlocked_platforms = set(saved_data["unlocked_platforms"]) | set(DEFAULT_UNLOCKED_PLATFORMS)

stats["best_classic"] = max(stats["best_classic"], high_score)
stats["best_survival"] = max(stats["best_survival"], survival_high_score)

pygame.mixer.music.set_volume(music_volume)

TEXTS = {
    "ru": {
        "play": "КЛАССИКА", "survival": "РЕЖИМ ВЫЖИВАНИЯ", "shop": "МАГАЗИН ФОНОВ", "platform_shop": "СТИЛЬ ПЛАТФОРМЫ", "boosters_btn": "БУСТЕРЫ", "wheel": "РУЛЕТКА", "settings": "НАСТРОЙКИ", "back": "НАЗАД",
        "score": "Счет", "best": "Рекорд", "survival_best": "Рекорд Выживания", "game_over": "ИГРА ОКОНЧЕНА", "restart": "Нажмите на экран для рестарта",
        "lang": "Язык: Русский", "sound_lbl": "Звуки", "music_lbl": "Музыка", "spin": "КРУТИТЬ", "cooldown": "Доступно через:", "reward": "Вы выиграли:",
        "equipped": "ВЫБРАНО", "select": "ВЫБРАТЬ", "buy": "КУПИТЬ", "no_money": "Мало монет!", "start_game": "НАЧАТЬ РАУНД", "prep_title": "ВЫБОР БУСТЕРОВ",
        "b_shield": "Щит", "b_dshield": "Двойной щит", "b_speed": "Ускорение", "b_dspeed": "Турбо ускорение", "lives": "Жизни",
        "achievements": "ДОСТИЖЕНИЯ", "ach_unlocked": "Достижение получено!", "new_platform": "Новый цвет платформы",
        "locked": "Закрыто", "available": "Доступно", "on_run": "Включён на раунд", "off": "Выключен",
        "bought": "Куплено", "pcs": "шт.", "sec": "сек", "sec_short": "с",
        "cooldown_active": "Рулетка ещё не готова!", "menu": "Меню",
        "stats_btn": "СТАТИСТИКА", "new_record": "НОВЫЙ РЕКОРД!", "paused": "ПАУЗА", "resume": "ПРОДОЛЖИТЬ", "to_menu": "В МЕНЮ",
        "reset_progress": "СБРОС ПРОГРЕССА", "reset_title": "Сбросить прогресс?",
        "reset_warn1": "Монеты, рекорды, покупки и достижения", "reset_warn2": "будут удалены без возможности вернуть.", "reset_warn3": "Язык и громкость сохранятся.",
        "reset_yes": "ДА, СБРОСИТЬ", "reset_no": "ОТМЕНА", "new_bg": "Новый фон",
        "b_life": "Доп. жизнь", "b_dcoins": "Двойные монеты",
        "d_shield": "Блокирует 1 бомбу", "d_double_shield": "Блокирует 2 бомбы",
        "d_speed": "Предметы падают в 1.4 раза быстрее", "d_double_speed": "Предметы падают в 2 раза быстрее",
        "d_extra_life": "+1 жизнь в режиме выживания", "d_double_coins": "Монеты x2 на один раунд",
        "time_fmt": "{h} ч {m} мин",
        "st_balls": "Поймано мячей", "st_games": "Сыграно раундов", "st_time": "Время в игре",
        "st_best_classic": "Рекорд (классика)", "st_best_survival": "Рекорд (выживание)", "st_bounces": "Отбито мячей",
        "st_blocked": "Бомб заблокировано", "st_coins": "Монет заработано", "st_purchases": "Покупок",
        "st_spins": "Прокруток рулетки", "st_magnets": "Магнитов подобрано", "st_ach": "Достижения"
    },
    "en": {
        "play": "CLASSIC", "survival": "SURVIVAL MODE", "shop": "BACKGROUND SHOP", "platform_shop": "PLATFORM STYLE", "boosters_btn": "BOOSTERS", "wheel": "WHEEL", "settings": "SETTINGS", "back": "BACK",
        "score": "Score", "best": "High Score", "survival_best": "Survival High Score", "game_over": "GAME OVER", "restart": "Tap screen to Restart",
        "lang": "Language: English", "sound_lbl": "Sound", "music_lbl": "Music", "spin": "SPIN", "cooldown": "Available in:", "reward": "You won:",
        "equipped": "EQUIPPED", "select": "SELECT", "buy": "BUY", "no_money": "Not enough coins!", "start_game": "START RUN", "prep_title": "SELECT BOOSTERS",
        "b_shield": "Shield", "b_dshield": "Double Shield", "b_speed": "Speed", "b_dspeed": "Turbo Speed", "lives": "Lives",
        "achievements": "ACHIEVEMENTS", "ach_unlocked": "Achievement unlocked!", "new_platform": "New platform color",
        "locked": "Locked", "available": "Available", "on_run": "Enabled for this run", "off": "Disabled",
        "bought": "Purchased", "pcs": "pcs", "sec": "sec", "sec_short": "s",
        "cooldown_active": "The wheel isn't ready yet!", "menu": "Menu",
        "stats_btn": "STATISTICS", "new_record": "NEW RECORD!", "paused": "PAUSED", "resume": "RESUME", "to_menu": "MAIN MENU",
        "reset_progress": "RESET PROGRESS", "reset_title": "Reset progress?",
        "reset_warn1": "Coins, records, purchases and achievements", "reset_warn2": "will be deleted permanently.", "reset_warn3": "Language and volume are kept.",
        "reset_yes": "YES, RESET", "reset_no": "CANCEL", "new_bg": "New background",
        "b_life": "Extra Life", "b_dcoins": "Double Coins",
        "d_shield": "Blocks 1 bomb", "d_double_shield": "Blocks 2 bombs",
        "d_speed": "Items fall 1.4x faster", "d_double_speed": "Items fall 2x faster",
        "d_extra_life": "+1 life in Survival mode", "d_double_coins": "Coins x2 for one round",
        "time_fmt": "{h}h {m}m",
        "st_balls": "Balls caught", "st_games": "Rounds played", "st_time": "Time played",
        "st_best_classic": "Best (Classic)", "st_best_survival": "Best (Survival)", "st_bounces": "Balls bounced",
        "st_blocked": "Bombs blocked", "st_coins": "Coins earned", "st_purchases": "Purchases",
        "st_spins": "Wheel spins", "st_magnets": "Magnets collected", "st_ach": "Achievements"
    }
}

wheel_reward_text = ""
shop_message = ""
selected_run_boosters = {k: False for k in DEFAULT_BOOSTERS}

ACHIEVEMENTS = [
    {"id": "first_catch", "icon": "⚽", "key": "balls_caught", "target": 1, "reward": 20,
     "ru": ("Первый улов", "Поймай 1 мяч"), "en": ("First Catch", "Catch 1 ball")},
    {"id": "collector", "icon": "🧺", "key": "balls_caught", "target": 500, "reward": 150, "platform": 5,
     "ru": ("Коллекционер", "Поймай 500 мячей за всё время"), "en": ("Collector", "Catch 500 balls in total")},
    {"id": "master", "icon": "🏆", "key": "balls_caught", "target": 2000, "reward": 400,
     "ru": ("Мастер ловли", "Поймай 2000 мячей за всё время"), "en": ("Catch Master", "Catch 2000 balls in total")},
    {"id": "warmup", "icon": "🔥", "key": "best_classic", "target": 50, "reward": 50,
     "ru": ("Разминка", "Набери 50 очков за раунд в классике"), "en": ("Warm-Up", "Score 50 in a Classic round")},
    {"id": "pro", "icon": "💪", "key": "best_classic", "target": 150, "reward": 200, "platform": 4,
     "ru": ("Профи", "Набери 150 очков за раунд в классике"), "en": ("Pro", "Score 150 in a Classic round")},
    {"id": "legend", "icon": "👑", "key": "best_classic", "target": 300, "reward": 500, "platform": 8,
     "ru": ("Легенда", "Набери 300 очков за раунд в классике"), "en": ("Legend", "Score 300 in a Classic round")},
    {"id": "rare", "icon": "🥎", "key": "special_caught", "target": 10, "reward": 100,
     "ru": ("Редкая находка", "Поймай 10 редких мячей"), "en": ("Rare Find", "Catch 10 rare balls")},
    {"id": "shield", "icon": "🛡️", "key": "bombs_blocked", "target": 5, "reward": 100, "platform": 6,
     "ru": ("Щит спас!", "Заблокируй щитом 5 бомб"), "en": ("Shield Saved Me!", "Block 5 bombs with a shield")},
    {"id": "first_bounce", "icon": "🏀", "key": "survival_bounces", "target": 1, "reward": 20,
     "ru": ("Первый отскок", "Отбей мяч в режиме выживания"), "en": ("First Bounce", "Bounce a ball in Survival mode")},
    {"id": "juggler", "icon": "🤹", "key": "survival_bounces", "target": 500, "reward": 200, "platform": 7,
     "ru": ("Жонглёр", "Отбей 500 мячей в выживании"), "en": ("Juggler", "Bounce 500 balls in Survival mode")},
    {"id": "survivor", "icon": "❤️", "key": "best_survival", "target": 100, "reward": 250,
     "ru": ("Живучий", "Набери 100 очков в выживании"), "en": ("Survivor", "Score 100 in Survival mode")},
    {"id": "rich", "icon": "💰", "key": "coins_balance", "target": 5000, "reward": 300, "background": 6,
     "ru": ("Богач", "Накопи 5000 монет на балансе"), "en": ("Moneybags", "Have 5000 coins at once")},
    {"id": "shopper", "icon": "🛍️", "key": "purchases", "target": 10, "reward": 100,
     "ru": ("Шопоголик", "Соверши 10 покупок"), "en": ("Shopaholic", "Make 10 purchases")},
    {"id": "fashion", "icon": "🎨", "key": "bgs_unlocked", "target": None, "reward": 400,
     "ru": ("Модник", "Купи все фоны в магазине"), "en": ("Trendsetter", "Buy all shop backgrounds")},
    {"id": "lucky", "icon": "🎰", "key": "spins", "target": 5, "reward": 80,
     "ru": ("Счастливчик", "Покрути рулетку 5 раз"), "en": ("Lucky One", "Spin the wheel 5 times")},
    {"id": "magnet", "icon": "🧲", "key": "magnets", "target": 10, "reward": 100,
     "ru": ("Магнитный человек", "Подбери 10 магнитов"), "en": ("Magnet Man", "Collect 10 magnets")},
    {"id": "platinum", "icon": "💎", "key": "ach_others", "target": None, "reward": 1000, "platform": 9, "background": 7,
     "ru": ("Платина", "Получи все остальные достижения"), "en": ("Platinum", "Unlock all other achievements")},
]
PLATFORM_UNLOCKERS = {a["platform"]: a for a in ACHIEVEMENTS if a.get("platform") is not None}
BG_UNLOCKERS = {a["background"]: a for a in ACHIEVEMENTS if a.get("background") is not None}

ach_toasts = []
TOAST_TIME = 3.8
ACH_ROW_H = 92
ACH_TOP = 115
ACH_BOTTOM = 880

def lname(d):
    return d.get("name_en", d["name"]) if current_lang == "en" else d["name"]

def ach_text(a):
    return a[current_lang]

def get_progress(a):
    key = a["key"]
    if key == "coins_balance":
        return total_coins
    if key == "bgs_unlocked":
        return sum(1 for b in BACKGROUNDS if b["unlocked"] and not b.get("ach"))
    if key == "ach_others":
        return sum(1 for x in ACHIEVEMENTS if x["id"] != "platinum" and x["id"] in unlocked_achievements)
    return stats.get(key, 0)

def get_target(a):
    if a["key"] == "bgs_unlocked":
        return sum(1 for b in BACKGROUNDS if not b.get("ach"))
    if a["key"] == "ach_others":
        return len(ACHIEVEMENTS) - 1
    return a["target"]

def check_achievements():
    global total_coins
    changed = False
    for a in ACHIEVEMENTS:
        if a["id"] in unlocked_achievements:
            continue
        if get_progress(a) >= get_target(a):
            unlocked_achievements.add(a["id"])
            total_coins += a["reward"]
            if a.get("platform") is not None:
                unlocked_platforms.add(a["platform"])
            if a.get("background") is not None:
                BACKGROUNDS[a["background"]]["unlocked"] = True
            ach_toasts.append({"ach": a, "t": 0.0})
            changed = True
    if changed:
        play_sfx("reward")
        save_game_data()

def draw_achievement_toast(dt):
    if not ach_toasts:
        return
    cur = ach_toasts[0]
    cur["t"] += min(dt, 0.1)
    tm = cur["t"]
    if tm >= TOAST_TIME:
        ach_toasts.pop(0)
        return
    slide = 0.35
    if tm < slide:
        k = tm / slide
    elif tm > TOAST_TIME - slide:
        k = (TOAST_TIME - tm) / slide
    else:
        k = 1.0
    k = 1 - (1 - k) ** 3
    a = cur["ach"]
    tr = TEXTS[current_lang]
    extras = []
    if a.get("platform") is not None:
        extras.append(f"{tr['new_platform']}: {lname(PLATFORM_GRADIENTS[a['platform']])}")
    if a.get("background") is not None:
        extras.append(f"{tr['new_bg']}: {lname(BACKGROUNDS[a['background']])}")
    h = 88 + 20 * max(0, len(extras) - 1)
    y = int(-h + (h + 105) * k)
    rect = pygame.Rect(30, y, SCREEN_WIDTH - 60, h)
    bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(bg, (30, 30, 55, 240), bg.get_rect(), border_radius=14)
    screen.blit(bg, rect.topleft)
    pygame.draw.rect(screen, (255, 215, 0), rect, 3, border_radius=14)

    a = cur["ach"]
    tr = TEXTS[current_lang]
    icon = font_emoji.render(a["icon"], True, (255, 255, 255))
    screen.blit(icon, (rect.x + 16, rect.centery - icon.get_height() // 2))
    screen.blit(font_s.render(tr["ach_unlocked"], True, (255, 215, 0)), (rect.x + 75, rect.y + 10))
    screen.blit(font_m.render(ach_text(a)[0], True, (255, 255, 255)), (rect.x + 75, rect.y + 30))
    draw_coin_icon(rect.x + 86, rect.y + 68, 10)
    line = f"+{a['reward']}"
    if extras:
        line += f"    {extras[0]}"
    screen.blit(font_s.render(line, True, (220, 220, 240)), (rect.x + 102, rect.y + 60))
    for j, ex in enumerate(extras[1:]):
        screen.blit(font_s.render(ex, True, (220, 220, 240)), (rect.x + 102, rect.y + 80 + j * 20))

def ach_max_scroll():
    return max(0, len(ACHIEVEMENTS) * ACH_ROW_H - (ACH_BOTTOM - ACH_TOP) + 10)

def draw_achievements_screen(scroll):
    tr = TEXTS[current_lang]
    title = font_m.render(tr["achievements"], True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 35))
    cnt = font_s.render(f"{len(unlocked_achievements)}/{len(ACHIEVEMENTS)}", True, (255, 215, 0))
    screen.blit(cnt, (SCREEN_WIDTH // 2 - cnt.get_width() // 2, 72))
    draw_coin_display(25, 25, total_coins)

    screen.set_clip(pygame.Rect(0, ACH_TOP, SCREEN_WIDTH, ACH_BOTTOM - ACH_TOP))
    for i, a in enumerate(ACHIEVEMENTS):
        y = ACH_TOP + i * ACH_ROW_H - scroll
        if y > ACH_BOTTOM or y + 82 < ACH_TOP:
            continue
        rect = pygame.Rect(30, y, 450, 82)
        done = a["id"] in unlocked_achievements
        pygame.draw.rect(screen, (45, 85, 55) if done else (45, 45, 72), rect, border_radius=12)
        pygame.draw.rect(screen, (255, 215, 0) if done else (110, 110, 150), rect, 2, border_radius=12)

        icon = font_emoji.render(a["icon"], True, (255, 255, 255))
        if not done:
            icon.set_alpha(90)
        screen.blit(icon, (rect.x + 14, rect.centery - icon.get_height() // 2))

        name, desc = ach_text(a)
        screen.blit(font_m.render(name, True, (255, 255, 255) if done else (190, 190, 210)), (rect.x + 68, rect.y + 8))
        screen.blit(font_s.render(desc, True, (200, 200, 220)), (rect.x + 68, rect.y + 34))

        target = get_target(a)
        prog = target if done else min(get_progress(a), target)
        bar = pygame.Rect(rect.x + 68, rect.y + 60, 190, 10)
        pygame.draw.rect(screen, (30, 30, 50), bar, border_radius=5)
        fw = int(bar.width * prog / target) if target else 0
        if fw > 0:
            pygame.draw.rect(screen, (255, 215, 0) if done else (0, 200, 255),
                             (bar.x, bar.y, fw, bar.height), border_radius=5)
        screen.blit(font_s.render(f"{prog}/{target}", True, (220, 220, 240)), (bar.right + 10, rect.y + 57))

        draw_coin_icon(rect.right - 70, rect.y + 18, 10)
        screen.blit(font_s.render(f"+{a['reward']}", True, (255, 215, 0)), (rect.right - 55, rect.y + 10))
        if a.get("platform") is not None:
            p = PLATFORM_GRADIENTS[a["platform"]]
            sw = pygame.Rect(rect.right - 90, rect.y + 50, 80, 16)
            pygame.draw.rect(screen, p["c1"], (sw.x, sw.y, 40, sw.height), border_top_left_radius=6, border_bottom_left_radius=6)
            pygame.draw.rect(screen, p["c2"], (sw.x + 40, sw.y, 40, sw.height), border_top_right_radius=6, border_bottom_right_radius=6)
            pygame.draw.rect(screen, (255, 255, 255), sw, 1, border_radius=6)
        if a.get("background") is not None:
            bgd = BACKGROUNDS[a["background"]]
            both = a.get("platform") is not None
            bh = 12 if both else 16
            bsw = pygame.Rect(rect.right - 90, rect.y + (31 if both else 50), 80, bh)
            pygame.draw.rect(screen, bgd["bg"], (bsw.x, bsw.y, 40, bh), border_top_left_radius=6, border_bottom_left_radius=6)
            pygame.draw.rect(screen, bgd["coin"], (bsw.x + 40, bsw.y, 40, bh), border_top_right_radius=6, border_bottom_right_radius=6)
            pygame.draw.rect(screen, (255, 255, 255), bsw, 1, border_radius=6)
    screen.set_clip(None)

    mx_scroll = ach_max_scroll()
    if mx_scroll > 0:
        view_h = ACH_BOTTOM - ACH_TOP
        thumb_h = max(30, int(view_h * view_h / (view_h + mx_scroll)))
        thumb_y = ACH_TOP + int((view_h - thumb_h) * scroll / mx_scroll)
        pygame.draw.rect(screen, (60, 60, 90), (498, ACH_TOP, 5, view_h), border_radius=3)
        pygame.draw.rect(screen, (150, 150, 200), (498, thumb_y, 5, thumb_h), border_radius=3)

def platform_card_rect(i):
    return pygame.Rect(40 + (i % 2) * 240, 130 + (i // 2) * 135, 220, 120)

def draw_platform_cards():
    tr = TEXTS[current_lang]
    for i, p in enumerate(PLATFORM_GRADIENTS):
        rect = platform_card_rect(i)
        owned = i in unlocked_platforms
        sel = (i == current_platform_idx)
        col = (0, 150, 100) if sel else ((60, 60, 90) if owned else (40, 40, 55))
        pygame.draw.rect(screen, col, rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255) if sel else (150, 150, 150), rect, 2, border_radius=12)
        screen.blit(font_m.render(lname(p), True, (255, 255, 255) if owned else (150, 150, 170)), (rect.x + 15, rect.y + 12))

        sw = pygame.Rect(rect.x + 15, rect.y + 48, 190, 26)
        half = sw.width // 2
        pygame.draw.rect(screen, p["c1"], (sw.x, sw.y, half, sw.height), border_top_left_radius=6, border_bottom_left_radius=6)
        pygame.draw.rect(screen, p["c2"], (sw.x + half, sw.y, sw.width - half, sw.height), border_top_right_radius=6, border_bottom_right_radius=6)
        if owned:
            label = tr["equipped"] if sel else tr["select"]
            screen.blit(font_s.render(label, True, (150, 255, 150) if sel else (200, 200, 200)), (rect.x + 15, rect.y + 88))
        else:
            ov = pygame.Surface(sw.size, pygame.SRCALPHA)
            pygame.draw.rect(ov, (0, 0, 0, 160), ov.get_rect(), border_radius=6)
            screen.blit(ov, sw.topleft)
            screen.blit(font_s.render(tr["locked"], True, (255, 120, 120)), (rect.x + 15, rect.y + 82))
            ach = PLATFORM_UNLOCKERS.get(i)
            if ach:
                screen.blit(font_s.render(ach_text(ach)[0], True, (255, 215, 0)), (rect.x + 15, rect.y + 98))

# --- Система частиц ---
particles = []

def add_particles(x, y, color, count=12):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "color": color,
            "radius": random.randint(3, 6),
            "alpha": 1.0
        })

def update_and_draw_particles(dt):
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["alpha"] -= dt * 2.5
        if p["alpha"] <= 0:
            particles.remove(p)
        else:
            color = (*p["color"], int(p["alpha"] * 255))
            surf = pygame.Surface((p["radius"] * 2, p["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (p["radius"], p["radius"]), p["radius"])
            screen.blit(surf, (int(p["x"] - p["radius"]), int(p["y"] - p["radius"])))

class Player:
    def __init__(self):
        self.width = 125
        self.height = 26
        self.x = float(SCREEN_WIDTH // 2 - self.width // 2)
        self.y = SCREEN_HEIGHT - 120
        self.rect = pygame.Rect(int(self.x), self.y, self.width, self.height)
        self.shield_hits = 0
        self.magnet_timer = 0.0
        self.speed_multiplier = 1.0

    def move_to(self, target_x):
        desired_x = target_x - self.width // 2
        desired_x = max(0, min(desired_x, SCREEN_WIDTH - self.width))
        self.x += (desired_x - self.x) * 0.45
        self.rect.x = int(self.x)

    def draw(self):
        grad = PLATFORM_GRADIENTS[current_platform_idx]
        half_w = self.width // 2
        left_rect = pygame.Rect(self.rect.x, self.rect.y, half_w, self.height)
        right_rect = pygame.Rect(self.rect.x + half_w, self.rect.y, self.width - half_w, self.height)
        
        pygame.draw.rect(screen, grad["c1"], left_rect, border_top_left_radius=12, border_bottom_left_radius=12)
        pygame.draw.rect(screen, grad["c2"], right_rect, border_top_right_radius=12, border_bottom_right_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=12)

        if self.shield_hits == 1:
            pygame.draw.rect(screen, (0, 150, 255), self.rect.inflate(8, 8), 3, border_radius=14)
        elif self.shield_hits >= 2:
            pygame.draw.rect(screen, (255, 215, 0), self.rect.inflate(10, 10), 4, border_radius=16)

SPECIAL_KINDS = ("magnet", "gold", "clock", "ice", "heart")
SPECIAL_EMOJI = {"magnet": "🧲", "gold": "", "clock": "⏰", "ice": "🧊", "heart": "❤️"}

class FallingItem:
    def __init__(self, score, speed_mult, is_survival=False, kind=None, x=None):
        self.radius = 22
        self.x = x if x is not None else random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = -40
        base_speed = random.randint(5, 8)
        self.speed = (base_speed + (score // 20)) * speed_mult
        self.vy = self.speed
        self.vx = 0.0
        self.bounces = 0
        self.age = 0.0
        self.zigzag = False
        self.base_x = self.x
        self.kind = "ball"
        self.is_bomb = False
        self.score_val = 0
        self.coin_val = 0

        if kind in SPECIAL_KINDS:
            self.kind = kind
            self.emoji = SPECIAL_EMOJI[kind]
            if kind == "gold":
                self.score_val = 3
                self.coin_val = 5
        elif is_survival:
            chosen = random.choice([
                {"emoji": "⚽", "score": 1, "coins": 1},
                {"emoji": "🏀", "score": 1, "coins": 1},
                {"emoji": "🏐", "score": 1, "coins": 1},
                {"emoji": "⚾", "score": 3, "coins": 2},
            ])
            self.emoji = chosen["emoji"]
            self.score_val = chosen["score"]
            self.coin_val = chosen["coins"]
        else:
            item_types = [
                {"emoji": "⚽", "score": 1, "coins": 1, "weight": 35, "is_bomb": False},
                {"emoji": "🏀", "score": 1, "coins": 1, "weight": 30, "is_bomb": False},
                {"emoji": "🏐", "score": 1, "coins": 1, "weight": 20, "is_bomb": False},
                {"emoji": "⚾", "score": 3, "coins": 2, "weight": 5,  "is_bomb": False},
                {"emoji": "🥎", "score": 5, "coins": 3, "weight": 2,  "is_bomb": False},
                {"emoji": "💣", "score": 0, "coins": 0, "weight": 38, "is_bomb": True},
            ]
            total_weight = sum(it["weight"] for it in item_types)
            r = random.uniform(0, total_weight)
            current = 0
            chosen = item_types[0]
            for it in item_types:
                current += it["weight"]
                if r <= current:
                    chosen = it
                    break
            self.emoji = chosen["emoji"]
            self.score_val = chosen["score"]
            self.coin_val = chosen["coins"]
            self.is_bomb = chosen["is_bomb"]
            if self.is_bomb:
                self.kind = "bomb"
                if score >= 30 and random.random() < 0.45:
                    self.zigzag = True
                    self.zz_amp = random.randint(40, 80)
                    self.zz_speed = random.uniform(0.06, 0.10)
        self.is_magnet = (self.kind == "magnet")

    def update(self, speed_mult, is_survival=False, scale=1.0):
        if scale <= 0:
            return
        self.age += scale
        if is_survival:
            self.y += self.vy * scale
            self.x += self.vx * scale
            if self.x - self.radius < 0:
                self.x = self.radius
                self.vx = -self.vx
            elif self.x + self.radius > SCREEN_WIDTH:
                self.x = SCREEN_WIDTH - self.radius
                self.vx = -self.vx
            if self.y < -40:
                self.y = -40
                self.vy = abs(self.vy)
                self.vx = random.uniform(-2.0, 2.0)
        else:
            self.y += self.speed * scale
            if self.zigzag:
                self.x = max(self.radius, min(SCREEN_WIDTH - self.radius,
                                              self.base_x + self.zz_amp * math.sin(self.age * self.zz_speed)))

    def draw(self):
        cx, cy = int(self.x), int(self.y)
        if self.kind == "gold":
            pygame.draw.circle(screen, (255, 200, 0), (cx, cy), self.radius)
            pygame.draw.circle(screen, (200, 140, 0), (cx, cy), self.radius, 3)
            pygame.draw.circle(screen, (255, 245, 170), (cx - 8, cy - 9), 6)
            lbl = font_s.render("x5", True, (120, 70, 0))
            screen.blit(lbl, (cx - lbl.get_width() // 2 + 2, cy - lbl.get_height() // 2 + 3))
            return
        item_surf = font_emoji.render(self.emoji, True, (255, 255, 255))
        screen.blit(item_surf, (cx - item_surf.get_width() // 2, cy - item_surf.get_height() // 2))

def pick_special_classic():
    r = random.random()
    acc = 0.0
    for kind, p in (("magnet", 0.04), ("gold", 0.03), ("clock", 0.03), ("ice", 0.03)):
        acc += p
        if r < acc:
            return kind
    return None

def spawn_group(score, speed_mult):
    x0 = random.randint(40, SCREEN_WIDTH - 40 - 200)
    while True:
        group = [FallingItem(score, speed_mult, False, kind="ball", x=x0 + j * 100) for j in range(3)]
        if sum(1 for g in group if g.kind == "bomb") <= 2:
            break
    spd = group[0].speed
    for g in group:
        g.speed = spd
        g.vy = spd
        g.zigzag = False
    return group

def earn_coins(n):
    global total_coins
    total_coins += n
    stats["coins_earned"] += n

class Run:
    def __init__(self, survival=False):
        self.survival = survival
        self.items = []
        self.score = 0
        self.lives = 3
        self.max_lives = 5
        self.over = False
        self.over_time = 0.0
        self.paused = False
        self.spawn_timer = 0.0
        self.special_timer = random.uniform(6, 10)
        self.coin_mult = 1
        self.freeze = 0.0
        self.slow = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.new_record = False
        self.fx_timer = 0.0
        self.bounce_count = 0

CLASSIC_BOOSTERS = ["shield", "double_shield", "speed", "double_speed", "double_coins"]
SURVIVAL_BOOSTERS = ["extra_life", "double_coins"]
SHOP_BOOSTERS = ["shield", "double_shield", "speed", "double_speed", "extra_life", "double_coins"]
BOOSTER_NAME_KEY = {"shield": "b_shield", "double_shield": "b_dshield", "speed": "b_speed",
                    "double_speed": "b_dspeed", "extra_life": "b_life", "double_coins": "b_dcoins"}
BOOSTER_PRICE = 200
MENU_ENTRIES = ["play", "survival", "shop", "platform_shop", "boosters_btn", "wheel",
                "achievements", "stats_btn", "settings"]

def btn_rect(y, height=55, width=380):
    return pygame.Rect(SCREEN_WIDTH // 2 - width // 2, y, width, height)

def menu_rect(i):
    return btn_rect(330 + i * 64, 52)

def bg_card_rect(i):
    return pygame.Rect(40, 95 + i * 95, 440, 85)

def booster_card_rect(i):
    return pygame.Rect(50, 110 + i * 125, 420, 100)

def prep_card_rect(i):
    return pygame.Rect(40, 110 + i * 115, 440, 100)

def draw_button(text, y, height=55, width=380, color=(50, 50, 80), border=(100, 100, 150)):
    rect = btn_rect(y, height, width)
    pygame.draw.rect(screen, color, rect, border_radius=14)
    pygame.draw.rect(screen, border, rect, 2, border_radius=14)
    txt = font_m.render(text, True, (255, 255, 255))
    screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
    return rect

def draw_slider(label, y, value):
    margin = 60
    slider_w = SCREEN_WIDTH - margin * 2
    screen.blit(font_m.render(f"{label}: {int(value * 100)}%", True, (255, 255, 255)), (margin, y))
    track_rect = pygame.Rect(margin, y + 35, slider_w, 14)
    pygame.draw.rect(screen, (60, 60, 90), track_rect, border_radius=7)

    fill_width = int(slider_w * value)
    fill_rect = pygame.Rect(margin, y + 35, fill_width, 14)
    pygame.draw.rect(screen, (0, 200, 255), fill_rect, border_radius=7)

    handle_x = margin + fill_width
    pygame.draw.circle(screen, (255, 255, 255), (handle_x, y + 42), 12)
    return track_rect

def draw_coin_display(x, y, count):
    draw_coin_icon(x + 14, y + 14, 14)
    txt = font_m.render(f": {count}", True, (255, 255, 255))
    screen.blit(txt, (x + 36, y + 2))

def draw_background():
    bg = BACKGROUNDS[current_bg_idx]
    if bg["image"]:
        screen.blit(bg["image"], (0, 0))
    else:
        screen.fill(bg["bg"])

def reset_progress():
    global total_coins, high_score, survival_high_score, current_bg_idx, current_platform_idx, last_spin_time
    total_coins = 500
    high_score = 0
    survival_high_score = 0
    current_bg_idx = 0
    current_platform_idx = 0
    last_spin_time = 0.0
    for i, b in enumerate(BACKGROUNDS):
        b["unlocked"] = (i == 0)
    player_boosters.clear()
    player_boosters.update(DEFAULT_BOOSTERS)
    stats.clear()
    stats.update(DEFAULT_STATS)
    unlocked_achievements.clear()
    unlocked_platforms.clear()
    unlocked_platforms.update(DEFAULT_UNLOCKED_PLATFORMS)
    ach_toasts.clear()
    for k in selected_run_boosters:
        selected_run_boosters[k] = False
    save_game_data()

def format_play_time(sec):
    sec = int(sec)
    return TEXTS[current_lang]["time_fmt"].format(h=sec // 3600, m=(sec % 3600) // 60)

def draw_stats_screen():
    tr = TEXTS[current_lang]
    title = font_m.render(tr["stats_btn"], True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
    draw_coin_display(25, 25, total_coins)
    rows = [
        (tr["st_balls"], stats["balls_caught"]),
        (tr["st_games"], stats["games_played"]),
        (tr["st_time"], format_play_time(stats["play_time"])),
        (tr["st_best_classic"], max(high_score, stats["best_classic"])),
        (tr["st_best_survival"], max(survival_high_score, stats["best_survival"])),
        (tr["st_bounces"], stats["survival_bounces"]),
        (tr["st_blocked"], stats["bombs_blocked"]),
        (tr["st_coins"], stats["coins_earned"]),
        (tr["st_purchases"], stats["purchases"]),
        (tr["st_spins"], stats["spins"]),
        (tr["st_magnets"], stats["magnets"]),
        (tr["st_ach"], f"{len(unlocked_achievements)}/{len(ACHIEVEMENTS)}"),
    ]
    for i, (label, val) in enumerate(rows):
        rect = pygame.Rect(40, 110 + i * 58, 440, 48)
        pygame.draw.rect(screen, (45, 45, 72), rect, border_radius=10)
        pygame.draw.rect(screen, (110, 110, 150), rect, 2, border_radius=10)
        screen.blit(font_m.render(label, True, (230, 230, 245)), (rect.x + 16, rect.centery - 8))
        v = font_m.render(str(val), True, (255, 215, 0))
        screen.blit(v, (rect.right - 16 - v.get_width(), rect.centery - 8))

def draw_effect(x, y, emoji, seconds):
    icon = font_emoji.render(emoji, True, (255, 255, 255))
    screen.blit(icon, (x, y))
    txt = font_s.render(f"{int(math.ceil(seconds))}{TEXTS[current_lang]['sec_short']}", True, (255, 215, 0))
    screen.blit(txt, (x + icon.get_width() + 4, y + icon.get_height() // 2 - txt.get_height() // 2))
    return x + icon.get_width() + 4 + txt.get_width() + 18

dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
dim_surf.fill((0, 0, 0, 160))
flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
flash_surf.fill((255, 30, 30))
ice_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
ice_surf.fill((150, 220, 255))

def main():
    global current_lang, sound_volume, music_volume, current_bg_idx, current_platform_idx
    global total_coins, high_score, survival_high_score, last_spin_time, wheel_reward_text, shop_message

    clock = pygame.time.Clock()
    state = "menu"

    player = Player()
    run = Run(False)
    is_dragging = False
    prep_survival = False
    ach_scroll = 0
    ach_drag = False
    ach_drag_y = 0
    ach_drag_scroll = 0

    def set_paused(flag):
        run.paused = flag
        if flag:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    def start_run(survival, use_boosters):
        nonlocal run
        run = Run(survival)
        stats["games_played"] += 1
        player.shield_hits = 0
        player.speed_multiplier = 1.0
        player.magnet_timer = 0.0
        if use_boosters:
            def use(key):
                if selected_run_boosters[key] and player_boosters[key] > 0:
                    player_boosters[key] -= 1
                    if player_boosters[key] <= 0:
                        selected_run_boosters[key] = False
                    return True
                return False
            if not survival:
                if use("double_shield"):
                    player.shield_hits = 2
                elif use("shield"):
                    player.shield_hits = 1
                if use("double_speed"):
                    player.speed_multiplier = 2.0
                elif use("speed"):
                    player.speed_multiplier = 1.4
            else:
                if use("extra_life"):
                    run.lives = min(run.max_lives, run.lives + 1)
            if use("double_coins"):
                run.coin_mult = 2
            save_game_data()
        if survival:
            run.items.append(FallingItem(0, 1.0, True))

    def end_run():
        global high_score, survival_high_score
        run.over = True
        run.over_time = 0.0
        play_sfx("game_over")
        prev = survival_high_score if run.survival else high_score
        if run.score > prev:
            run.new_record = True
            if run.survival:
                survival_high_score = run.score
            else:
                high_score = run.score
            play_sfx("reward")
            for _ in range(3):
                add_particles(random.randint(100, SCREEN_WIDTH - 100), random.randint(180, 420), (255, 215, 0), 25)
        save_game_data()

    def collect_special(item):
        kind = item.kind
        colors = {"magnet": (255, 215, 0), "gold": (255, 200, 0), "clock": (255, 255, 120),
                  "ice": (150, 220, 255), "heart": (255, 80, 120)}
        add_particles(item.x, item.y, colors[kind], 14)
        if kind == "magnet":
            play_sfx("collect")
            player.magnet_timer = 6.0
            stats["magnets"] += 1
        elif kind == "gold":
            play_sfx("collect")
            run.score += item.score_val
            earn_coins(item.coin_val * run.coin_mult)
            stats["balls_caught"] += 1
        elif kind == "clock":
            play_sfx("select")
            run.slow = 5.0
        elif kind == "ice":
            play_sfx("shield")
            run.freeze = 3.0
        elif kind == "heart":
            play_sfx("purchase")
            run.lives = min(run.max_lives, run.lives + 1)

    while True:
        t = TEXTS[current_lang]
        draw_background()
        dt = min(clock.tick(60) / 1000.0, 0.1)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()

            if event.type in (getattr(pygame, "WINDOWFOCUSLOST", -1), getattr(pygame, "WINDOWMINIMIZED", -2)):
                if state == "game" and not run.over and not run.paused:
                    set_paused(True)

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for i, key in enumerate(MENU_ENTRIES):
                        if not menu_rect(i).collidepoint(mx, my):
                            continue
                        play_sfx("button")
                        if key == "play":
                            prep_survival = False
                            state = "pre_game"
                        elif key == "survival":
                            prep_survival = True
                            state = "pre_game"
                        elif key == "shop":
                            shop_message = ""
                            state = "shop"
                        elif key == "platform_shop":
                            state = "platform_shop"
                        elif key == "boosters_btn":
                            state = "boosters"
                        elif key == "wheel":
                            state = "wheel"
                        elif key == "achievements":
                            ach_scroll = 0
                            state = "achievements"
                        elif key == "stats_btn":
                            state = "stats"
                        elif key == "settings":
                            state = "settings"
                        break

            elif state == "pre_game":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        play_sfx("button")
                        state = "menu"
                    elif btn_rect(820).collidepoint(mx, my):
                        play_sfx("button")
                        start_run(prep_survival, True)
                        state = "game"
                    else:
                        keys = SURVIVAL_BOOSTERS if prep_survival else CLASSIC_BOOSTERS
                        for i, key in enumerate(keys):
                            if prep_card_rect(i).collidepoint(mx, my):
                                if player_boosters[key] > 0:
                                    play_sfx("select")
                                    selected_run_boosters[key] = not selected_run_boosters[key]
                                else:
                                    play_sfx("error")

            elif state == "shop":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        save_game_data()
                        play_sfx("button")
                        state = "menu"
                    for i, th in enumerate(BACKGROUNDS):
                        if bg_card_rect(i).collidepoint(mx, my):
                            if th["unlocked"]:
                                play_sfx("select")
                                current_bg_idx = i
                                shop_message = ""
                                save_game_data()
                            elif th.get("ach"):
                                play_sfx("error")
                            elif total_coins >= th["price"]:
                                play_sfx("purchase")
                                stats["purchases"] += 1
                                total_coins -= th["price"]
                                th["unlocked"] = True
                                current_bg_idx = i
                                shop_message = f"{t['bought']}: {lname(th)}!"
                                save_game_data()
                            else:
                                play_sfx("error")
                                shop_message = t["no_money"]

            elif state == "platform_shop":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        save_game_data()
                        play_sfx("button")
                        state = "menu"
                    for i, p in enumerate(PLATFORM_GRADIENTS):
                        if platform_card_rect(i).collidepoint(mx, my):
                            if i in unlocked_platforms:
                                play_sfx("select")
                                current_platform_idx = i
                                save_game_data()
                            else:
                                play_sfx("error")

            elif state == "boosters":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        save_game_data()
                        play_sfx("button")
                        state = "menu"
                    for i, key in enumerate(SHOP_BOOSTERS):
                        if booster_card_rect(i).collidepoint(mx, my):
                            if total_coins >= BOOSTER_PRICE:
                                play_sfx("purchase")
                                stats["purchases"] += 1
                                total_coins -= BOOSTER_PRICE
                                player_boosters[key] += 1
                                save_game_data()
                            else:
                                play_sfx("error")

            elif state == "wheel":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        play_sfx("button")
                        state = "menu"
                    elif btn_rect(720).collidepoint(mx, my):
                        current_time = time.time()
                        if current_time - last_spin_time > 60:
                            play_sfx("spin")
                            reward_type = random.choice(["coins"] + SHOP_BOOSTERS)
                            if reward_type == "coins":
                                amt = random.choice([50, 100, 200])
                                earn_coins(amt)
                                wheel_reward_text = f"{t['reward']} +{amt} 🪙"
                            else:
                                player_boosters[reward_type] += 1
                                wheel_reward_text = f"{t['reward']} +1 {t[BOOSTER_NAME_KEY[reward_type]]}!"
                            last_spin_time = current_time
                            stats["spins"] += 1
                            play_sfx("reward")
                            save_game_data()
                        else:
                            wheel_reward_text = t["cooldown_active"]

            elif state == "achievements":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        play_sfx("button")
                        ach_drag = False
                        state = "menu"
                    elif ACH_TOP <= my <= ACH_BOTTOM:
                        ach_drag = True
                        ach_drag_y = my
                        ach_drag_scroll = ach_scroll
                elif event.type == pygame.MOUSEMOTION and ach_drag:
                    ach_scroll = max(0, min(ach_max_scroll(), ach_drag_scroll - (event.pos[1] - ach_drag_y)))
                elif event.type == pygame.MOUSEBUTTONUP:
                    ach_drag = False
                elif event.type == pygame.MOUSEWHEEL:
                    ach_scroll = max(0, min(ach_max_scroll(), ach_scroll - event.y * 60))

            elif state == "stats":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_rect(900).collidepoint(event.pos):
                        play_sfx("button")
                        state = "menu"

            elif state == "settings":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(900).collidepoint(mx, my):
                        save_game_data()
                        play_sfx("button")
                        state = "menu"
                    elif btn_rect(220).collidepoint(mx, my):
                        play_sfx("button")
                        current_lang = "en" if current_lang == "ru" else "ru"
                        save_game_data()
                    elif btn_rect(640).collidepoint(mx, my):
                        play_sfx("button")
                        state = "confirm_reset"

                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                    if pygame.mouse.get_pressed()[0]:
                        mx, my = event.pos
                        margin = 60
                        slider_w = SCREEN_WIDTH - margin * 2
                        if 320 <= my <= 390 and margin <= mx <= margin + slider_w:
                            sound_volume = max(0.0, min(1.0, (mx - margin) / slider_w))
                            save_game_data()
                        elif 450 <= my <= 520 and margin <= mx <= margin + slider_w:
                            music_volume = max(0.0, min(1.0, (mx - margin) / slider_w))
                            pygame.mixer.music.set_volume(music_volume)
                            save_game_data()

            elif state == "confirm_reset":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if btn_rect(560).collidepoint(mx, my):
                        reset_progress()
                        play_sfx("bomb")
                        state = "settings"
                    elif btn_rect(630).collidepoint(mx, my):
                        play_sfx("button")
                        state = "settings"

            elif state == "game":
                menu_btn_rect = pygame.Rect(SCREEN_WIDTH - 110, 25, 85, 40)
                pause_btn_rect = pygame.Rect(SCREEN_WIDTH - 165, 25, 45, 40)

                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if not run.over:
                        set_paused(not run.paused)
                        is_dragging = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if run.paused:
                        if btn_rect(450).collidepoint(mx, my):
                            play_sfx("button")
                            set_paused(False)
                        elif btn_rect(520).collidepoint(mx, my):
                            play_sfx("button")
                            set_paused(False)
                            save_game_data()
                            state = "menu"
                    elif menu_btn_rect.collidepoint(mx, my):
                        save_game_data()
                        state = "menu"
                    elif pause_btn_rect.collidepoint(mx, my) and not run.over:
                        play_sfx("button")
                        set_paused(True)
                        is_dragging = False
                    elif run.over:
                        if run.over_time > 0.6:
                            start_run(run.survival, False)
                    else:
                        is_dragging = True
                        player.move_to(mx)

                elif event.type == pygame.MOUSEBUTTONUP:
                    is_dragging = False

                elif event.type == pygame.MOUSEMOTION and not run.over and not run.paused:
                    mx, my = event.pos
                    if is_dragging or pygame.mouse.get_focused():
                        player.move_to(mx)

        # ======================= ОТРИСОВКА / ЛОГИКА =======================
        if state == "menu":
            if logo_image:
                screen.blit(logo_image, (SCREEN_WIDTH // 2 - logo_image.get_width() // 2, 50))
            else:
                title = font_l.render("Bounce It Out", True, (255, 255, 255))
                screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

            stats_txt = font_s.render(f"{t['best']}: {high_score} | {t['survival_best']}: {survival_high_score}", True, (255, 255, 255))
            screen.blit(stats_txt, (SCREEN_WIDTH // 2 - stats_txt.get_width() // 2, 290))

            draw_coin_display(25, 25, total_coins)

            for i, key in enumerate(MENU_ENTRIES):
                label = t[key]
                if key == "achievements":
                    label = f"{label} ({len(unlocked_achievements)}/{len(ACHIEVEMENTS)})"
                draw_button(label, 330 + i * 64, 52)

        elif state == "pre_game":
            title = font_m.render(t["prep_title"], True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
            draw_coin_display(25, 25, total_coins)

            keys = SURVIVAL_BOOSTERS if prep_survival else CLASSIC_BOOSTERS
            for i, key in enumerate(keys):
                rect = prep_card_rect(i)
                is_selected = selected_run_boosters[key]
                col = (0, 150, 100) if is_selected else (50, 60, 90)
                pygame.draw.rect(screen, col, rect, border_radius=12)
                pygame.draw.rect(screen, (255, 215, 0) if is_selected else (120, 120, 150), rect, 2, border_radius=12)
                name = t[BOOSTER_NAME_KEY[key]]
                screen.blit(font_m.render(f"{name} ({t['available']}: {player_boosters[key]})", True, (255, 255, 255)), (rect.x + 20, rect.y + 15))
                screen.blit(font_s.render(t["d_" + key], True, (200, 200, 220)), (rect.x + 20, rect.y + 48))
                status_txt = t["on_run"] if is_selected else t["off"]
                screen.blit(font_s.render(status_txt, True, (255, 215, 0) if is_selected else (170, 170, 190)), (rect.x + 20, rect.y + 72))

            draw_button(t["start_game"], 820)
            draw_button(t["back"], 900)

        elif state == "shop":
            title = font_m.render(t["shop"], True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 35))
            draw_coin_display(25, 25, total_coins)

            for i, th in enumerate(BACKGROUNDS):
                rect = bg_card_rect(i)
                if i == current_bg_idx:
                    btn_color = (0, 150, 100)
                elif th["unlocked"]:
                    btn_color = (60, 100, 150)
                elif th.get("ach"):
                    btn_color = (40, 40, 55)
                else:
                    btn_color = (80, 50, 50)
                pygame.draw.rect(screen, btn_color, rect, border_radius=12)
                pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=12)
                screen.blit(font_m.render(lname(th), True, (255, 255, 255)), (rect.x + 25, rect.y + 14))
                if i == current_bg_idx:
                    status, scol = t["equipped"], (200, 200, 200)
                elif th["unlocked"]:
                    status, scol = t["select"], (200, 200, 200)
                elif th.get("ach"):
                    unl = BG_UNLOCKERS.get(i)
                    status = f"{t['locked']}: {ach_text(unl)[0]}" if unl else t["locked"]
                    scol = (255, 215, 0)
                else:
                    status, scol = f"{t['buy']}: {th['price']}", (200, 200, 200)
                screen.blit(font_s.render(status, True, scol), (rect.x + 25, rect.y + 52))
                
                pygame.draw.rect(screen, th["bg"], (rect.right - 90, rect.y + 20, 36, 44), border_top_left_radius=8, border_bottom_left_radius=8)
                pygame.draw.rect(screen, th["coin"], (rect.right - 54, rect.y + 20, 36, 44), border_top_right_radius=8, border_bottom_right_radius=8)
                pygame.draw.rect(screen, (255, 255, 255), (rect.right - 90, rect.y + 20, 72, 44), 1, border_radius=8)

            screen.blit(font_s.render(shop_message, True, (255, 100, 100)), (SCREEN_WIDTH // 2 - 100, 862))
            draw_button(t["back"], 900)

        elif state == "platform_shop":
            title = font_m.render(t["platform_shop"], True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
            draw_platform_cards()
            draw_button(t["back"], 900)

        elif state == "boosters":
            title = font_m.render(t["boosters_btn"], True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 35))
            draw_coin_display(25, 25, total_coins)

            for i, key in enumerate(SHOP_BOOSTERS):
                rect = booster_card_rect(i)
                pygame.draw.rect(screen, (50, 70, 100), rect, border_radius=12)
                pygame.draw.rect(screen, (120, 160, 220), rect, 2, border_radius=12)
                name = t[BOOSTER_NAME_KEY[key]]
                screen.blit(font_m.render(f"{name}: {player_boosters[key]} {t['pcs']}", True, (255, 255, 255)), (rect.x + 20, rect.y + 14))
                screen.blit(font_s.render(t["d_" + key], True, (200, 200, 220)), (rect.x + 20, rect.y + 46))
                screen.blit(font_s.render(f"{t['buy']} ({BOOSTER_PRICE})", True, (255, 215, 0)), (rect.x + 20, rect.y + 72))

            draw_button(t["back"], 900)

        elif state == "wheel":
            title = font_m.render(t["wheel"], True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

            wheel_center = (SCREEN_WIDTH // 2, 320)
            pygame.draw.circle(screen, (40, 40, 60), wheel_center, 140)
            pygame.draw.circle(screen, (255, 215, 0), wheel_center, 140, 6)
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                nx = wheel_center[0] + int(140 * math.cos(rad))
                ny = wheel_center[1] + int(140 * math.sin(rad))
                pygame.draw.line(screen, (100, 100, 150), wheel_center, (nx, ny), 2)
            pygame.draw.circle(screen, (255, 69, 0), wheel_center, 20)

            time_left = 60 - (time.time() - last_spin_time)
            if time_left <= 0:
                draw_button(t["spin"], 720)
            else:
                secs = int(time_left)
                screen.blit(font_s.render(f"{t['cooldown']} {secs} {t['sec']}", True, (255, 100, 100)), (SCREEN_WIDTH // 2 - 100, 735))

            reward_surf = font_m.render(wheel_reward_text, True, (255, 215, 0))
            screen.blit(reward_surf, (SCREEN_WIDTH // 2 - reward_surf.get_width() // 2, 520))
            draw_button(t["back"], 900)

        elif state == "achievements":
            draw_achievements_screen(ach_scroll)
            draw_button(t["back"], 900)

        elif state == "stats":
            draw_stats_screen()
            draw_button(t["back"], 900)

        elif state == "settings":
            title = font_m.render(t["settings"], True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

            draw_button(t["lang"], 220)
            draw_slider(t["sound_lbl"], 320, sound_volume)
            draw_slider(t["music_lbl"], 450, music_volume)
            draw_button(t["reset_progress"], 640, color=(120, 40, 40), border=(220, 90, 90))

            draw_button(t["back"], 900)

        elif state == "confirm_reset":
            title = font_l.render(t["reset_title"], True, (255, 120, 120))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 340))
            for j, key in enumerate(("reset_warn1", "reset_warn2", "reset_warn3")):
                line = font_s.render(t[key], True, (230, 230, 245))
                screen.blit(line, (SCREEN_WIDTH // 2 - line.get_width() // 2, 410 + j * 28))
            draw_button(t["reset_yes"], 560, color=(150, 40, 40), border=(240, 100, 100))
            draw_button(t["reset_no"], 630)

        elif state == "game":
            if not run.paused:
                run.shake = max(0.0, run.shake - dt)
                run.flash = max(0.0, run.flash - dt)

                if run.over:
                    run.over_time += dt
                    if run.new_record and run.over_time < 6:
                        run.fx_timer -= dt
                        if run.fx_timer <= 0:
                            run.fx_timer = 0.3
                            col = random.choice([(255, 215, 0), (255, 105, 180), (0, 200, 255), (120, 255, 120), (255, 255, 255)])
                            add_particles(random.randint(80, SCREEN_WIDTH - 80), random.randint(150, 450), col, 22)
                else:
                    stats["play_time"] += dt
                    if player.magnet_timer > 0:
                        player.magnet_timer -= dt
                    run.freeze = max(0.0, run.freeze - dt)
                    run.slow = max(0.0, run.slow - dt)
                    scale = 0.0 if run.freeze > 0 else (0.5 if run.slow > 0 else 1.0)

                    if not run.survival:
                        if run.freeze <= 0:
                            run.spawn_timer += scale
                            threshold = max(12, 38 - (run.score // 8))
                            if run.spawn_timer > threshold:
                                run.spawn_timer = 0.0
                                if run.score >= 60 and random.random() < 0.12:
                                    run.items.extend(spawn_group(run.score, player.speed_multiplier))
                                else:
                                    run.items.append(FallingItem(run.score, player.speed_multiplier, False, kind=pick_special_classic()))
                    else:
                        balls = [i for i in run.items if i.kind == "ball"]
                        total_bounces = sum(i.bounces for i in run.items)
                        if len(balls) < 1 + (total_bounces // 10) and run.freeze <= 0:
                            run.items.append(FallingItem(run.score, player.speed_multiplier, True))
                        if run.freeze <= 0:
                            run.special_timer -= dt
                            if run.special_timer <= 0:
                                run.special_timer = random.uniform(7, 12)
                                pool = ["magnet", "clock", "ice"] + (["heart"] if run.lives < run.max_lives else [])
                                run.items.append(FallingItem(run.score, player.speed_multiplier, True, kind=random.choice(pool)))

                    if player.magnet_timer > 0:
                        nearest_item = None
                        min_dist = 9999
                        for item in run.items:
                            if not item.is_bomb:
                                dist = math.hypot(player.rect.centerx - item.x, player.rect.centery - item.y)
                                if dist < min_dist:
                                    min_dist = dist
                                    nearest_item = item
                        if nearest_item:
                            dx = player.rect.centerx - nearest_item.x
                            dy = player.rect.centery - nearest_item.y
                            nearest_item.x += dx * 0.1 * player.speed_multiplier
                            nearest_item.y += dy * 0.1 * player.speed_multiplier

                    frozen_survival = run.survival and run.freeze > 0
                    for item in run.items[:]:
                        if run.over:
                            break
                        item.update(player.speed_multiplier, run.survival, scale)
                        item_rect = pygame.Rect(item.x - item.radius, item.y - item.radius, item.radius * 2, item.radius * 2)

                        if (not frozen_survival) and player.rect.colliderect(item_rect):
                            if item.kind in SPECIAL_KINDS:
                                collect_special(item)
                                run.items.remove(item)
                            elif run.survival:
                                play_sfx("bounce")
                                item.vy = -abs(item.vy) * random.uniform(0.95, 1.1)
                                item.vx = random.uniform(-3.5, 3.5)
                                item.bounces += 1
                                run.score += 1
                                stats["survival_bounces"] += 1
                                run.bounce_count += 1
                                if run.bounce_count % 5 == 0:
                                    earn_coins(1 * run.coin_mult)
                                add_particles(item.x, item.y, (0, 200, 255), 10)
                            else:
                                if item.is_bomb:
                                    if player.shield_hits > 0:
                                        player.shield_hits -= 1
                                        play_sfx("shield")
                                        stats["bombs_blocked"] += 1
                                        add_particles(item.x, item.y, (0, 150, 255), 18)
                                    else:
                                        play_sfx("bomb")
                                        run.shake = 0.3
                                        run.flash = 0.15
                                        add_particles(item.x, item.y, (255, 50, 50), 25)
                                        end_run()
                                else:
                                    play_sfx("collect")
                                    run.score += item.score_val
                                    earn_coins(item.coin_val * run.coin_mult)
                                    stats["balls_caught"] += 1
                                    if item.emoji == "🥎":
                                        stats["special_caught"] += 1
                                    add_particles(item.x, item.y, (255, 215, 0), 10)
                                run.items.remove(item)

                        elif item.y > SCREEN_HEIGHT + 40:
                            if not run.survival:
                                if not item.is_bomb and item.kind not in SPECIAL_KINDS:
                                    play_sfx("loss_life")
                                    end_run()
                                else:
                                    run.items.remove(item)
                            else:
                                if item.kind not in SPECIAL_KINDS:
                                    run.lives -= 1
                                    play_sfx("loss_life")
                                    run.shake = 0.25
                                    add_particles(item.x, SCREEN_HEIGHT - 30, (255, 80, 80), 20)
                                    if run.lives <= 0:
                                        end_run()
                                    else:
                                        item.y = -40
                                        item.vy = abs(item.vy)
                                else:
                                    run.items.remove(item)

            check_achievements()

            ox = random.randint(-6, 6) if run.shake > 0 else 0
            oy = random.randint(-6, 6) if run.shake > 0 else 0

            for item in run.items:
                item.draw()

            player.draw()

            update_and_draw_particles(dt)

            if run.flash > 0:
                screen.blit(flash_surf, (0, 0))
            elif run.freeze > 0:
                ice_surf.set_alpha(int(min(1.0, run.freeze) * 60))
                screen.blit(ice_surf, (0, 0))

            score_txt = font_m.render(f"{t['score']}: {run.score}", True, (255, 255, 255))
            screen.blit(score_txt, (25 + ox, 25 + oy))

            if run.survival:
                lives_txt = font_m.render(f"{t['lives']}: {'❤️' * run.lives}", True, (255, 255, 255))
                screen.blit(lives_txt, (25 + ox, 60 + oy))

            fx_x = 25
            if player.magnet_timer > 0:
                fx_x = draw_effect(fx_x, 90, "🧲", player.magnet_timer)
            if run.slow > 0:
                fx_x = draw_effect(fx_x, 90, "⏰", run.slow)
            if run.freeze > 0:
                fx_x = draw_effect(fx_x, 90, "🧊", run.freeze)

            if not run.over and not run.paused:
                pygame.draw.rect(screen, (50, 50, 80), (SCREEN_WIDTH - 110, 25, 85, 40), border_radius=8)
                pygame.draw.rect(screen, (100, 100, 150), (SCREEN_WIDTH - 110, 25, 85, 40), 2, border_radius=8)
                m_txt = font_s.render(t["menu"], True, (255, 255, 255))
                screen.blit(m_txt, (SCREEN_WIDTH - 110 + 42 - m_txt.get_width() // 2, 36))

                pygame.draw.rect(screen, (50, 50, 80), (SCREEN_WIDTH - 165, 25, 45, 40), border_radius=8)
                pygame.draw.rect(screen, (100, 100, 150), (SCREEN_WIDTH - 165, 25, 45, 40), 2, border_radius=8)
                p_txt = font_m.render("⏸", True, (255, 255, 255))
                screen.blit(p_txt, (SCREEN_WIDTH - 165 + 22 - p_txt.get_width() // 2, 32))

            if run.paused:
                screen.blit(dim_surf, (0, 0))
                p_txt = font_l.render(t["paused"], True, (255, 255, 255))
                screen.blit(p_txt, (SCREEN_WIDTH // 2 - p_txt.get_width() // 2, 320))
                draw_button(t["resume"], 450)
                draw_button(t["to_menu"], 520)

            if run.over:
                screen.blit(dim_surf, (0, 0))
                go_txt = font_l.render(t["game_over"], True, (255, 50, 50))
                screen.blit(go_txt, (SCREEN_WIDTH // 2 - go_txt.get_width() // 2, 380))

                final_txt = font_m.render(f"{t['score']}: {run.score}", True, (255, 255, 255))
                screen.blit(final_txt, (SCREEN_WIDTH // 2 - final_txt.get_width() // 2, 440))

                if run.new_record:
                    rec_txt = font_m.render(t["new_record"], True, (255, 215, 0))
                    screen.blit(rec_txt, (SCREEN_WIDTH // 2 - rec_txt.get_width() // 2, 480))

                res_txt = font_s.render(t["restart"], True, (200, 200, 200))
                screen.blit(res_txt, (SCREEN_WIDTH // 2 - res_txt.get_width() // 2, 530))

        draw_achievement_toast(dt)
        pygame.display.flip()

if __name__ == "__main__":
    main()