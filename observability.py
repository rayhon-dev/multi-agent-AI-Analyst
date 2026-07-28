from config import LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY


def get_callbacks() -> list:
    if not (LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY):
        return []

    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler

    Langfuse(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_SECRET_KEY, host=LANGFUSE_HOST)
    return [CallbackHandler()]
