import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import pyttsx3
import datetime
import speech_recognition as sr
import webbrowser
import os
from groq import Groq
from key import api_key

client = Groq(api_key=api_key)
GROQ_MODEL = "llama-3.1-8b-instant"

engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)
engine.setProperty("rate", 180)
engine.setProperty("volume", 1.0)
stop_speaking = False

def speak(text):
    """Speak text in a thread (interruptible)"""
    global stop_speaking
    stop_speaking = False

    def run():
        engine.say(text)
        engine.runAndWait()

    t = threading.Thread(target=run)
    t.start()
    while t.is_alive():
        if stop_speaking:
            engine.stop()
            break

messages = [
    {"role": "system", "content": "You are Jarvis, an advanced helpful AI assistant."}
]

def run_ai(query):
    global messages
    try:
        messages.append({"role": "user", "content": query})
        chat_display.insert(tk.END, "Jarvis: Thinking...\n", "thinking")
        chat_display.see(tk.END)
        
        chat = client.chat.completions.create(model=GROQ_MODEL, messages=messages)
        response = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": response})
        
        # Remove the "Thinking..." message
        chat_display.delete("end-2l", "end-1l")
        return response
    except Exception as e:
        return f"Error connecting to Groq servers: {e}"
    
def process_command(query):
    q = query.lower()

    if any(word in q for word in ["exit", "quit", "stop"]):
        speak("Goodbye sir.")
        root.destroy()
        return "Exiting…"

    if "open youtube" in q:
        speak("Opening YouTube sir.")
        webbrowser.open("https://youtube.com")
        return "Opening YouTube…"

    if "open google" in q:
        speak("Opening Google.")
        webbrowser.open("https://google.com")
        return "Opening Google…"

    if "play music" in q:
        music_dir = "E:\\Music"
        if os.path.exists(music_dir):
            songs = os.listdir(music_dir)
            if songs:
                speak("Playing music.")
                os.startfile(os.path.join(music_dir, songs[0]))
                return "Playing music…"
        return "Music folder not found."

    if "time" in q:
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        reply = f"Sir, the time is {time_str}"
        speak(reply)
        return reply

    if "open vs code" in q:
        path = r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        if os.path.exists(path):
            speak("Opening VS Code.")
            os.startfile(path)
            return "Opening VS Code…"
        return "VS Code not found."

    if "open notepad" in q:
        speak("Opening Notepad.")
        os.system("start notepad.exe")
        return "Opening Notepad…"

    if "open calculator" in q:
        speak("Opening Calculator.")
        os.system("start calc.exe")
        return "Opening Calculator…"

    response = run_ai(query)
    speak(response)
    return response

def voice_input():
    r = sr.Recognizer()
    
    # Update voice button to show listening state
    voice_button.config(text="🎤 Listening...", bg="#ff6b6b", state=tk.DISABLED)
    root.update()

    try:
        with sr.Microphone() as source:
            chat_display.insert(tk.END, "Jarvis: Listening...\n", "jarvis")
            chat_display.see(tk.END)

            r.adjust_for_ambient_noise(source, duration=1)
            r.dynamic_energy_threshold = True

            audio = r.listen(source, timeout=10, phrase_time_limit=8)

        query = r.recognize_google(audio, language="en-in")
        chat_display.insert(tk.END, f"You: {query}\n", "user")
        chat_display.see(tk.END)

        reply = process_command(query)
        chat_display.insert(tk.END, f"Jarvis: {reply}\n", "jarvis")
        chat_display.see(tk.END)

    except sr.WaitTimeoutError:
        chat_display.insert(tk.END, "Jarvis: No speech detected. Please try again.\n", "error")
        chat_display.see(tk.END)

    except sr.UnknownValueError:
        chat_display.insert(tk.END, "Jarvis: Could not understand audio. Please try again.\n", "error")
        chat_display.see(tk.END)

    except Exception as e:
        chat_display.insert(tk.END, f"Jarvis: Voice Error: {e}\n", "error")
        chat_display.see(tk.END)
    
    finally:
        # Reset voice button
        voice_button.config(text="🎤 Voice", bg="#4a90e2", state=tk.NORMAL)

def send_input():
    query = user_input.get()
    if not query.strip():
        return

    chat_display.insert(tk.END, f"You: {query}\n", "user")
    chat_display.see(tk.END)
    user_input.delete(0, tk.END)

    # Process command in a separate thread to keep UI responsive
    def process_and_display():
        reply = process_command(query)
        chat_display.insert(tk.END, f"Jarvis: {reply}\n", "jarvis")
        chat_display.see(tk.END)
    
    threading.Thread(target=process_and_display).start()

def clear_chat():
    chat_display.delete(1.0, tk.END)

def stop_speech():
    global stop_speaking
    stop_speaking = True

