from typing import List
from typing import Dict
from typing import Tuple
from random_emoji import random_emoji
from openai import OpenAI
from dotenv import load_dotenv 
import playsound

class ChatGeneration(): 
    def __init__(self, key): 
        # load_dotenv() 
        self.model = "gpt-3.5-turbo"
        self.client = OpenAI(api_key=key)

    def generate_response(self, messages: List[Dict[str, str]]) -> None:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=messages
        )
        
        return response.choices[0].message.content

    def speak(self, message: str, voice: str) -> None: 
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice, 
            input=message
        )

        response.stream_to_file("output.mp3")
        playsound.playsound("output.mp3")

    def generate_random_bot(self) -> Tuple[str, Tuple[str, str]]: 
        rand_emoji = random_emoji()
        rand_name = self.generate_response(messages=[
                                               {"role": "system", "content": "You are a creative bot tasked with finding a unique name for the emoji given."}, 
                                               {"role": "user", "content": f"Come up with a creative, concise, and reasonable name for the given emoji: {rand_emoji}.\nOnly output the name."}
                                            ])   
        rand_description = self.generate_response(messages=[
                                                      {"role": "system", "content": "You are creative and are tasked with finding an interesting personality for the given character. Think out of the box."}, 
                                                      {"role": "user", "content": f"Given this name: {rand_name}, and this avatar: {rand_emoji}, come up with a creative and interesting personality for this character.\nKeep it relatively concise and only one paragraph."}
                                                  ])

        return (rand_emoji, rand_name, rand_description)