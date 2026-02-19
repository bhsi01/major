import tkinter as tk
from tkinter import scrolledtext
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

def read_text(text):
    """Speak text in a separate thread"""
    def run():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()


messages = [{"role": "system", "content": "You are Jarvis, an advanced helpful AI assistant."}]

def run_ai(query):
    """Send query to AI and return response text"""
    global messages
    try:
        messages.append({"role": "user", "content": query})
        chat_display.insert(tk.END, "Jarvis: Thinking...\n", "thinking")
        chat_display.see(tk.END)
        chat = client.chat.completions.create(model=GROQ_MODEL, messages=messages)
        response = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": response})
        chat_display.delete("end-2l", "end-1l")
        return response
    except Exception as e:
        return f"Error connecting to Groq servers: {e}"


def process_command(query):
    q = query.lower()

    if any(word in q for word in ["exit", "quit"]):
        read_text("Goodbye sir.")
        root.destroy()
        return "Exiting…"

    if "open youtube" in q:
        read_text("Opening YouTube sir.")
        webbrowser.open("https://youtube.com")
        return "Opening YouTube…"

    if "open google" in q:
        read_text("Opening Google sir.")
        webbrowser.open("https://google.com")
        return "Opening Google…"

    if "play music" in q:
        music_dir = "E:\\Music"
        if os.path.exists(music_dir):
            songs = os.listdir(music_dir)
            if songs:
                read_text("Playing music.")
                os.startfile(os.path.join(music_dir, songs[0]))
                return "Playing music…"
        return "Music folder not found."

    if "time" in q:
        reply = f"Sir, the time is {datetime.datetime.now().strftime('%H:%M:%S')}"
        return reply

    if "open vs code" in q:
        path = r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        if os.path.exists(path):
            read_text("Opening VS Code.")
            os.startfile(path)
            return "Opening VS Code…"
        return "VS Code not found."

    if "open notepad" in q:
        read_text("Opening Notepad.")
        os.system("start notepad.exe")
        return "Opening Notepad…"

    if "open calculator" in q:
        read_text("Opening Calculator.")
        os.system("start calc.exe")
        return "Opening Calculator…"

    response = run_ai(query)
    return response


listening = False

def continuous_voice_input():
    global listening
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        chat_display.insert(tk.END, "Jarvis: Voice chat started. Listening...\n", "jarvis")
        chat_display.see(tk.END)
        while listening:
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=8)
                if audio:
                    def process_audio(audio_data):
                        try:
                            query = r.recognize_google(audio_data, language="en-in")
                            if query.strip():
                                chat_display.insert(tk.END, f"You: {query}\n", "user")
                                chat_display.see(tk.END)
                                reply = process_command(query)
                                chat_display.insert(tk.END, f"Jarvis: {reply}\n", "jarvis")
                                chat_display.see(tk.END)
                                read_text(reply)
                        except sr.UnknownValueError:
                            pass  # Ignore silence

                    threading.Thread(target=process_audio, args=(audio,), daemon=True).start()
            except Exception:
                continue
        chat_display.insert(tk.END, "Jarvis: Voice chat ended.\n", "jarvis")
        chat_display.see(tk.END)

def start_voice_chat():
    global listening
    if not listening:
        listening = True
        threading.Thread(target=continuous_voice_input, daemon=True).start()
        voice_button.config(text="🎤 Voice Chat Active", bg="#2ecc71", state=tk.DISABLED)

def end_voice_chat():
    global listening
    listening = False
    voice_button.config(text="🎤 Voice", bg="#4a90e2", state=tk.NORMAL)


def send_input():
    query = user_input.get()
    if not query.strip():
        return
    chat_display.insert(tk.END, f"You: {query}\n", "user")
    chat_display.see(tk.END)
    user_input.delete(0, tk.END)

    def process_and_speak():
        reply = process_command(query)
        chat_display.insert(tk.END, f"Jarvis: {reply}\n", "jarvis")
        chat_display.see(tk.END)
        read_text(reply)

    threading.Thread(target=process_and_speak).start()

def clear_chat():
    chat_display.delete(1.0, tk.END)

def stop_speech():
    engine.stop()

def start_greeting():
    greeting = "Hello sir, I am J.A.R.V.I.S. How may I assist you today?"
    chat_display.insert(tk.END, f"Jarvis: {greeting}\n", "jarvis")
    chat_display.see(tk.END)
    read_text(greeting)


root = tk.Tk()
root.title("J.A.R.V.I.S - Just A Rather Very Intelligent System")
root.geometry("800x700")
root.configure(bg="#1e1e1e")

styles = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "accent": "#4a90e2",
    "secondary": "#2d2d2d",
    "user_bg": "#2d2d2d",
    "jarvis_bg": "#1a3c5c",
    "error_bg": "#5c1a1a"
}

chat_display = scrolledtext.ScrolledText(
    root, wrap=tk.WORD, width=80, height=25, font=("Arial", 11),
    bg=styles["secondary"], fg=styles["fg"], insertbackground=styles["fg"],
    relief=tk.FLAT, padx=10, pady=10
)
chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

chat_display.tag_configure("user", background=styles["user_bg"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
chat_display.tag_configure("jarvis", background=styles["jarvis_bg"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
chat_display.tag_configure("error", background=styles["error_bg"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
chat_display.tag_configure("thinking", background=styles["jarvis_bg"], foreground="#aaaaaa", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)


user_input = tk.Entry(root, font=("Arial", 12), bg=styles["secondary"], fg=styles["fg"], insertbackground=styles["fg"], relief=tk.FLAT)
user_input.pack(fill=tk.X, side=tk.LEFT, padx=10, pady=5)
user_input.bind("<Return>", lambda event: send_input())
user_input.focus()


button_frame = tk.Frame(root, bg=styles["bg"])
button_frame.pack(fill=tk.X, padx=10, pady=5)

def create_button(parent, text, command, bg=styles["accent"], width=12):
    return tk.Button(parent, text=text, command=command, bg=bg, fg=styles["fg"], font=("Arial", 10, "bold"), relief=tk.FLAT, width=width, cursor="hand2")

send_button = create_button(button_frame, "📤 Send", send_input)
send_button.pack(side=tk.LEFT, padx=(0,5))

voice_button = create_button(button_frame, "🎤 Voice", start_voice_chat)
voice_button.pack(side=tk.LEFT, padx=5)

end_voice_button = create_button(button_frame, "⏹️ End Voice", end_voice_chat, bg="#e74c3c")
end_voice_button.pack(side=tk.LEFT, padx=5)

clear_button = create_button(button_frame, "🗑️ Clear", clear_chat, bg="#e74c3c")
clear_button.pack(side=tk.LEFT, padx=5)

stop_button = create_button(button_frame, "⏹️ Stop", stop_speech, bg="#e67e22")
stop_button.pack(side=tk.LEFT, padx=5)


threading.Thread(target=start_greeting).start()

root.mainloop()