def start_greeting():
    speak("Hello sir, I am J.A.R.V.I.S. How may I assist you today?")
    chat_display.insert(tk.END, "Jarvis: Hello sir, I am J.A.R.V.I.S. How may I assist you today?\n", "jarvis")
    chat_display.see(tk.END)

# Create main window
root = tk.Tk()
root.title("J.A.R.V.I.S - Just A Rather Very Intelligent System")
root.geometry("800x700")
root.configure(bg="#1e1e1e")

# Set window icon (you can add an icon file if desired)
try:
    root.iconbitmap("jarvis_icon.ico")  # Optional: add an icon file
except:
    pass

# Custom styles
styles = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "accent": "#4a90e2",
    "secondary": "#2d2d2d",
    "user_bg": "#2d2d2d",
    "jarvis_bg": "#1a3c5c",
    "error_bg": "#5c1a1a"
}

# Create title frame
title_frame = tk.Frame(root, bg=styles["bg"])
title_frame.pack(fill=tk.X, padx=10, pady=10)

title_label = tk.Label(
    title_frame, 
    text="J.A.R.V.I.S", 
    font=("Arial", 24, "bold"), 
    fg=styles["accent"],
    bg=styles["bg"]
)
title_label.pack(side=tk.LEFT)

subtitle_label = tk.Label(
    title_frame, 
    text="Just A Rather Very Intelligent System", 
    font=("Arial", 10), 
    fg=styles["fg"],
    bg=styles["bg"]
)
subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

# Create chat display area
chat_frame = tk.Frame(root, bg=styles["bg"])
chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

chat_display = scrolledtext.ScrolledText(
    chat_frame, 
    wrap=tk.WORD, 
    width=80, 
    height=25, 
    font=("Arial", 11),
    bg=styles["secondary"],
    fg=styles["fg"],
    insertbackground=styles["fg"],
    relief=tk.FLAT,
    padx=10,
    pady=10
)
chat_display.pack(fill=tk.BOTH, expand=True)

# Configure text tags for different message types
chat_display.tag_configure("user", background=styles["user_bg"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
chat_display.tag_configure("jarvis", background=styles["jarvis_bg"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
chat_display.tag_configure("error", background=styles["error_bg"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
chat_display.tag_configure("thinking", background=styles["jarvis_bg"], foreground="#aaaaaa", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)

# Create input frame
input_frame = tk.Frame(root, bg=styles["bg"])
input_frame.pack(fill=tk.X, padx=10, pady=10)

user_input = tk.Entry(
    input_frame, 
    font=("Arial", 12),
    bg=styles["secondary"],
    fg=styles["fg"],
    insertbackground=styles["fg"],
    relief=tk.FLAT
)
user_input.pack(fill=tk.X, side=tk.LEFT, padx=(0, 10))
user_input.bind("<Return>", lambda event: send_input())
user_input.focus()

# Create button frame
button_frame = tk.Frame(root, bg=styles["bg"])
button_frame.pack(fill=tk.X, padx=10, pady=5)

# Function to create styled buttons
def create_button(parent, text, command, bg=styles["accent"], width=12):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=styles["fg"],
        font=("Arial", 10, "bold"),
        relief=tk.FLAT,
        width=width,
        cursor="hand2"
    )

send_button = create_button(button_frame, "📤 Send", send_input)
send_button.pack(side=tk.LEFT, padx=(0, 5))

voice_button = create_button(button_frame, "🎤 Voice", lambda: threading.Thread(target=voice_input).start())
voice_button.pack(side=tk.LEFT, padx=5)

clear_button = create_button(button_frame, "🗑️ Clear", clear_chat, bg="#e74c3c")
clear_button.pack(side=tk.LEFT, padx=5)

stop_button = create_button(button_frame, "⏹️ Stop", stop_speech, bg="#e67e22")
stop_button.pack(side=tk.LEFT, padx=5)

# Status bar
status_frame = tk.Frame(root, bg=styles["secondary"])
status_frame.pack(fill=tk.X, padx=10, pady=5)

status_label = tk.Label(
    status_frame,
    text="Ready | Voice: Active | AI: Connected",
    font=("Arial", 9),
    fg=styles["fg"],
    bg=styles["secondary"]
)
status_label.pack(side=tk.LEFT, padx=5, pady=2)

# Add some helpful tips
tips_frame = tk.Frame(root, bg=styles["bg"])
tips_frame.pack(fill=tk.X, padx=10, pady=5)

tips_label = tk.Label(
    tips_frame,
    text="💡 Tips: Use voice commands, ask questions, or try 'open youtube', 'what time is it', 'play music'",
    font=("Arial", 9),
    fg="#aaaaaa",
    bg=styles["bg"],
    wraplength=700
)
tips_label.pack()

# Start greeting in a separate thread
threading.Thread(target=start_greeting).start()

root.mainloop()