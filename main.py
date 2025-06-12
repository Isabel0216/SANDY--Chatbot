import time
import random
import os
from openai import OpenAI
import io 
import uuid
import string # For punctuation check in Animalese
import threading # for asynchronous sound playback
from typing import TYPE_CHECKING, Optional, Tuple, List 
import traceback

# Initialize OpenAI client with default settings
try:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url="https://api.openai.com/v1"
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    traceback.print_exc()
    raise

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
        self.digraphs = digraphs # This line was missing
        self.punctuation_sound = punctuation_sound
        self.speed_range = speed_range

        self.AudioSegment: Optional[type] = None
        self.pydub_play: Optional[callable] = None
        self.CouldntEncodeError: Optional[type] = None
        self.CouldntDecodeError: Optional[type] = None
        self.is_ready = False
        self.winsound_module: Optional[object] = None # For Windows-specific playback

        try:
            from pydub import AudioSegment as PydubAudioSegmentImport
            self.AudioSegment = PydubAudioSegmentImport
            from pydub.exceptions import CouldntEncodeError as PydubCouldntEncodeErrorImport, \
                                         CouldntDecodeError as PydubCouldntDecodeErrorImport
            self.CouldntEncodeError = PydubCouldntEncodeErrorImport
            self.CouldntDecodeError = PydubCouldntDecodeErrorImport
            self.is_ready = True
        except ImportError:
            print_slowly("💬 To use my Animalese voice, I need the 'pydub' library.")
            print_slowly("   You can install it with: pip install pydub")
            print_slowly("   You'll also likely need FFmpeg installed and in your system's PATH.")
            print_slowly("   (Search 'install ffmpeg <your_os>' for instructions).")
        
        # Attempt to import winsound for fallback playback on Windows
        try:
            import winsound
            self.winsound_module = winsound
        except ImportError:
            self.winsound_module = None # Not on Windows or winsound not available

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
        swear_words = ["fuck", "shit", "piss", "crap", "bugger"] 
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
        """Generates Animalese speech from text, saves it temporarily, and plays it."""
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

        # Sound will be played from memory, no temporary file needed for winsound playback itself.
        final_sound: Optional["PydubAudioSegmentType"] = None

        try:
            # --- Sound Generation ---
            raw_sound = self._build_audio_segment(text_for_speech)
            if not raw_sound or len(raw_sound) == 0:
                print_slowly("💬 (Animalese: Couldn't build any sound for that text.)")
                return

            speed_factor = random.uniform(self.speed_range[0], self.speed_range[1])
            final_sound = self._change_playback_speed(raw_sound, speed_factor)
            # At this point, final_sound is an in-memory AudioSegment

            # --- Playback Attempts ---
            played_successfully = False

            # Attempt winsound playback 
            if self.winsound_module and final_sound:
                try:
                    # print_slowly("💬 (Preparing sound for in-memory winsound playback...)") # Suppressed for cleaner output
                    sound_bytes_io = io.BytesIO()
                    final_sound.export(sound_bytes_io, format="wav")
                    sound_bytes = sound_bytes_io.getvalue()
                    sound_bytes_io.close()

                    if sound_bytes:
                        # print_slowly("💬 (Starting threaded in-memory winsound playback...)") # Suppressed for cleaner output
                        # Play in a separate thread to not block the main flow
                        playback_thread = threading.Thread(target=self._play_sound_in_thread, args=(sound_bytes,))
                        playback_thread.daemon = True # Allows main program to exit even if thread is running
                        playback_thread.start()
                        played_successfully = True # Assume it started successfully
                    else:
                        print_slowly(f"🌊 Oh dear! Failed to get sound bytes for winsound playback.")

                except (self.CouldntEncodeError, self.CouldntDecodeError) as e_export: # type: ignore
                    print_slowly(f"🌊 Drats! A little hiccup exporting my Animalese voice to memory (pydub/ffmpeg issue): {e_export}")
                except Exception as e_winsound_prep:
                    print_slowly(f"🌊 Whoops! Something went wrong preparing for/during in-memory winsound playback: {e_winsound_prep}")
            
            elif not self.winsound_module and final_sound:
                print_slowly("🌊 I generated my voice, but 'winsound' is not available on this system for playback.")
                print_slowly("   (Winsound is typically available on Windows systems.)")

            if not played_successfully:
                print_slowly("🌊 I generated my voice, but couldn't play it using winsound.")

        except (self.CouldntEncodeError, self.CouldntDecodeError) as e: # type: ignore
            print_slowly(f"🌊 Drats! A little hiccup processing my Animalese voice (pydub/ffmpeg issue): {e}")
            print_slowly("   This usually means FFmpeg is missing or not set up right.")
            return
        except PermissionError:
            print_slowly(f"🌊 Oh no! A permission issue occurred while preparing the voice. 📁")
            return
        except Exception as e: # Catch any other error during generation, export, or loading
            print_slowly(f"🌊 Yikes! Something unexpected happened with my Animalese voice: {e} 🎤")
            return
        # No temporary file cleanup needed here as playback is from memory

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
    try:
        # Remove emojis for speech
        processed_text = _remove_emojis_for_speech(text)
        
        # Initialize synthesizer if not done
        if not hasattr(speak, 'synthesizer'):
            speak.synthesizer = _initialize_animalese_synthesizer()
        
        if not speak.synthesizer or not speak.synthesizer.is_ready:
            raise Exception("Animalese synthesizer not initialized properly")
            
        if return_bytes:
            return speak.synthesizer.generate_audio_bytes(processed_text)
        else:
            speak.synthesizer.generate_and_play(processed_text)
            
    except Exception as e:
        print(f"Error in speak function: {str(e)}")
        traceback.print_exc()
        if return_bytes:
            return None
        raise Exception(f"Failed to generate speech: {str(e)}")

def chat_with_bot(user_input):
    try:
        # Add user's message to conversation history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150
        )
        
        # Extract the bot's response
        bot_response = response.choices[0].message.content
        
        # Add bot's response to conversation history
        conversation_history.append({"role": "assistant", "content": bot_response})
        
        return bot_response
    except Exception as e:
        print(f"Error in chat_with_bot: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Failed to get response from OpenAI: {str(e)}")

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
        # Then print the full response slowly
        print_slowly(response)
        show_jellyfish_art()