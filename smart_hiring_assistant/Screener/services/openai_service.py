from openai import OpenAI
import os
from django.conf import settings

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
    def generate_chat_completion(self, messages):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            return response
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise