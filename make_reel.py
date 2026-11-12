import os
import json
import asyncio
import datetime
from PIL import Image, ImageDraw, ImageFont
from google import genai
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. Ask Gemini for a fascinating Psychology Fact Reel script
prompt = """
Create a 25-to-30 second educational Instagram Reel about a fascinating, lesser-known human psychology fact or cognitive bias.
Return ONLY valid JSON with this exact structure (no markdown backticks, no extra text):
{
  "topic": "Short Psychology Title (max 4 words)",
  "slides": [
    {"step": "HOOK", "headline": "Curiosity-sparking question (4-7 words)", "body": "1 short intriguing line.", "narration": "Spoken hook to stop the scroll."},
    {"step": "THE FACT", "headline": "Name of Phenomenon or Rule", "body": "Clear 10-14 word explanation of what happens.", "narration": "Spoken explanation of the psychology fact."},
    {"step": "WHY IT HAPPENS", "headline": "The Brain's Trigger", "body": "Clear 10-14 word explanation of why our brain does this.", "narration": "Spoken explanation of the brain mechanism."},
    {"step": "TAKEAWAY", "headline": "How To Use This", "body": "Actionable 8-12 word advice for daily life.", "narration": "Spoken practical takeaway."}
  ],
  "caption": "Engaging Instagram caption summarizing the psychology fact with a question for comments and 5 psychology hashtags."
}
"""

res = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt
)
raw_json = res.text.strip().removeprefix("```json").removesuffix("```").strip()
data = json.loads(raw_json)

os.makedirs("reels", exist_ok=True)
today = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

# Save caption file
with open(f"reels/psych_{today}_caption.txt", "w", encoding="utf-8") as f:
    f.write(data["caption"])

# Helper to generate natural human-sounding voiceover
async def make_voice(text, filename):
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    await communicate.save(filename)

# Helper to wrap text cleanly inside cards
def wrap_text(text, max_chars):
    words, lines, curr = text.split(), [], ""
    for w in words:
        if len(curr + w) <= max_chars:
            curr += w + " "
        else:
            lines.append(curr.strip())
            curr = w + " "
    lines.append(curr.strip())
    return "\n".join(lines)

# Helper to draw sleek psychology motion-graphic cards
def draw_slide(topic, step, headline, body, idx, total_slides):
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), color=(11, 15, 25)) # Deep Midnight Background
    draw = ImageDraw.Draw(img)

    font_pill = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    font_step = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)

    # Top Category Badge
    draw.rounded_rectangle([80, 170, 1000, 255], radius=25, fill=(24, 32, 50))
    draw.text((115, 193), f"PSYCHOLOGY  •  {topic.upper()}", font=font_pill, fill=(167, 139, 250))

    # Main Card Container
    draw.rounded_rectangle([80, 440, 1000, 1420], radius=45, fill=(20, 27, 45), outline=(139, 92, 246), width=4)

    # Step Tag Pill
    draw.rounded_rectangle([135, 510, 480, 575], radius=15, fill=(139, 92, 246))
    draw.text((160, 523), step.upper(), font=font_step, fill=(255, 255, 255))

    # Headline & Body Text
    draw.text((135, 640), wrap_text(headline, 19), font=font_title, fill=(255, 255, 255))
    draw.text((135, 980), wrap_text(body, 27), font=font_body, fill=(203, 213, 225))

    # Bottom Slide Progress Dots / Bar
    bar_width = 920
    progress = int(bar_width * ((idx + 1) / total_slides))
    draw.rounded_rectangle([80, 1520, 1000, 1540], radius=10, fill=(30, 41, 59))
    draw.rounded_rectangle([80, 1520, 80 + progress, 1540], radius=10, fill=(167, 139, 250))

    path = f"slide_{idx}.png"
    img.save(path)
    return path

# 2. Build each slide with smooth motion + voiceover sync
clips = []
total = len(data["slides"])

for i, s in enumerate(data["slides"]):
    audio_file = f"voice_{i}.mp3"
    asyncio.run(make_voice(s["narration"], audio_file))
    audio_clip = AudioFileClip(audio_file)
    dur = audio_clip.duration + 0.35

    img_file = draw_slide(data["topic"], s["step"], s["headline"], s["body"], i, total)

    # Smooth subtle zoom-in motion on every card
    img_clip = (
        ImageClip(img_file)
        .with_duration(dur)
        .resized(lambda t: 1.0 + 0.035 * (t / dur))
        .with_position("center")
        .with_audio(audio_clip)
    )
    clips.append(img_clip)

final_video = concatenate_videoclips(clips, method="compose")
final_video.write_videofile(f"reels/psych_{today}.mp4", fps=24, codec="libx264", audio_codec="aac")
