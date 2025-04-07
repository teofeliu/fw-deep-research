from fireworks.client import AsyncFireworks
from openai import AsyncOpenAI

class ModelInterface:
    def __init__(self, model_id, config=None):
        self.model_id = model_id
        self.config = config or {}
        self.provider = self.config.get("provider", "fireworks")
        
        if self.provider == "openai":
            self.client = AsyncOpenAI(
                api_key=self.config.get("openai_api_key")
            )
        else:  # Default to fireworks
            self.client = AsyncFireworks(
                api_key=self.config.get("fireworks_api_key")
            )
    
    async def generate(self, prompt, temperature=None, max_tokens=None):
        """Generate a response using the LLM."""
        temp = temperature or self.config.get("temperature", 0.7)
        max_tok = max_tokens or self.config.get("max_tokens", 2048)
        
        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=max_tok
            )
        else:  # Fireworks
            response = await self.client.chat.completions.acreate(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_tok,
                stream=False
            )
        
        return response.choices[0].message.content