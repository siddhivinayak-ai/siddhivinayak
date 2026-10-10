import asyncio
import edge_tts

async def test_speak():
    communicate = edge_tts.Communicate("Namaste! I am Siddhivinayak, your assistant.", voice="en-IN-PrabhatNeural")
    await communicate.save("server/test_prabhat.mp3")
    print("Prabhat audio generated successfully!")

asyncio.run(test_speak())
