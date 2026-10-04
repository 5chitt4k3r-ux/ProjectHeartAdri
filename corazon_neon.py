import colorsys
import math
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import turtle

# ==========================================================
# CONFIGURACIÓN GENERAL Y AUDIO
# ==========================================================
MUSIC_FILE = "Los Caligaris - Con Vos.mp3"   # Nombre de tu mp3 (en la misma carpeta que este script) o ruta completa
MUSIC_VOLUME = 0.8           # 0.0 a 1.0 (solo Windows)
MUSIC_LOOP = False           # True = repite la canción y reinicia la letra junto con ella

# Ajuste de sincronización en segundos (por si la letra no coincide exactamente con tu mp3)
# Puedes presionar las flechas IZQUIERDA / DERECHA en el teclado durante la animación para ajustar en vivo
SYNC_OFFSET = 0.0  # + retarda subtítulos, - los adelanta

WORDS = ["Te amodoro", "PapitaLover", "Te amo mi vida"]
CENTER_TEXT = "Te amo Adri"
SCALE = 17  # Escala armónica del corazón para dejar espacio a los subtítulos

# Velocidades de animación del corazón
ROTATION_SPEED = 0.016   # Velocidad a la que giran las palabras alrededor del contorno
COLOR_SPEED = 0.0014     # Velocidad de transición (Rosado <-> Morado <-> Verde)
COLOR_MODE = "UNIFORME"  # "UNIFORME" o "ONDA"

# ==========================================================
# REPRODUCTOR DE MP3 (sin pygame, sin instalar nada)
#   Windows: reproductor nativo (MCI)
# ==========================================================
class Music:
    def __init__(self, filename, volume=0.8, loop=False):
        if not os.path.isabs(filename):
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        self.path = filename
        self.volume = volume
        self.loop = loop
        self.win = False
        self.proc = None
        self._stop = threading.Event()
        self._restarted = False

    def _mci(self, cmd):
        import ctypes
        buf = ctypes.create_unicode_buffer(255)
        err = ctypes.windll.winmm.mciSendStringW(cmd, buf, 254, 0)
        return err, buf.value

    def start(self):
        if not os.path.isfile(self.path):
            print("No encuentro el archivo de musica:", self.path)
            return
        try:
            if sys.platform.startswith("win"):
                self._mci("close bgm")
                err, _ = self._mci(f'open "{self.path}" type mpegvideo alias bgm')
                if err:
                    print("Windows no pudo abrir el mp3 (codigo %d)." % err)
                    return
                self._mci(f"setaudio bgm volume to {int(self.volume * 1000)}")
                self._mci("play bgm")
                self.win = True
            elif sys.platform == "darwin":
                self._start_thread(["afplay", self.path])
            else:
                for name, args in (
                    ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
                    ("mpg123", ["-q"]),
                    ("cvlc", ["--play-and-exit", "--quiet"]),
                ):
                    exe = shutil.which(name)
                    if exe:
                        self._start_thread([exe] + args + [self.path])
                        return
                print("No hay reproductor de mp3. Instala ffmpeg, mpg123 o vlc.")
        except Exception as e:
            print("No se pudo reproducir la musica:", e)

    def _start_thread(self, cmd):
        def run():
            first = True
            while not self._stop.is_set():
                if not first:
                    self._restarted = True
                first = False
                t0 = time.time()
                self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)
                while self.proc.poll() is None and not self._stop.is_set():
                    time.sleep(0.2)
                if self._stop.is_set():
                    self.proc.terminate()
                    return
                if not self.loop or time.time() - t0 < 0.5:
                    return
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        """Devuelve True si la cancion acaba de reiniciarse (solo con MUSIC_LOOP)."""
        if self.win:
            _, mode = self._mci("status bgm mode")
            if mode == "stopped" and self.loop:
                self._mci("play bgm from 0")
                return True
            return False
        if self._restarted:
            self._restarted = False
            return True
        return False

    def stop(self):
        self._stop.set()
        if self.win:
            self._mci("close bgm")
            self.win = False
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

music = Music(MUSIC_FILE, MUSIC_VOLUME, MUSIC_LOOP)

