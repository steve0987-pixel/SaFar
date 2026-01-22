"""
LLM utilities for Smart Trip Copilot.
Supports OpenAI API and local LLM via Ollama.
"""

import os
import json
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

T = TypeVar('T', bound=BaseModel)


class OllamaClient:
    """Local LLM client using Ollama."""
    
    def __init__(self, model: str = "phi3:mini", base_url: str = None):
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        print(f"🦙 Ollama client: {self.base_url} | model: {self.model} (CPU optimized)")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Get text completion from Ollama."""
        import requests
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise Exception(f"Ollama error: {response.status_code} - {response.text}")
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> dict:
        """Get JSON completion from Ollama."""
        
        json_prompt = f"""
{prompt}

ВАЖНО: Ответь ТОЛЬКО валидным JSON без markdown, без ```json, без пояснений.
"""
        
        response = self.complete(json_prompt, system_prompt, temperature)
        
        # Clean response
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        # Find JSON in response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            response = response[start:end]
        
        return json.loads(response)
    
    def complete_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> T:
        """Get structured output matching Pydantic schema."""
        
        schema_json = output_schema.model_json_schema()
        
        full_prompt = f"""
{prompt}

Ответь JSON объектом по этой схеме:
{json.dumps(schema_json, indent=2, ensure_ascii=False)}

Только JSON, без markdown и пояснений.
"""
        
        result = self.complete_json(full_prompt, system_prompt, temperature)
        return output_schema.model_validate(result)


class GroqClient:
    """Groq API client - OpenAI compatible, super fast cloud inference."""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")
        
        print(f"⚡ Groq client: {self.model} (cloud, ultra-fast)")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Get text completion from Groq."""
        import requests
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Groq error: {response.status_code} - {response.text}")
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> dict:
        """Get JSON completion from Groq."""
        
        json_prompt = f"""
{prompt}

IMPORTANT: Respond with ONLY valid JSON. No markdown, no ```json, no explanations.
"""
        
        response = self.complete(json_prompt, system_prompt, temperature)
        
        # Clean response
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        # Find JSON in response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            response = response[start:end]
        
        return json.loads(response)
    
    def complete_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> T:
        """Get structured output matching Pydantic schema."""
        
        schema_json = output_schema.model_json_schema()
        
        full_prompt = f"""
{prompt}

Respond with a JSON object matching this schema:
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON, no markdown or explanation.
"""
        
        result = self.complete_json(full_prompt, system_prompt, temperature)
        return output_schema.model_validate(result)


class OpenAIClient:
    """OpenAI API client with structured output support."""
    
    def __init__(self, model: str = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.2")  # Bleeding edge model!
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in .env file")
        
        if self.api_key in ["sk-your-key-here", "sk-ваш-ключ-здесь"]:
            raise ValueError("Please replace the placeholder OpenAI API key in .env with your actual key")
        
        self._client = None
        print(f"🤖 OpenAI client ready: {self.model}")
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def get_embeddings(self, texts: list, model: str = "text-embedding-3-small") -> list:
        """Get embeddings for a list of texts using OpenAI."""
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"⚠️  OpenAI embeddings error: {e}")
            raise
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Get text completion from OpenAI."""
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️  OpenAI completion error: {e}")
            raise
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> dict:
        """Get JSON completion from OpenAI."""
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"⚠️  OpenAI JSON completion error: {e}")
            raise
    
    def complete_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> T:
        """Get structured output matching Pydantic schema."""
        
        schema_json = output_schema.model_json_schema()
        
        full_prompt = f"""
{prompt}

Respond with a JSON object matching this schema:
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON, no markdown or explanation.
"""
        
        result = self.complete_json(full_prompt, system_prompt, temperature)
        return output_schema.model_validate(result)


class MockLLMClient:
    """Mock LLM client for testing without API access."""
    
    def __init__(self, model: str = "mock"):
        self.model = model
        print("🔧 MockLLMClient - демо режим без LLM")
    
    def complete(self, prompt: str, **kwargs) -> str:
        return "Mock response. Подключите Ollama или OpenAI для реальных ответов."
    
    def complete_json(self, prompt: str, **kwargs) -> dict:
        """Return mock JSON response based on prompt content."""
        
        # Mock TripRequest parsing
        if "TripRequest" in prompt or "trip" in prompt.lower() or "запрос" in prompt.lower():
            return {
                "city": "Samarkand",
                "duration_days": 2,
                "budget_usd": 100,
                "interests": ["history", "nature"],
                "constraints": ["mountains on day 2"],
                "pace": "moderate"
            }
        
        return {"result": "mock response"}
    
    def complete_structured(self, prompt: str, output_schema: Type[T], **kwargs) -> T:
        result = self.complete_json(prompt, **kwargs)
        return output_schema.model_validate(result)


def get_llm_client(use_mock: bool = False, prefer_local: bool = None):
    """
    Get LLM client with priority:
    1. OpenAI if API key set (best quality)
    2. Groq (cloud, ultra-fast) as alternative
    3. Ollama (local) if prefer_local=True
    4. Mock fallback
    """
    
    if use_mock:
        return MockLLMClient()
    
    # Check env for preference
    if prefer_local is None:
        prefer_local = os.getenv("PREFER_LOCAL_LLM", "false").lower() == "true"
    
    # Try OpenAI first (best quality)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key not in ["sk-your-key-here", "sk-ваш-ключ-здесь"]:
        try:
            # Avoid UnicodeEncodeError on Windows consoles with legacy encodings (cp1251, etc.)
            print("Using OpenAI API")
            return OpenAIClient()
        except Exception as e:
            print(f"OpenAI not available: {e}")
    
    # Try Groq as alternative (ultra-fast)
    if not prefer_local:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                return GroqClient(model=model)
            except Exception as e:
                print(f"Groq not available: {e}")
    
    # Try Ollama if preferred or as fallback
    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                model_name = os.getenv("OLLAMA_MODEL", "phi3:mini")
                available_models = [m["name"].split(":")[0] for m in models]
                if model_name not in available_models and available_models:
                    model_name = available_models[0]
                print(f"Using Ollama with model: {model_name}")
                return OllamaClient(model=model_name, base_url=ollama_url)
    except Exception as e:
        print(f"Ollama not available: {e}")
    
    # Fallback to mock
    print("No LLM available. Using MockLLMClient.")
    return MockLLMClient()


# Quick test
if __name__ == "__main__":
    client = get_llm_client()
    
    test_prompt = "Извлеки город и бюджет из: '2 дня Самарканд, $100'"
    
    try:
        result = client.complete_json(test_prompt)
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
