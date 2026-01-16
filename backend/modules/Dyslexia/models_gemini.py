from google import genai
import os

# Initialize the client with your API key
client = genai.Client(api_key="AIzaSyCpBHHTt8XGT6tRo80vZsvNGuDHvLeds6A")

# List all available models
for model in client.models.list():
    print(f"Name: {model.name}")
    print(f"Display Name: {model.display_name}")
    print("-" * 30)