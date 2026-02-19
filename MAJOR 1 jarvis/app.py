import pygame
import sys
import threading
import math
import sqlite3
import queue
import re

from ai import chat_with_ai
from db import create_chat, get_chats, save_message, load_messages
from voice import listen

import pyttsx3

pygame.init()

# ---------------- Window ----------------
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("J.A.R.V.I.S")

font = pygame.font.SysFont("consolas", 17)
bold_font = pygame.font.SysFont("consolas", 18, bold=True)
title_font = pygame.font.SysFont("consolas", 22, bold=True)

clock = pygame.time.Clock()

# ---------------- Layout ----------------
SIDEBAR_W = 300
CHAT_X = SIDEBAR_W + 20
CHAT_W = WIDTH - CHAT_X - 20
CHAT_TOP = 80
CHAT_H = HEIGHT - 260
LINE_H = 24

INPUT_BOX = pygame.Rect(CHAT_X, HEIGHT - 160, CHAT_W, 100)

SEND_BTN = pygame.Rect(WIDTH - 160, HEIGHT - 50, 120, 40)
VOICE_BTN = pygame.Rect(WIDTH - 320, HEIGHT - 50, 140, 40)

NEW_BTN = pygame.Rect(20, HEIGHT - 110, SIDEBAR_W - 40, 40)
DEL_BTN = pygame.Rect(20, HEIGHT - 60, SIDEBAR_W - 40, 40)

# ---------------- State ----------------
current_chat_id, _, _ = create_chat()
chat_log = []
input_text = ""
thinking = False

listening = False
glow_phase = 0

chat_list = get_chats()
chat_buttons = []

# ---------------- Utils ----------------
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
    global chat_log, current_chat_id
    chat_log = []
    current_chat_id = chat_id
    for r, c in load_messages(chat_id):
        chat_log.append(f"{r}: {c}")

