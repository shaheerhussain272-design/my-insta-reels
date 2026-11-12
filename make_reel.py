import os
import datetime
from google import genai
from gtts import gTTS
from moviepy import ColorClip, TextClip, CompositeVideoClip, AudioFileClip

# 1. Ask Gemini for a short Reel script & caption
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """
Write a punchy, 10-second motivational quote for an Instagram Reel.
Format your response in two exact parts separated by '|||':
Part 1: The quote itself (maximum 15 words, easy to read on screen).
Part 2: An engaging Instagram caption with 5 hashtags.
Do not include any labels like 'Part 1' or 'Quote:'.
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

parts = response.text.strip().split("|||")
quote_text = parts[0].strip()
caption_text = parts[1].strip() if len(parts) > 1 else quote_text

# Create output folder
os.makedirs("reels", exist_ok=True)
today = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

# 2. Save the caption file
caption_path = f"reels/reel_{today}_caption.txt"
with open(caption_path, "w", encoding="utf-8") as f:
    f.write(caption_text)

# 3. Generate Voiceover Audio
audio_path = "voiceover.mp3"
tts = gTTS(text=quote_text, lang="en", slow=False)
tts.save(audio_path)
audio = AudioFileClip(audio_path)
duration = max(audio.duration + 1.0, 5.0)

# 4. Build Vertical 9:16 Video (1080x1920)
background = ColorClip(size=(1080, 1920), color=(18, 18, 24), duration=duration)

txt_clip = TextClip(
    text=quote_text,
    font_size=65,
    color="white",
    size=(900, None),
    method="caption",
    text_align="center"
).with_position("center").with_duration(duration)

video = CompositeVideoClip([background, txt_clip]).with_audio(audio)
video_path = f"reels/reel_{today}.mp4"
video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")
