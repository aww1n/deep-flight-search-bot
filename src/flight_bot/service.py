from openai import AsyncOpenAI


class FlightSearchService:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        reasoning_effort: str,
        instructions: str,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.instructions = instructions

    async def respond(self, message: str, previous_response_id: str | None) -> tuple[str, str]:
        request: dict = {
            "model": self.model,
            "instructions": self.instructions,
            "input": message,
            "tools": [
                {
                    "type": "web_search",
                    "search_context_size": "high",
                    "external_web_access": True,
                }
            ],
            "tool_choice": "auto",
            "reasoning": {"effort": self.reasoning_effort},
            "store": True,
        }
        if previous_response_id:
            request["previous_response_id"] = previous_response_id

        response = await self.client.responses.create(**request)
        answer = response.output_text.strip()
        if not answer:
            answer = "Не удалось сформировать ответ. Попробуйте повторить запрос."
        return answer, response.id
