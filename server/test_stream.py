import asyncio
import io
import edge_tts

async def synthesize_male_stream(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice="en-IN-PrabhatNeural")
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()

async def main():
    audio_bytes = await synthesize_male_stream("Hello! I am a male Indian voice.")
    print("Generated audio bytes:", len(audio_bytes))

asyncio.run(main())