# ==========================================================
# LETRA COMPLETA SINCRONIZADA ("Con Vos" - Los Caligaris)
# Cada línea con su marca de tiempo exacta de inicio y fin (en segundos)
# ==========================================================
LYRICS_TIMELINE = [
    # Intro instrumental
    (0.0, 10.0, "♫ (Música instrumental) ♫"),

    # Verso 1
    (10.0, 14.5, "Hoy siento la feliz vergüenza de haberme jactado"),
    (14.5, 19.5, "De que con la soledad de aliada encontraba felicidad"),
    (19.5, 24.0, "¿Qué sabía de felicidad ese payaso?"),
    (24.0, 28.5, "Si nunca pudo imaginarse con vos en el patio"),
    (28.5, 33.0, "Cantando temas de los Beatles de noche"),
    (33.0, 38.0, "Con la viola y tomando un fernet"),

    # Coro 1
    (38.0, 42.5, "Quiero vivir con vos"),
    (42.5, 47.0, "Amontonar todas las cosas que hay en el placard"),
    (47.0, 51.5, "Y que en el mundo nuestra pieza sea mi lugar"),
    (51.5, 56.5, "Que a cada día sea tu abrazo el que le dé el mejor final"),
    (56.5, 61.0, "Quiero morir con vos"),
    (61.0, 65.5, "Y de tu vida hacer por siempre la mejor canción"),
    (65.5, 70.0, "Y convivir con la noticia tan feliz"),
    (70.0, 77.0, "De que a la noche vamos a dormir los dos"),

    # Interludio
    (77.0, 81.0, "♫ Con vos... ♫"),

    # Verso 2
    (81.0, 85.5, "Volver de la gira y saber que me estás esperando"),
    (85.5, 90.0, "Cruzar esa puerta y de pronto ahogarme en tu paz"),
    (90.0, 94.5, "Son esas postales con las que yo vivo soñando"),
    (94.5, 99.5, "Sentados, viejitos, nos veo a los dos en el patio"),
    (99.5, 104.0, "Cantando temas de los Beatles de noche"),
    (104.0, 109.0, "Con la viola y tomando un malbec"),

    # Coro 2
    (109.0, 113.5, "Quiero vivir con vos"),
    (113.5, 118.0, "Amontonar todas las cosas que hay en el placard"),
    (118.0, 122.5, "Y que en el mundo nuestra pieza sea mi lugar"),
    (122.5, 127.5, "Que a cada día sea tu abrazo el que le dé el mejor final"),
    (127.5, 132.0, "Quiero morir con vos"),
    (132.0, 136.5, "Y de tu vida hacer por siempre la mejor canción"),
    (136.5, 141.0, "Y convivir con la noticia tan feliz"),
    (141.0, 147.5, "De que a la noche vamos a dormir los dos"),

    # Outro
    (147.5, 152.0, "Con vos"),
    (152.0, 156.0, "U-uh"),
    (156.0, 162.0, "A-ah"),
]

TOTAL_SONG_DURATION = LYRICS_TIMELINE[-1][1]

def get_current_subtitle(elapsed_seconds):
    """Obtiene la línea de la canción correspondiente al segundo actual."""
    song_time = elapsed_seconds % TOTAL_SONG_DURATION
    for start, end, text in LYRICS_TIMELINE:
        if start <= song_time < end:
            return text
    return ""

# ==========================================================
# CONFIGURACIÓN DE LA VENTANA
# ==========================================================
WINDOW_W, WINDOW_H = 1250, 840
screen = turtle.Screen()
screen.setup(width=WINDOW_W, height=WINDOW_H)
screen.bgcolor("#070308")  # Fondo negro profundo de alto contraste
screen.title("I love you <3 - Los Caligaris: Con Vos")
screen.tracer(0)

# ==========================================================
# CONTROL DE SINCRONIZACIÓN CON EL TECLADO
# ==========================================================
manual_offset = 0.0

def delay_subs():
    global manual_offset
    manual_offset -= 1.0  # Retrasar subtítulos 1s

def advance_subs():
    global manual_offset
    manual_offset += 1.0  # Adelantar subtítulos 1s

def reset_subs():
    global manual_offset
    manual_offset = 0.0

screen.listen()
screen.onkey(advance_subs, "Right")
screen.onkey(delay_subs, "Left")
screen.onkey(reset_subs, "space")

# ==========================================================
# FÓRMULAS MATEMÁTICAS Y DE COLOR DEL CORAZÓN
# ==========================================================
HEART_CY = 45  # Elevamos ligeramente el corazón para dar espacio a los subtítulos abajo

def heart_xy(t):
    """Calcula las coordenadas (x, y) de la curva paramétrica del corazón."""
    x = 16 * (math.sin(t) ** 3)
    y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
    return x * SCALE, y * SCALE + HEART_CY

def heart_pulse(t):
    """Simula el latido cardíaco realista (sístole y diástole 'lub-dub' + reposo)."""
    phase = t % (2 * math.pi)
    if phase < 0.7:
        return 1.0 + 0.08 * math.sin(phase / 0.7 * math.pi)
    elif 0.9 < phase < 1.5:
        return 1.0 + 0.04 * math.sin((phase - 0.9) / 0.6 * math.pi)
    else:
        return 1.0

def get_tri_color(val):
    """Genera la transición continua entre Rosado Neón, Morado y Verde Neón."""
    p = (val % 1.0) * 4.0
    seg = int(p)
    f = p - seg

    if seg == 0:    # Rosado -> Morado
        h = 0.91 - f * (0.91 - 0.76)
    elif seg == 1:  # Morado -> Verde (pasa por azul/cian eléctrico)
        h = 0.76 - f * (0.76 - 0.38)
    elif seg == 2:  # Verde -> Morado (pasa por cian/azul eléctrico)
        h = 0.38 + f * (0.76 - 0.38)
    else:           # Morado -> Rosado
        h = 0.76 + f * (0.91 - 0.76)

    r_neon, g_neon, b_neon = colorsys.hsv_to_rgb(h, 0.95, 1.0)
    neon_hex = '#{:02x}{:02x}{:02x}'.format(int(r_neon * 255), int(g_neon * 255), int(b_neon * 255))
    r_base, g_base, b_base = colorsys.hsv_to_rgb(h, 0.85, 0.52)
    base_hex = '#{:02x}{:02x}{:02x}'.format(int(r_base * 255), int(g_base * 255), int(b_base * 255))
    return base_hex, neon_hex

# ==========================================================
# PRE-GENERACIÓN DE LAS PARTÍCULAS DEL CORAZÓN
# ==========================================================
# 1. Línea exterior giratoria (borde del corazón)
border_particles = []
NUM_BORDER = 110
for i in range(NUM_BORDER):
    t_base = (i / NUM_BORDER) * 2 * math.pi
    is_neon = (i % 4 == 0) or (random.random() < 0.22)
    border_particles.append({
        "t_base": t_base,
        "word": random.choice(WORDS),
        "is_neon": is_neon,
        "size": random.choice([9, 10]),
    })

# 2. Relleno interior del corazón
inner_particles = []
NUM_INNER = 50
for _ in range(NUM_INNER):
    t_base = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.18, 0.85)
    is_neon = random.random() < 0.20
    inner_particles.append({
        "t_base": t_base,
        "r": r,
        "word": random.choice(WORDS),
        "is_neon": is_neon,
        "size": random.choice([7, 8]),
    })

# Pincel turtle para el corazón y texto central
pen = turtle.Turtle()
pen.hideturtle()
pen.penup()

# ==========================================================
# BUCLE PRINCIPAL DE ANIMACIÓN INFINITA
# ==========================================================
music.start()                    # <- la música arranca justo antes del reloj de la letra
start_timestamp = time.time()
last_music_poll = 0.0
time_counter = 0.0
rotation_angle = 0.0
color_cycle = 0.0

SUBTITLE_Y = -320  # Posición de los subtítulos debajo del corazón

