import os
import io
import asyncio
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv

load_dotenv()

# Using v1alpha for the March 2026 Live features
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={'api_version': 'v1alpha'}
)

async def voice_loop():
    print("--- Gemini Continuous Voice (March 2026) ---")
    print("Type 'exit' or 'quit' to stop the conversation.\n")
    
    model_id = "gemini-3.1-flash-live-preview"
    config = {"response_modalities": ["AUDIO"]}
    
    # Open a single persistent connection
    async with client.aio.live.connect(model=model_id, config=config) as session:
        while True:
            user_query = input("You: ")
            
            if user_query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            try:
                # Send the input to the existing session
                await session.send_realtime_input(text=user_query)
                print("Gemini is thinking...")
                
                audio_data = io.BytesIO()
                
                # Listen for the response stream
                async for message in session.receive():
                    if message.server_content and message.server_content.model_turn:
                        for part in message.server_content.model_turn.parts:
                            if part.inline_data:
                                audio_data.write(part.inline_data.data)
                    
                    # Exit the receive loop once the turn is finished
                    if message.server_content and message.server_content.turn_complete:
                        break

                # Play the response
                audio_data.seek(0)
                if audio_data.getbuffer().nbytes > 0:
                    audio_seg = AudioSegment.from_raw(
                        audio_data, 
                        sample_width=2, 
                        frame_rate=24000, 
                        channels=1
                    )
                    print("Gemini is speaking...")
                    play(audio_seg)
                else:
                    print("Gemini had no audio response.")

            except Exception as e:
                print(f"Loop Error: {e}")
                break

if __name__ == "__main__":
    try:
        asyncio.run(voice_loop())
    except KeyboardInterrupt:
        print("\nSession ended by user.")