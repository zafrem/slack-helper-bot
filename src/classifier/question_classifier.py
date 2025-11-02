"""Question type classifier using LLM."""

import structlog
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from src.config.settings import Settings
from src.models.conversation import QuestionType

logger = structlog.get_logger(__name__)


class QuestionClassifier:
    """Classifier for determining question types."""

    CLASSIFICATION_PROMPT = """Analyze the following message and classify it into one of these categories:

1. **bug**: The user is reporting a bug, error, or something not working as expected
2. **how_to**: The user is asking how to do something or requesting guidance
3. **feature_request**: The user is requesting a new feature or enhancement
4. **ops_action**: The user is requesting an operational action (restart service, clear cache, etc.)
5. **other**: Anything else that doesn't fit the above categories

Message: {message}

Respond with ONLY the category name (bug, how_to, feature_request, ops_action, or other).
"""

    def __init__(self, settings: Settings) -> None:
        """Initialize the classifier.

        Args:
            settings: Application settings
        """
        self.settings = settings

        if settings.llm_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is required")
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key.get_secret_value()
            )
        else:
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key is required")
            self.client = AsyncAnthropic(
                api_key=settings.anthropic_api_key.get_secret_value()
            )

    async def classify(self, message: str) -> QuestionType:
        """Classify a message into a question type.

        Args:
            message: The message to classify

        Returns:
            Question type
        """
        logger.info("Classifying message", message_length=len(message))

        try:
            prompt = self.CLASSIFICATION_PROMPT.format(message=message)

            if self.settings.llm_provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.settings.llm_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful classification assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=10,
                )
                classification = response.choices[0].message.content.strip().lower()
            else:
                response = await self.client.messages.create(
                    model=self.settings.llm_model,
                    max_tokens=10,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                )
                classification = response.content[0].text.strip().lower()

            # Map to QuestionType enum
            type_map = {
                "bug": QuestionType.BUG,
                "how_to": QuestionType.HOW_TO,
                "feature_request": QuestionType.FEATURE_REQUEST,
                "ops_action": QuestionType.OPS_ACTION,
                "other": QuestionType.OTHER,
            }

            question_type = type_map.get(classification, QuestionType.OTHER)

            logger.info(
                "Message classified",
                classification=classification,
                question_type=question_type.value,
            )

            return question_type

        except Exception as e:
            logger.exception("Error classifying message", error=str(e))
            return QuestionType.OTHER
