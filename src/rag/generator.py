"""LLM generation module using Ollama."""

import json
from typing import Dict, Any, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config import Settings


class Generator:
    """LLM-based text generation using Ollama."""

    def __init__(self, settings: Settings):
        """
        Initialize generator with Ollama.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.top_p = settings.llm_top_p
        self.timeout = settings.llm_timeout

        logger.info(f"Initialized Generator with model: {self.model} at {self.base_url}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API with retry logic.

        Args:
            prompt: Prompt text

        Returns:
            Generated text response
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_p": self.top_p,
            },
        }

        logger.debug(f"Calling Ollama API: {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        try:
            # Combine system prompt and user prompt if system prompt provided
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            logger.info(f"Generating response (prompt length: {len(full_prompt)} chars)")

            response = await self._call_ollama(full_prompt)

            logger.info(f"Generated response (length: {len(response)} chars)")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def generate_incident_summary(
        self,
        email_content: str,
        context: str,
        has_kb_match: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate incident summary based on email and knowledge base context.

        Args:
            email_content: Original email content
            context: Retrieved knowledge base context
            has_kb_match: Whether knowledge base match was found

        Returns:
            Dictionary with summary, description, and metadata
        """
        logger.info("Generating incident summary from email and context")

        # Build system prompt
        system_prompt = """You are an expert IT incident analyst. Your task is to analyze
the incident report from an email and create a structured incident summary for ServiceNow.

You should:
1. Extract the main problem/issue from the email
2. If knowledge base articles are provided, reference relevant solutions
3. Categorize the incident appropriately
4. Suggest urgency and impact levels
5. Provide a clear, concise summary

Format your response as JSON with the following structure:
{
    "short_description": "Brief one-line description",
    "description": "Detailed description with context",
    "category": "Incident category",
    "urgency": 1-5,
    "impact": 1-5,
    "recommended_actions": ["action1", "action2"],
    "kb_references": ["KB article title 1", "KB article title 2"]
}"""

        # Build user prompt
        if has_kb_match and context:
            user_prompt = f"""Analyze this incident email and create a ServiceNow incident summary.

EMAIL CONTENT:
{email_content}

RELEVANT KNOWLEDGE BASE ARTICLES:
{context}

Based on the email and knowledge base articles, provide a structured incident summary."""
        else:
            user_prompt = f"""Analyze this incident email and create a ServiceNow incident summary.
No matching knowledge base articles were found, so base your analysis solely on the email content.

EMAIL CONTENT:
{email_content}

Provide a structured incident summary with your best assessment."""

        try:
            # Generate response
            response = await self.generate(user_prompt, system_prompt)

            # Try to parse JSON response
            try:
                # Extract JSON from response (in case LLM adds extra text)
                json_start = response.find("{")
                json_end = response.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    incident_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON from LLM response: {e}")
                # Fallback: create structured data from raw text
                incident_data = self._extract_incident_from_text(response, email_content)

            # Add metadata
            incident_data["has_kb_match"] = has_kb_match
            incident_data["raw_llm_response"] = response

            logger.info("Successfully generated incident summary")
            return incident_data

        except Exception as e:
            logger.error(f"Error generating incident summary: {e}")
            # Return minimal fallback data
            return {
                "short_description": "Incident from email",
                "description": email_content[:500],
                "category": "Incident",
                "urgency": 3,
                "impact": 3,
                "recommended_actions": [],
                "kb_references": [],
                "has_kb_match": False,
                "error": str(e),
            }

    def _extract_incident_from_text(
        self, text: str, email_content: str
    ) -> Dict[str, Any]:
        """
        Extract incident data from unstructured text response.

        Args:
            text: LLM response text
            email_content: Original email content

        Returns:
            Structured incident data
        """
        logger.warning("Using fallback text extraction for incident data")

        # Simple extraction logic
        lines = text.split("\n")

        short_desc = lines[0][:200] if lines else "Incident from email"
        description = text[:1000] if len(text) > 200 else email_content[:500]

        return {
            "short_description": short_desc,
            "description": description,
            "category": "Incident",
            "urgency": 3,
            "impact": 3,
            "recommended_actions": [],
            "kb_references": [],
        }

    async def check_health(self) -> bool:
        """
        Check if Ollama service is healthy and model is available.

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Check if our model is available
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name") for m in models]

                if self.model in model_names:
                    logger.info(f"Ollama is healthy, model {self.model} is available")
                    return True
                else:
                    logger.warning(
                        f"Ollama is running but model {self.model} not found. "
                        f"Available models: {model_names}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
