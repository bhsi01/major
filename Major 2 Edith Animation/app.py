import pygame
import sys
import threading
import math
import sqlite3
import requests
import io
import time

from ai import chat_with_ai
from db import create_chat, get_chats, save_message, load_messages
from voice import listen
from config import ELEVEN_API_KEY, VOICE_ID, TTS_MODEL

pygame.init()
pygame.mixer.init()

#Window code
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("E.D.I.T.H")

font = pygame.font.SysFont("consolas", 17)
bold_font = pygame.font.SysFont("consolas", 18, bold=True)
title_font = pygame.font.SysFont("consolas", 22, bold=True)

clock = pygame.time.Clock()

SIDEBAR_W = 300 #layout

# set animation and text area 
ANIM_H = int(HEIGHT * 0.55)
CHAT_TOP = ANIM_H - 50  
CHAT_H = HEIGHT - CHAT_TOP - 20 - 60  
CHAT_X = SIDEBAR_W + 20
CHAT_W = WIDTH - CHAT_X - 40
LINE_H = 24

CHAT_AREA = pygame.Rect(CHAT_X, CHAT_TOP, CHAT_W, CHAT_H)

INPUT_HEIGHT = 60
INPUT_BOX = pygame.Rect(CHAT_X, HEIGHT - INPUT_HEIGHT - 20, CHAT_W, INPUT_HEIGHT)

# Buttons in input box
BTN_WIDTH = 100
BTN_HEIGHT = 36
BTN_MARGIN = 10
SEND_BTN = pygame.Rect(INPUT_BOX.right - BTN_WIDTH - BTN_MARGIN, INPUT_BOX.y + INPUT_BOX.height - BTN_HEIGHT - BTN_MARGIN, BTN_WIDTH, BTN_HEIGHT)
VOICE_BTN = pygame.Rect(SEND_BTN.left - BTN_WIDTH - BTN_MARGIN, SEND_BTN.y, BTN_WIDTH, BTN_HEIGHT)
STOP_BTN = pygame.Rect(VOICE_BTN.left - BTN_WIDTH - BTN_MARGIN, SEND_BTN.y, BTN_WIDTH, BTN_HEIGHT)

NEW_BTN = pygame.Rect(20, HEIGHT - 110, SIDEBAR_W - 40, 40)
DEL_BTN = pygame.Rect(20, HEIGHT - 60, SIDEBAR_W - 40, 40)

#Set State
current_chat_id, _, _ = create_chat()
chat_log = []
input_text = ""
thinking = False
listening = False
glow_phase = 0
speaking = False
stop_speech_flag = threading.Event()
scroll_offset = 0
auto_scroll = True

chat_list = get_chats()
chat_buttons = []

#Utils
def wrap_text(text, max_w):
    words = text.split(" ")
    lines, line = [], ""
    for w in words:
        test = line + w + " "
        if font.size(test)[0] <= max_w:
            line = test
        else:
            lines.append(line)
            line = w + " "
    lines.append(line)
    return lines

def load_chat(chat_id):
    global chat_log, current_chat_id, scroll_offset
    chat_log = []
    current_chat_id = chat_id
    for r, c in load_messages(chat_id):
        chat_log.append(f"{r}: {c}")
    scroll_offset = 0

def delete_chat(chat_id):
    conn = sqlite3.connect("chats.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    cur.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

#ElevenLabs
def stop_speaking():
    global speaking
    stop_speech_flag.set()
    pygame.mixer.music.stop()
    speaking = False

def speak(text):
    global speaking
    stop_speaking()
    stop_speech_flag.clear()

    def tts_thread():
        global speaking
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
            headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/wav"
            }
            payload = {"text": text, "model_id": TTS_MODEL}

            r = requests.post(url, json=payload, headers=headers, timeout=20)
            if r.status_code != 200:
                print("TTS failed", r.status_code, r.text)
                return

            speaking = True
            audio = io.BytesIO(r.content)
            pygame.mixer.music.load(audio)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy() and not stop_speech_flag.is_set():
                time.sleep(0.05)

        except Exception as e:
            print("TTS Error:", e)
        finally:
            speaking = False

    threading.Thread(target=tts_thread, daemon=True).start()

#AI
def ask_ai(prompt):
    global thinking, scroll_offset, auto_scroll
    thinking = True
    try:
        reply = chat_with_ai(prompt)
    except Exception as e:
        reply = "Error: Could not get AI response."
        print(e)
    save_message(current_chat_id, "Edith", reply)
    chat_log.append(f"Edith: {reply}")
    auto_scroll = True
    speak(reply)
    thinking = False

#Voice
def voice_thread():
    global listening, input_text
    spoken = listen()
    listening = False
    input_text = ""
    if spoken:
        save_message(current_chat_id, "You", spoken)
        chat_log.append(f"You: {spoken}")
        auto_scroll = True
        threading.Thread(target=ask_ai, args=(spoken,), daemon=True).start()

#Main Loop
while True:
    mouse_pos = pygame.mouse.get_pos()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif e.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif e.key == pygame.K_UP:
                auto_scroll = False
                scroll_offset -= LINE_H
            elif e.key == pygame.K_DOWN:
                auto_scroll = False
                scroll_offset += LINE_H
            elif e.unicode:
                input_text += e.unicode

        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                if SEND_BTN.collidepoint(e.pos) and input_text.strip() and not thinking:
                    msg = input_text.strip()
                    input_text = ""
                    save_message(current_chat_id, "You", msg)
                    chat_log.append(f"You: {msg}")
                    auto_scroll = True
                    threading.Thread(target=ask_ai, args=(msg,), daemon=True).start()

                if VOICE_BTN.collidepoint(e.pos) and not listening and not thinking:
                    listening = True
                    glow_phase = 0
                    input_text = "Listening..."
                    threading.Thread(target=voice_thread, daemon=True).start()

                if STOP_BTN.collidepoint(e.pos):
                    stop_speaking()

                if NEW_BTN.collidepoint(e.pos):
                    current_chat_id, _, _ = create_chat()
                    chat_log = []
                    chat_list = get_chats()
                    scroll_offset = 0

                if DEL_BTN.collidepoint(e.pos) and chat_list:
                    delete_chat(current_chat_id)
                    chat_list = get_chats()
                    if chat_list:
                        load_chat(chat_list[0][0])
                    else:
                        current_chat_id, _, _ = create_chat()
                        chat_log = []
                        scroll_offset = 0

                for rect, cid in chat_buttons:
                    if rect.collidepoint(e.pos):
                        load_chat(cid)
                        break

            if e.button == 4:
                scroll_offset -= LINE_H
                auto_scroll = False
            elif e.button == 5:
                scroll_offset += LINE_H
                auto_scroll = False

    #Draw animation
    phase = pygame.time.get_ticks() * 0.002
    cx, cy = WIDTH // 2, ANIM_H // 2
    max_radius = int(min(WIDTH, ANIM_H) * 0.65 / 2)
    r = int(max_radius * 0.3 + 6 * math.sin(phase))

    screen.fill((8, 12, 24))

    for i in range(4):
        arc_r = int(r + max_radius * 0.2 + i * (max_radius * 0.15))
        rect = pygame.Rect(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        pygame.draw.arc(screen, (0, 160, 255), rect, phase + i, phase + i + 1.6, 3)

    pygame.draw.circle(screen, (0, 200, 255), (cx, cy), r, 3)

    #Sidebar and title
    pygame.draw.rect(screen, (12, 20, 40), (0, 0, WIDTH, 60))
    screen.blit(title_font.render("E.D.I.T.H", True, (0, 200, 255)), (20, 18))
    pygame.draw.rect(screen, (14, 22, 42), (0, 60, SIDEBAR_W, HEIGHT))
    screen.blit(bold_font.render("Chats", True, (200, 220, 255)), (20, 80))

    # Chat buttons
    chat_buttons.clear()
    y = 120
    for cid, num, ts in chat_list:
        rect = pygame.Rect(20, y, SIDEBAR_W - 40, 36)
        chat_buttons.append((rect, cid))
        hovered = rect.collidepoint(mouse_pos)
        active = cid == current_chat_id
        color = (40, 60, 90)
        if active: color = (0, 170, 255)
        elif hovered: color = (80, 120, 180)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        screen.blit(font.render(f"#{num} • {ts}", True, (255, 255, 255)), (rect.x + 10, rect.y + 9))
        y += 44

    for btn, label, base, hover in [
        (NEW_BTN, "＋ New Chat", (0, 180, 255), (80, 220, 255)),
        (DEL_BTN, "🗑 Delete Chat", (200, 60, 60), (255, 90, 90))
    ]:
        color = hover if btn.collidepoint(mouse_pos) else base
        pygame.draw.rect(screen, color, btn, border_radius=8)
        screen.blit(bold_font.render(label, True, (255, 255, 255)), (btn.x + 40, btn.y + 10))

    #Chat messages area
    lines = []
    for msg in chat_log:
        lines.extend(wrap_text(msg, CHAT_W))
        lines.append("")

    total_height = len(lines) * LINE_H
    max_scroll = max(total_height - CHAT_AREA.h, 0)
    scroll_offset = min(max(scroll_offset, 0), max_scroll)
    if auto_scroll:
        scroll_offset = max_scroll

    chat_surface = pygame.Surface((CHAT_AREA.w, CHAT_AREA.h), pygame.SRCALPHA)  # transparent
    y = -scroll_offset
    for ln in lines:
        if y + LINE_H > 0 and y < CHAT_AREA.h:
            chat_surface.blit(font.render(ln, True, (210, 230, 255)), (0, y))
        y += LINE_H
    screen.blit(chat_surface, CHAT_AREA.topleft)

    #Input box
    pygame.draw.rect(screen, (20, 30, 55), INPUT_BOX, border_radius=8)
    pygame.draw.rect(screen, (0, 180, 255), INPUT_BOX, 2, border_radius=8)
    screen.blit(font.render(input_text, True, (255, 255, 255)), (INPUT_BOX.x + 10, INPUT_BOX.y + 10))

    # Buttons inside input box
    for btn, text, base, hover, danger in [
        (SEND_BTN, "SEND", (0,180,255), (80,220,255), False),
        (VOICE_BTN, "🎤 VOICE", (120,180,255), (160,220,255), False),
        (STOP_BTN, "STOP", (200,60,60), (255,90,90), True)
    ]:
        color = hover if btn.collidepoint(mouse_pos) else base
        pygame.draw.rect(screen, color, btn, border_radius=8)
        if danger:
            pygame.draw.rect(screen, (255,255,255), btn, 2, border_radius=8)
        screen.blit(bold_font.render(text, True, (255,255,255)), (btn.x + 15, btn.y + 6))

    # Listening glow
    if listening:
        glow_phase += 0.2
        pulse = int(20 + 12 * abs(math.sin(glow_phase)))
        for i in range(3):
            r_glow = VOICE_BTN.inflate(pulse + i*18, pulse + i*18)
            s = pygame.Surface(r_glow.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 220, 255, 40 - i*10), s.get_rect(), border_radius=18)
            screen.blit(s, r_glow.topleft)

    pygame.display.flip()
    clock.tick(60)
