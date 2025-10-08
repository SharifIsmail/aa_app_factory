import litellm
from litellm import Cache
from litellm.types.caching import LiteLLMCacheType

from service.agent_core.constants import LITELLM_CACHE_DIR, LITELLM_CACHE_TTL
from service.agent_core.llm.aleph_alpha_llm_provider import AALLMProvider


def configure_litellm() -> None:
    aa_llm_provider = AALLMProvider()
    litellm.cache = Cache(
        type=LiteLLMCacheType.DISK,
        disk_cache_dir=LITELLM_CACHE_DIR,
        ttl=LITELLM_CACHE_TTL,
    )
    litellm.enable_cache()
    litellm.suppress_debug_info = True
    litellm.custom_provider_map = [
        {"provider": "aleph-alpha", "custom_handler": aa_llm_provider}
    ]
