import sys
import asyncio
from loguru import logger
from app.services.llm import LLMService, LLMRequest

async def main():
    try:
        print("Testing LLM service...")
        service = LLMService()
        
        # Get configuration details
        print(f"Default model: {service.default_model}")
        print(f"Ollama base URL: {service.ollama_base_url}")
        print(f"Ollama model: {service.ollama_model}")
        
        # Try to generate some text
        print("\nTesting text generation...")
        response = await service.generate_text(
            LLMRequest(
                prompt="Write a short paragraph about artificial intelligence.",
                max_tokens=100
            )
        )
        
        print(f"Response model: {response.model}")
        print(f"Token usage: {response.token_usage}")
        print(f"Generated text: \n{response.text}")
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 