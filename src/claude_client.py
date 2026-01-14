"""Claude API client for tutorial assistance."""

import os
from collections.abc import Generator

from anthropic import Anthropic

from .models import TutorialSession


class ClaudeClient:
    """Client for interacting with Claude API for tutorial assistance."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Claude client.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        self.conversation_history: list[dict] = []

    def _build_system_prompt(self, session: TutorialSession) -> str:
        """Build the system prompt with tutorial context."""
        return f"""You are a helpful coding tutorial assistant. You're helping a developer follow along with a YouTube coding tutorial.

## Tutorial Information
- **Video URL**: {session.video_url}
- **Title**: {session.title}
- **Total Duration**: {session.format_duration()}
- **Number of Segments**: {len(session.segments)}

## Full Transcript
The complete tutorial transcript is provided below. Use this to answer questions about any part of the tutorial.

<transcript>
{session.full_transcript}
</transcript>

## Your Role
1. Answer questions about the tutorial content clearly and concisely
2. Help explain code concepts mentioned in the tutorial
3. If asked about a specific timestamp, refer to the relevant part of the transcript
4. Provide code examples when helpful
5. If the user seems stuck, offer to break down the current step

## Guidelines
- Be concise but thorough
- Use code blocks with proper syntax highlighting
- Reference specific timestamps when relevant (e.g., "At 5:30, the instructor mentions...")
- If something isn't covered in the transcript, say so honestly
- Focus on being practical and helping the user make progress"""

    def ask(
        self,
        question: str,
        session: TutorialSession,
    ) -> Generator[str, None, None]:
        """
        Ask a question about the tutorial with streaming response.

        Args:
            question: The user's question
            session: The current tutorial session

        Yields:
            Chunks of the response text as they stream in
        """
        system_prompt = self._build_system_prompt(session)

        # Add the new user message to history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        # Stream the response
        full_response = ""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=self.conversation_history,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield text

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

    def ask_sync(self, question: str, session: TutorialSession) -> str:
        """
        Ask a question and get the complete response (non-streaming).

        Args:
            question: The user's question
            session: The current tutorial session

        Returns:
            The complete response text
        """
        chunks = list(self.ask(question, session))
        return "".join(chunks)
