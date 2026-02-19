import pygame
import threading
import requests
import io
import time
import sys
import math
import speech_recognition as sr

from ai import chat_with_ai
from config import ELEVEN_API_KEY, VOICE_ID, TTS_MODEL

# ---------------- Utils ----------------
def sanitize(text):
    return text.replace("\x00", "")

def wrap_text(text, font, width):
    words = text.split(" ")
    lines, line = [], ""
    for w in words:
        test = line + w + " "
        if font.size(test)[0] <= width:
            line = test
        else:
            lines.append(line)
            line = w + " "
    lines.append(line)
    return lines

# ---------------- Init ----------------
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 920, 860
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("J.A.R.V.I.S")

clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
big_font = pygame.font.SysFont("consolas", 22)
btn_font = pygame.font.SysFont("consolas", 18, bold=True)

# ---------------- State ----------------
input_text = ""
chat_log = []          # stores ALL visible messages
thinking = False
speaking = False
listening = False

# ---------------- Layout ----------------
TEXT_AREA_HEIGHT = 300
TEXT_AREA_TOP = HEIGHT - 520
TEXT_AREA_LEFT = 60
TEXT_AREA_WIDTH = WIDTH - 120
LINE_HEIGHT = 24

BTN_Y = HEIGHT - 95
SEND_BTN = pygame.Rect(WIDTH//2 - 170, BTN_Y, 150, 42)
STOP_BTN = pygame.Rect(WIDTH//2 + 20, BTN_Y, 150, 42)
VOICE_BTN = pygame.Rect(WIDTH//2 - 75, BTN_Y - 55, 150, 42)

# ---------------- TTS ----------------
def stop_speaking():
    global speaking
    pygame.mixer.music.stop()
    speaking = False

def speak(text):
    global speaking
    stop_speaking()

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/wav"
    }
    payload = {"text": text, "model_id": TTS_MODEL}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        if r.status_code != 200:
            return

        speaking = True
        audio = io.BytesIO(r.content)
        pygame.mixer.music.load(audio)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except Exception:
        pass

    speaking = False

# ---------------- AI ----------------
def ask_ai(prompt):
    global thinking
    thinking = True
    try:
        reply = chat_with_ai(prompt)
        chat_log.append("You: " + prompt)
        chat_log.append("Jarvis: " + reply)
        speak(reply)
    except Exception:
        pass
    thinking = False

# ---------------- Voice Input ----------------
def voice_listen():
    global listening
    r = sr.Recognizer()
    with sr.Microphone() as src:
        r.adjust_for_ambient_noise(src, duration=0.6)
        listening = True
        try:
            audio = r.listen(src, phrase_time_limit=6)
            query = r.recognize_google(audio)
            threading.Thread(target=ask_ai, args=(query,), daemon=True).start()
        except Exception:
            pass
        listening = False

# ---------------- Button ----------------
def draw_button(rect, text, active=True, danger=False):
    color = (200,60,60) if danger else (0,170,255)
    if not active:
        color = (80,80,80)
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, (255,255,255), rect, 2, border_radius=10)
    label = btn_font.render(text, True, (255,255,255))
    screen.blit(label, label.get_rect(center=rect.center))

# ---------------- Main Loop ----------------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.MOUSEBUTTONDOWN:
            if SEND_BTN.collidepoint(e.pos) and input_text.strip():
                threading.Thread(
                    target=ask_ai,
                    args=(sanitize(input_text),),
                    daemon=True
                ).start()
                input_text = ""

            if STOP_BTN.collidepoint(e.pos):
                stop_speaking()

            if VOICE_BTN.collidepoint(e.pos) and not listening:
                threading.Thread(target=voice_listen, daemon=True).start()

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN and (e.mod & pygame.KMOD_CTRL):
                if input_text.strip():
                    threading.Thread(
                        target=ask_ai,
                        args=(sanitize(input_text),),
                        daemon=True
                    ).start()
                    input_text = ""
            elif e.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif e.unicode:
                input_text += e.unicode

    # ---------------- Draw ----------------
    screen.fill((6,12,22))
    phase = pygame.time.get_ticks() * 0.002

    # ---- Core Animation ----
    cx, cy = WIDTH//2, 240
    r = int(62 + 6 * math.sin(phase))
    for i in range(4):
        arc_r = r + 24 + i * 12
        rect = pygame.Rect(cx-arc_r, cy-arc_r, arc_r*2, arc_r*2)
        pygame.draw.arc(screen, (0,160+i*20,255),
                        rect, phase+i, phase+i+1.6, 3)
    pygame.draw.circle(screen, (0,200,255), (cx,cy), r, 3)

    wrapped_lines = []

    for msg in chat_log:
        wrapped = wrap_text(msg, font, TEXT_AREA_WIDTH)
        wrapped_lines.extend(wrapped)
        wrapped_lines.append("")  # blank line between messages

    max_lines = TEXT_AREA_HEIGHT // LINE_HEIGHT
    visible_lines = wrapped_lines[-max_lines:]

    y = TEXT_AREA_TOP
    for ln in visible_lines:
        screen.blit(
            font.render(ln, True, (190, 230, 255)),
            (TEXT_AREA_LEFT, y)
        )
        y += LINE_HEIGHT


    # ---- Input Box ----
    box = pygame.Rect(50, HEIGHT-240, WIDTH-100, 120)
    pygame.draw.rect(screen, (25,35,55), box, border_radius=10)
    pygame.draw.rect(screen, (0,200,255), box, 2, border_radius=10)

    y = box.y + 10
    for line in input_text.split("\n")[-4:]:
        screen.blit(big_font.render(line, True, (220,240,255)),
                    (box.x+12, y))
        y += 28

    # ---- Buttons ----
    draw_button(VOICE_BTN, "🎤 VOICE", not listening)
    draw_button(SEND_BTN, "SEND", not thinking)
    draw_button(STOP_BTN, "STOP", speaking, danger=True)

    pygame.display.flip()
    clock.tick(60)
