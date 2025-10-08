from pharia_skill import ChatParams, Csi, Message, skill
from pydantic import BaseModel


class Input(BaseModel):
    pass


class Output(BaseModel):
    quote: str | None


@skill
def custom_quote(csi: Csi, input: Input) -> Output:
    content = "Create a short insightful quote"
    message = Message.user(content)
    params = ChatParams(max_tokens=512)
    response = csi.chat("llama-3.1-8b-instruct", [message], params)
    return Output(quote=response.message.content)
