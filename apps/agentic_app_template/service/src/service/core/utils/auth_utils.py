from fastapi import Request


def extract_bearer_token_from_request(request: Request) -> str | None:
    return extract_bearer_token(request.headers.get("Authorization"))


def extract_bearer_token(header: str | None) -> str | None:
    auth_scheme = "Bearer "
    return (
        header[len(auth_scheme) :]
        if header is not None and header.startswith(auth_scheme)
        else None
    )