try:
    while True:
        pen.clear()

        # Tiempo transcurrido exacto del reloj para sincronía perfecta con el audio
        current_time = time.time()

        # Si la canción se repite (MUSIC_LOOP), la letra vuelve a empezar con ella
        if current_time - last_music_poll > 0.5:
            last_music_poll = current_time
            if music.poll():
                start_timestamp = current_time

        elapsed_seconds = (current_time - start_timestamp) + manual_offset + SYNC_OFFSET

        # 1. Calcular pulso cardíaco del corazón
        pulse = heart_pulse(time_counter)
        global_base, global_neon = get_tri_color(color_cycle)

        # --------------------------------------------------
        # 2. DIBUJAR EL CORAZÓN CENTRAL CON PALABRAS GIRANDO
        # --------------------------------------------------
        # Palabras de la línea exterior del corazón
        for p in border_particles:
            t_curr = (p["t_base"] + rotation_angle) % (2 * math.pi)
            bx, by = heart_xy(t_curr)
            # Escalar respecto al centro del corazón
            cur_x = bx * pulse
            cur_y = HEART_CY + (by - HEART_CY) * pulse
            pen.goto(cur_x, cur_y)

            if COLOR_MODE == "UNIFORME":
                base_color, neon_color = global_base, global_neon
            else:
                base_color, neon_color = get_tri_color(color_cycle + (t_curr / (2 * math.pi)))

            if p["is_neon"]:
                pen.color(neon_color)
                pen.write(p["word"], align="center", font=("Arial", p["size"], "bold"))
            else:
                pen.color(base_color)
                pen.write(p["word"], align="center", font=("Arial", p["size"], "normal"))

        # Palabras del relleno interior del corazón
        for p in inner_particles:
            t_curr = (p["t_base"] + rotation_angle * 0.5) % (2 * math.pi)
            bx, by = heart_xy(t_curr)
            cur_x = (bx * p["r"]) * pulse
            cur_y = HEART_CY + ((by - HEART_CY) * p["r"]) * pulse
            pen.goto(cur_x, cur_y)

            if COLOR_MODE == "UNIFORME":
                base_color, neon_color = global_base, global_neon
            else:
                base_color, neon_color = get_tri_color(color_cycle + (t_curr / (2 * math.pi)))

            if p["is_neon"]:
                pen.color(neon_color)
                pen.write(p["word"], align="center", font=("Arial", p["size"], "bold"))
            else:
                pen.color(base_color)
                pen.write(p["word"], align="center", font=("Arial", p["size"], "normal"))

        # --------------------------------------------------
        # 3. TEXTO CENTRAL ANIMADO CON RESPLANDOR NEÓN
        # --------------------------------------------------
        center_size = int(34 + 6 * (pulse - 1.0) / 0.08)

        # Capa 1: Resplandor Neón exterior (acompaña el color del corazón)
        pen.goto(0, HEART_CY - 22)
        pen.color(global_neon)
        pen.write(CENTER_TEXT, align="center", font=("Georgia", center_size + 2, "bold"))

        # Capa 2: Núcleo blanco brillante
        pen.goto(0, HEART_CY - 20)
        pen.color("#ffffff")
        pen.write(CENTER_TEXT, align="center", font=("Georgia", center_size, "bold"))

        # --------------------------------------------------
        # 4. SUBTÍTULOS DE LA CANCIÓN DEBAJO DEL CORAZÓN (BLANCO PURO)
        # --------------------------------------------------
        subtitle_text = get_current_subtitle(elapsed_seconds)

        if subtitle_text:
            # Sombra suave para dar volumen cinematográfico
            pen.goto(0, SUBTITLE_Y - 2)
            pen.color("#1a1a24")
            pen.write(subtitle_text, align="center", font=("Georgia", 16, "bold"))

            # Subtítulo principal en blanco puro de alto contraste
            pen.goto(0, SUBTITLE_Y)
            pen.color("#ffffff")
            pen.write(subtitle_text, align="center", font=("Georgia", 16, "bold"))

        # Indicador sutil del tema musical arriba
        pen.goto(0, 375)
        pen.color("#888899")
        pen.write("♪ Los Caligaris — Con Vos ♪", align="center", font=("Arial", 10, "italic"))

        screen.update()

        # 5. Actualizar contadores para el siguiente cuadro (~45 FPS)
        time_counter += 0.08
        rotation_angle += ROTATION_SPEED
        color_cycle += COLOR_SPEED
        time.sleep(0.015)

except (turtle.Terminator, Exception):
    # Cierre limpio de la ventana
    pass

finally:
    music.stop()                 # Detiene la música al cerrar la ventana