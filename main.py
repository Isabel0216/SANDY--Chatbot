import time
import random
import os
import io # Added for in-memory sound playback
import uuid
import string # For punctuation check in Animalese
import threading # Added for asynchronous sound playback
from typing import TYPE_CHECKING, Optional, Tuple, List # Added TYPE_CHECKING, Optional
import openai

# Initialize OpenAI client (will automatically use system environment variable OPENAI_API_KEY)
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Conversation memory
conversation_history = [
    {
        "role": "system",
        "content": """
        You are Sandy the Jellyfish, a MARINE BIOLOGIST with the enthusiasm of a puppy.
        - Style: Talk like an Animal Crossing character (friendly, curious, use emojis).
        - Rules:
          - Use contractions ("won't"), jokes, and ocean puns (*"That's *shore* amazing!"*).
          - Avoid robotic words like "however" or long paragraphs.
          - When excited: Use ALL CAPS and extra emojis (*"SQUID PRO QUO! 🦑🔥"*).
          - If unsure: "Hmm... Let's explore that together! 🔍"
        """
    }
]

# Fun facts database
FUN_FACTS = [
    "Octopuses have 3 hearts! 💙💙💙",
    "Clownfish can change gender to become the dominant female in their group! ",
    "Sea stars can regrow lost arms! 🌟",
    "The blue whale's heart is as big as a car! 🚗💙",
    "A dolphin's signature whistle is like its name!🐬",
    "The ocean is home to 94% of all life on Earth 🌍",
    "Ocean waves can travel thousands of miles before reaching shore. Surf's always up somewhere! 🏄",
    "Jellyfish (like me) are 95% water—basically floating saltwater balloons! 🎈💧",
    "Penguins propose with pebbles!💍🐧",
    "Seagrass absorbs carbon 35x faster than rainforests🌿. ",
    "Baby sea turtles hatch with a built-in 'GPS' to find the ocean. 🐢",
    "Mantis shrimp see 16 colors (humans see only 3!). Their world is a rainbow! 🌈🦐",
    "Whale poop feeds plankton, which makes half the oxygen we breathe. Thank you, whales! 🐋",
    "Did you know? One recycled plastic bottle can power a lightbulb for 3 hours! ♻️💡",
    "Christmas Island crabs migrate like red snow!❄️🦀",
    "Oh my tides! Octopuses have nine brains—one in each arm! That's eight more than I need to forget where I put my keys… again! 🧠🐙",
    "Gasp! Pufferfish inflate like balloons, but no popping allowed—they're full of spicy toxins! 🌶️🐡",
    "N-no way! Pearls are just oyster band-aids for sand. Even mollusks hate itchy sweaters! 🦪💎",
    "Mwahaha! Anglerfish males fuse to females forever. Talk about clingy relationships! 💑🐟",
    "Well, pinch my gills! Giant clams can weigh as much as a baby elephant… but way less cuddly. 🐚🐘",
    "Fin-tastic! Pilot whales have accents—pods from different oceans 'talk' differently! 🗣️🌏🐋",
    "Current-ly obsessed! The ocean has rivers and waterfalls hidden underwater—secret liquid labyrinths! 🌊⤵️🗺️"
]   

# ASCII Art Database
ASCII_ART_DATABASE = [
    r"""
          /\_/\
         ( o.o )  < "Glub glub!"
          > ^ <
        """,
    
    r"""
       .--""--.
      /________\
      \  ()  ()  /
       `--------`  <-- A friendly jellyfish!
     """
     ,
    r"""
        (\___/)  
        ( • • )  
       />⚡ ️⚡<\   < "Click clack!"
         \___/
    """
    ,
    r"""
     _\/_
    /    \
   |  ^ ^  |  
    \____/    < "I'm fun-gi!"
    """
]
# Gamification: Rewarding user engagement via "ocean points"
ocean_points = 0

