import logging

from config.clients import openai_client as client

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating text using OpenAI client with Groq API."""

    def translate_to_polish(self, text: str, max_retries: int = 3) -> str | None:
        """
        Translate English text to Polish using Groq API.

        Args:
            text: English text to translate
            max_retries: Maximum number of retry attempts

        Returns:
            Polish translation or None if translation fails
        """
        if not text or not text.strip():
            return None

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a professional translator. Translate the given"
                                " English text to Polish. Keep the translation accurate"
                                " and natural-sounding. Only return the translated text"
                                " without any additional explanations."
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                )

                translation = response.choices[0].message.content
                if translation:
                    return translation.strip()

            except Exception as e:
                logger.warning(
                    "Translation attempt %d failed for text '%s...': %s",
                    attempt + 1,
                    text[:50],
                    e,
                )
                if attempt == max_retries - 1:
                    logger.error(
                        "Failed to translate text after %s attempts: %s", max_retries, e
                    )

        return None