def delete_chat(chat_id):
    conn = sqlite3.connect("chats.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    cur.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

# ---------------- Voice (pyttsx3 queue) ----------------
speak_queue = queue.Queue()
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

def speaker_loop():
    while True:
        text = speak_queue.get()
        if text is None:
            break
        sentences = re.split(r'(?<=[.!?]) +', text)
        for s in sentences:
            if s.strip():
                engine.say(s.strip())
        engine.runAndWait()
        speak_queue.task_done()

threading.Thread(target=speaker_loop, daemon=True).start()

def speak(text):
    speak_queue.put(text)

# ---------------- AI ----------------
def ask_ai(prompt):
    global thinking
    thinking = True
    reply = chat_with_ai(prompt)
    save_message(current_chat_id, "Jarvis", reply)
    chat_log.append(f"Jarvis: {reply}")
    speak(reply)
    thinking = False

# ---------------- Voice Thread ----------------
def voice_thread():
    global listening, input_text
    spoken = listen()
    listening = False
    input_text = ""

    if spoken:
        save_message(current_chat_id, "You", spoken)
        chat_log.append(f"You: {spoken}")
        threading.Thread(target=ask_ai, args=(spoken,), daemon=True).start()

# ---------------- Main Loop ----------------
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
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:

            # SEND (TEXT)
            if SEND_BTN.collidepoint(e.pos) and input_text.strip() and not thinking:
                msg = input_text.strip()
                input_text = ""
                save_message(current_chat_id, "You", msg)
                chat_log.append(f"You: {msg}")
                threading.Thread(target=ask_ai, args=(msg,), daemon=True).start()

            # VOICE
            if VOICE_BTN.collidepoint(e.pos) and not thinking and not listening:
                listening = True
                glow_phase = 0
                input_text = "Listening..."
                threading.Thread(target=voice_thread, daemon=True).start()

            # NEW CHAT
            if NEW_BTN.collidepoint(e.pos):
                current_chat_id, _, _ = create_chat()
                chat_log = []
                chat_list = get_chats()

            # DELETE CHAT
            if DEL_BTN.collidepoint(e.pos) and chat_list:
                delete_chat(current_chat_id)
                chat_list = get_chats()
                if chat_list:
                    load_chat(chat_list[0][0])
                else:
                    current_chat_id, _, _ = create_chat()
                    chat_log = []

            # LOAD CHAT
            for rect, cid in chat_buttons:
                if rect.collidepoint(e.pos):
                    load_chat(cid)
                    break

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif e.unicode:
                input_text += e.unicode

    # ---------------- Draw ----------------
    screen.fill((8, 12, 24))

    pygame.draw.rect(screen, (12, 20, 40), (0, 0, WIDTH, 60))
    screen.blit(title_font.render("J.A.R.V.I.S", True, (0, 200, 255)), (20, 18))

    pygame.draw.rect(screen, (14, 22, 42), (0, 60, SIDEBAR_W, HEIGHT))
    screen.blit(bold_font.render("Chats", True, (200, 220, 255)), (20, 80))

    chat_buttons.clear()
    y = 120
    for cid, num, ts in chat_list:
        rect = pygame.Rect(20, y, SIDEBAR_W - 40, 36)
        chat_buttons.append((rect, cid))

        hovered = rect.collidepoint(mouse_pos)
        active = cid == current_chat_id

        color = (40, 60, 90)
        if active:
            color = (0, 170, 255)
        elif hovered:
            color = (80, 120, 180)

        pygame.draw.rect(screen, color, rect, border_radius=6)
        screen.blit(font.render(f"#{num} • {ts}", True, (255, 255, 255)),
                    (rect.x + 10, rect.y + 9))
        y += 44

    # Sidebar buttons
    for btn, label, base, hover in [
        (NEW_BTN, "＋ New Chat", (0, 180, 255), (80, 220, 255)),
        (DEL_BTN, "🗑 Delete Chat", (200, 60, 60), (255, 90, 90))
    ]:
        color = hover if btn.collidepoint(mouse_pos) else base
        pygame.draw.rect(screen, color, btn, border_radius=8)
        screen.blit(bold_font.render(label, True, (255, 255, 255)),
                    (btn.x + 40, btn.y + 10))

    # Chat text
    lines = []
    for msg in chat_log:
        lines.extend(wrap_text(msg, CHAT_W))
        lines.append("")
    lines = lines[-(CHAT_H // LINE_H):]

    y = CHAT_TOP
    for ln in lines:
        screen.blit(font.render(ln, True, (210, 230, 255)), (CHAT_X, y))
        y += LINE_H

    # Input box
    pygame.draw.rect(screen, (20, 30, 55), INPUT_BOX, border_radius=8)
    pygame.draw.rect(screen, (0, 180, 255), INPUT_BOX, 2, border_radius=8)
    screen.blit(font.render(input_text, True, (255, 255, 255)),
                (INPUT_BOX.x + 10, INPUT_BOX.y + 10))

    # SEND
    send_color = (80, 220, 255) if SEND_BTN.collidepoint(mouse_pos) else (0, 180, 255)
    pygame.draw.rect(screen, send_color, SEND_BTN, border_radius=8)
    screen.blit(bold_font.render("SEND", True, (255, 255, 255)),
                (SEND_BTN.x + 32, SEND_BTN.y + 10))

    # VOICE + GLOW
    if listening:
        glow_phase += 0.2
        pulse = int(20 + 12 * abs(math.sin(glow_phase)))
        for i in range(3):
            r = VOICE_BTN.inflate(pulse + i * 18, pulse + i * 18)
            s = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 220, 255, 40 - i * 10),
                             s.get_rect(), border_radius=18)
            screen.blit(s, r.topleft)

    voice_color = (160, 220, 255) if VOICE_BTN.collidepoint(mouse_pos) else (120, 180, 255)
    pygame.draw.rect(screen, voice_color, VOICE_BTN, border_radius=10)
    screen.blit(bold_font.render("🎤 VOICE", True, (0, 0, 0)),
                (VOICE_BTN.x + 25, VOICE_BTN.y + 10))

    pygame.display.flip()
    clock.tick(60)