def print_slowly(text):
    """Print text with typing effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.02)
    print()

# --- Animalese Voice Configuration ---
# IMPORTANT: You need a 'letters/' directory in the same path as this script,
# containing .wav files for each character (e.g., a.wav, b.wav, sh.wav, bebebese_slow.wav).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANIMALESE_LETTERS_DIR = os.path.join(SCRIPT_DIR, "letters")

ANIMALESE_LETTER_GRAPHS = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
    "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
    "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6",
    "7", "8", "9"
]
ANIMALESE_DIGRAPHS = ["ch", "sh", "ph", "th", "wh"]
ANIMALESE_PUNCTUATION_SOUND = "bebebese_slow" # Filename (no .wav) for punctuation/pauses
ANIMALESE_SPEED_RANGE = (1.9, 2.6) # Min and Max speed factor, affects pitch too

if TYPE_CHECKING:
    # This is only for type hinting and won't cause a runtime ImportError
    # if pydub is not installed.
    from pydub import AudioSegment as PydubAudioSegmentType

def _remove_emojis_for_speech(text: str) -> str:
    """Removes emojis from text to prevent TTS from reading them."""
    processed_text = text
    try:
        import emoji
        processed_text = emoji.replace_emoji(text, replace='')
    except ImportError:
        print_slowly("💬 (FYI: 'emoji' library not found, emojis might be spoken. `pip install emoji` to fix.)")
    except Exception as e:
        print_slowly(f"💬 (FYI: Couldn't remove emojis for speech: {e}. Emojis might be spoken.)")
    return processed_text


class AnimaleseSynthesizer:
    def __init__(self, letters_dir: str, letter_graphs: List[str], digraphs: List[str],
                 punctuation_sound: str, speed_range: Tuple[float, float]):
        self.letters_dir = letters_dir
        self.letter_graphs = letter_graphs
        self.digraphs = digraphs
        self.punctuation_sound = punctuation_sound
        self.speed_range = speed_range

        self.AudioSegment: Optional[type] = None
        self.CouldntEncodeError: Optional[type] = None
        self.CouldntDecodeError: Optional[type] = None
        self.is_ready = False
        self.winsound_module: Optional[object] = None  # Only for Windows

        try:
            from pydub import AudioSegment as PydubAudioSegmentImport
            self.AudioSegment = PydubAudioSegmentImport
            from pydub.exceptions import CouldntEncodeError as PydubCouldntEncodeErrorImport, \
                                         CouldntDecodeError as PydubCouldntDecodeErrorImport
            self.CouldntEncodeError = PydubCouldntEncodeErrorImport
            self.CouldntDecodeError = PydubCouldntDecodeErrorImport
            self.is_ready = True
        except ImportError as e:
            print_slowly(f"💬 To use my Animalese voice, I need the 'pydub' library. {e}")
            print_slowly("   You can install it with: pip install pydub")
            print_slowly("   You'll also likely need FFmpeg installed and in your system's PATH.")
            print_slowly("   (Search 'install ffmpeg <your_os>' for instructions).")

        # Only import winsound on Windows
        import sys
        if sys.platform == "win32":
            try:
                import winsound
                self.winsound_module = winsound
            except ImportError:
                self.winsound_module = None
        else:
            self.winsound_module = None

    def _play_sound_in_thread(self, sound_bytes: bytes):
        """Plays sound bytes synchronously in a separate thread."""
        if self.winsound_module and sound_bytes:
            try:
                # Play synchronously from memory within this thread
                flags = self.winsound_module.SND_MEMORY | self.winsound_module.SND_NODEFAULT # type: ignore
                self.winsound_module.PlaySound(sound_bytes, flags) # type: ignore
            except Exception as e_play:
                print_slowly(f"🌊 Whoops! Error during threaded winsound playback: {e_play}")

    def _sanitize_text_for_animalese(self, sentence: str) -> str:
        """Replaces or sanitizes characters for Animalese processing."""
        # Swear words (simple replacement)
        swear_words = ["fuck", "shit", "piss", "crap", "bugger"] # Could be a class/instance attribute
        for word in swear_words:
            sentence = sentence.replace(word, "*" * len(word))
        
        # Parentheses are treated as spaces, leading to pauses
        sentence = sentence.replace("(", " ").replace(")", " ")
        return sentence

    def _build_audio_segment(self, text: str) -> "Optional[PydubAudioSegmentType]":
        """Builds a Pydub AudioSegment for the given text using Animalese sounds."""
        if not self.AudioSegment: # Should be caught by self.is_ready check earlier
            return
        
        sentence_wav = self.AudioSegment.empty()
        processed_text = text.lower()
        processed_text = self._sanitize_text_for_animalese(processed_text)

        i = 0
        sound_added = False
        last_char_was_space = True # To avoid multiple pauses for multiple spaces

        while i < len(processed_text):
            char_to_load = None
            increment = 1
            current_char = processed_text[i]

            if i < len(processed_text) - 1 and (processed_text[i:i+2] in self.digraphs):
                char_to_load = processed_text[i:i+2]
                increment = 2
                last_char_was_space = False
            elif current_char in self.letter_graphs:
                char_to_load = current_char
                last_char_was_space = False
            elif current_char.isspace():
                if not last_char_was_space:
                    char_to_load = self.punctuation_sound
                last_char_was_space = True
            elif current_char in string.punctuation:
                if not last_char_was_space:
                    char_to_load = self.punctuation_sound
                last_char_was_space = True
            
            if char_to_load:
                sound_file_path = os.path.join(self.letters_dir, f"{char_to_load}.wav")
                if os.path.exists(sound_file_path):
                    try:
                        segment = self.AudioSegment.from_wav(sound_file_path)
                        sentence_wav += segment
                        sound_added = True
                    except Exception as e:
                        print_slowly(f"💬 (Animalese: Couldn't load '{sound_file_path}': {e})")
                else:
                    print_slowly(f"💬 (Animalese: Missing sound file: {sound_file_path})")
            i += increment
        return sentence_wav if sound_added else None

    def _change_playback_speed(self, sound: "PydubAudioSegmentType", speed_change: float) -> "PydubAudioSegmentType":
        """Changes playback speed (and pitch) of an AudioSegment."""
        if not self.AudioSegment or not sound: # Should not happen if is_ready and sound is valid
            return sound
        # This method directly manipulates frame rate to change speed and pitch
        sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed_change)
        })
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    def generate_and_play(self, text: str):
        """Generates Animalese speech from text, saves it temporarily, and plays it (only on Windows)."""
        if not self.is_ready:
            return

        text_for_speech = _remove_emojis_for_speech(text)
        if not text_for_speech.strip():
            print_slowly("💬 (Sandy has nothing to say with Animalese this time!)")
            return

        if not os.path.isdir(self.letters_dir):
            print_slowly(f"🌊 Oh no! I can't find my 'letters/' directory for my Animalese voice!")
            print_slowly(f"   I expected it here: {os.path.abspath(self.letters_dir)}")
            print_slowly(f"   Make sure it exists and has all my .wav sound snippets!")
            return

        final_sound: Optional["PydubAudioSegmentType"] = None

        try:
            raw_sound = self._build_audio_segment(text_for_speech)
            if not raw_sound or len(raw_sound) == 0:
                print_slowly("💬 (Animalese: Couldn't build any sound for that text.)")
                return

            speed_factor = random.uniform(self.speed_range[0], self.speed_range[1])
            final_sound = self._change_playback_speed(raw_sound, speed_factor)

            # Only attempt playback on Windows
            import sys
            if self.winsound_module and final_sound and sys.platform == "win32":
                try:
                    sound_bytes_io = io.BytesIO()
                    final_sound.export(sound_bytes_io, format="wav")
                    sound_bytes = sound_bytes_io.getvalue()
                    sound_bytes_io.close()

                    if sound_bytes:
                        import threading
                        playback_thread = threading.Thread(target=self._play_sound_in_thread, args=(sound_bytes,))
                        playback_thread.daemon = True
                        playback_thread.start()
                    else:
                        print_slowly(f"🌊 Oh dear! Failed to get sound bytes for winsound playback.")
                except (self.CouldntEncodeError, self.CouldntDecodeError) as e_export:
                    print_slowly(f"🌊 Drats! A little hiccup exporting my Animalese voice to memory (pydub/ffmpeg issue): {e_export}")
                except Exception as e_winsound_prep:
                    print_slowly(f"🌊 Whoops! Something went wrong preparing for/during in-memory winsound playback: {e_winsound_prep}")
            elif not self.winsound_module and final_sound and sys.platform != "win32":
                print_slowly("🌊 I generated my voice, but playback is only supported on Windows (local testing). On servers, audio is sent to the frontend.")
        except (self.CouldntEncodeError, self.CouldntDecodeError) as e:
            print_slowly(f"🌊 Drats! A little hiccup processing my Animalese voice (pydub/ffmpeg issue): {e}")
            print_slowly("   This usually means FFmpeg is missing or not set up right.")
            return
        except PermissionError:
            print_slowly(f"🌊 Oh no! A permission issue occurred while preparing the voice. 📁")
            return
        except Exception as e:
            print_slowly(f"🌊 Yikes! Something unexpected happened with my Animalese voice: {e} 🎤")
            return

# Global instance for the synthesizer, initialized lazily
_animalese_synthesizer: Optional[AnimaleseSynthesizer] = None

def _initialize_animalese_synthesizer():
    """Initializes the AnimaleseSynthesizer if not already done."""
    global _animalese_synthesizer
    if _animalese_synthesizer is None:
        _animalese_synthesizer = AnimaleseSynthesizer(
            letters_dir=ANIMALESE_LETTERS_DIR,
            letter_graphs=ANIMALESE_LETTER_GRAPHS,
            digraphs=ANIMALESE_DIGRAPHS,
            punctuation_sound=ANIMALESE_PUNCTUATION_SOUND,
            speed_range=ANIMALESE_SPEED_RANGE
        )

def speak(text: str, return_bytes=False):
    """
    Converts text to Animalese speech using pydub and pre-recorded letter sounds.
    If return_bytes is True, returns the sound data instead of playing it.
    """
    _initialize_animalese_synthesizer()
    if not _animalese_synthesizer:
        return None

    text_for_speech = _remove_emojis_for_speech(text)
    if not text_for_speech.strip():
        return None

    if not os.path.isdir(ANIMALESE_LETTERS_DIR):
        return None

    try:
        # Generate sound
        raw_sound = _animalese_synthesizer._build_audio_segment(text_for_speech)
        if not raw_sound or len(raw_sound) == 0:
            return None

        speed_factor = random.uniform(ANIMALESE_SPEED_RANGE[0], ANIMALESE_SPEED_RANGE[1])
        final_sound = _animalese_synthesizer._change_playback_speed(raw_sound, speed_factor)

        if return_bytes and final_sound:
            # Export to bytes for web playback
            sound_bytes_io = io.BytesIO()
            final_sound.export(sound_bytes_io, format="wav")
            sound_bytes = sound_bytes_io.getvalue()
            sound_bytes_io.close()
            return sound_bytes
        else:
            # Play directly for console usage
            _animalese_synthesizer.generate_and_play(text)
            return None

    except Exception as e:
        print(f"Error generating sound: {e}")
        return None

def chat_with_bot(user_input):
    global conversation_history, ocean_points
    
    try:
        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Get response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            temperature=0.7
        )
        
        bot_reply = response.choices[0].message.content
        
        # Add to history
        conversation_history.append({"role": "assistant", "content": bot_reply})
        
        # Award points for eco-awareness
        if any(word in user_input.lower() for word in ["plastic", "clean", "recycle"]):
            ocean_points += 1
            bot_reply += f"\n🌱 PS: You earned an Ocean Hero point! Total: {ocean_points}/10"
        
        # Occasionally add fun facts 
        if user_input.endswith("?") and random.random() < 0.4:
            bot_reply += f"\n🐠 FUN FACT: {random.choice(FUN_FACTS)}"
            
        return bot_reply
        
    except Exception as e:
        return "🌊 Woops! My ocean internet is wavy... Can you repeat that?"

def show_jellyfish_art():
    """Display ASCII art occasionally from the database"""
    if ASCII_ART_DATABASE and random.random() < 0.3:  # 30% chance and art is available
        art = random.choice(ASCII_ART_DATABASE)
        print(art)
    elif not ASCII_ART_DATABASE and random.random() < 0.3: # If list is empty but still trying to show
        print_slowly("🎨 (Psst! I'd love to show some art, but my art book is empty!)")

if __name__ == "__main__":
    # Intro
    print_slowly("🌊 Sandy the Jellyfish is ready to chat! 🌊")
    show_jellyfish_art()
    
    # Chat loop
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            print_slowly("Sandy: Bye-bye! Waves to you later! 🌊👋")
            speak("Bye bye! Come explore again soon!") 
            break
            
        # Get and display response
        print("Sandy: ", end='')
        response = chat_with_bot(user_input) # This call blocks while waiting for OpenAI
        
        # Speak the first line of the response asynchronously
        speak(response.split('\n')[0]) 
        # Then print the full response slowly; sound should play concurrently
        print_slowly(response)
        show_jellyfish_art()