import pytest
from pharia_skill.testing import StubCsi
from pharia_skill import ChatParams, Message, Role, ChatResponse, FinishReason

from quote import custom_quote, Input


class CustomStubCsi(StubCsi):
    def chat(
        self, model_name: str, messages: list[Message], params: ChatParams
    ) -> ChatResponse:
        return ChatResponse(
            message=Message(
                role=Role.Assistant,
                content="The shortest quote in the world",
            ),
            finish_reason=FinishReason.STOP,
        )


@pytest.fixture
def csi() -> CustomStubCsi:
    return CustomStubCsi()


def test_custom_quote(csi: CustomStubCsi):
    result = custom_quote(csi, Input())
    assert result.quote
    assert result.quote == "The shortest quote in the world"
