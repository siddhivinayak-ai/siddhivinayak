import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    indian = [v for v in voices if 'IN' in v['Locale']]
    for v in indian:
        print(v['ShortName'], '|', v['Gender'], '|', v['Locale'])

asyncio.run(main())
