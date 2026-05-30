"""Model context window size lookup and adjustment."""

from config.settings import get_settings
from loguru import logger


# Default context window sizes for known models/families.
# Keys are model family names or provider prefixes (lowercase).
DEFAULT_CONTEXT_WINDOWS: dict[str, int] = {
    # Specific model families (more specific first)
    "llama3.1": 131072,
    "llama-3.1": 131072,
    "llama3.2": 128000,
    "llama-3.2": 128000,
    "llama3": 8192,
    "llama-3": 8192,
    "llama2": 4096,
    "llama-2": 4096,
    "qwen2": 131072,
    "qwen": 32768,
    "gemma": 8192,
    "mistral": 32000,
    "mixtral": 32000,
    "step": 32000,
    "step2": 32000,
    "deepseek": 64000,
    "glm4": 128000,
    "glm5": 131072,
    "kimi": 200000,
    "claude": 200000,
    "gpt-4o": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4-32k": 32768,
    "gpt-4": 8192,
    "gemini": 128000,
    # Provider default (used if model family not recognized)
    "nvidia_nim": 131072,
}


def get_model_context_window(model_name: str) -> int:
    """Get the context window size for a given model name.

    The lookup order:
    1. User-configured MODEL_CONTEXT_WINDOW setting (exact or prefix match)
    2. Built-in DEFAULT_CONTEXT_WINDOWS (family name substring match)
    3. Provider prefix match (e.g., 'nvidia_nim')
    4. Fallback to 131072

    Args:
        model_name: The full model identifier, e.g., "nvidia_nim/meta/llama3-70b-instruct"

    Returns:
        The estimated context window size in tokens.
    """
    settings = get_settings()
    raw_config = settings.model_context_window.strip()

    # 1. Check user configuration
    if raw_config:
        # Single integer for all models
        if ":" not in raw_config:
            try:
                return int(raw_config)
            except ValueError:
                logger.warning(
                    f"Invalid MODEL_CONTEXT_WINDOW: '{raw_config}'. Expected integer or key:value pairs. Using defaults."
                )
        else:
            # Parse key:value pairs
            mapping: dict[str, int] = {}
            parts = [p.strip() for p in raw_config.split(",") if p.strip()]
            for part in parts:
                if ":" not in part:
                    continue
                key, val_str = part.split(":", 1)
                key = key.strip()
                try:
                    val = int(val_str.strip())
                    mapping[key] = val
                except ValueError:
                    logger.warning(
                        f"Invalid MODEL_CONTEXT_WINDOW entry: '{part}'. Skipping."
                    )
            if mapping:
                # Exact match
                if model_name in mapping:
                    return mapping[model_name]
                # Prefix match (longer prefixes first)
                sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
                for key in sorted_keys:
                    if model_name.startswith(key):
                        return mapping[key]

    # 2. Check built-in defaults by family substring (skip provider defaults for now)
    model_lower = model_name.lower()
    for key, window in DEFAULT_CONTEXT_WINDOWS.items():
        if key in ("nvidia_nim", "open_router", "lmstudio"):
            continue
        if key in model_lower:
            return window

    # 3. Provider prefix match
    if "/" in model_name:
        provider_prefix = model_name.split("/", 1)[0]
        if provider_prefix in DEFAULT_CONTEXT_WINDOWS:
            return DEFAULT_CONTEXT_WINDOWS[provider_prefix]

    # 4. Final fallback
    return 131072


def adjust_max_tokens_for_context_window(
    body: dict,
    input_tokens: int,
    model_name: str | None = None,
) -> None:
    """Adjust the max_tokens value in the request body to fit within the model's context window.

    This modification is done in-place on the body dictionary.

    Args:
        body: The OpenAI-format request body dictionary.
        input_tokens: The number of tokens in the input messages.
        model_name: Optional model identifier. If not provided, extracted from body['model'].
    """
    model = model_name or body.get("model")
    if not model:
        return

    max_tokens = body.get("max_tokens")
    if max_tokens is None:
        return

    settings = get_settings()
    margin = settings.context_window_safety_margin

    context_window = get_model_context_window(model)
    available_tokens = context_window - input_tokens - margin

    if available_tokens <= 0:
        # Input already exceeds the context window minus margin
        logger.warning(
            f"Input tokens ({input_tokens}) exceed model {model}'s context window "
            f"({context_window}) even with safety margin ({margin}). "
            "Request will likely fail. Setting max_tokens to 1."
        )
        body["max_tokens"] = 1
        return

    if max_tokens > available_tokens:
        old_max = max_tokens
        body["max_tokens"] = available_tokens
        logger.info(
            f"Adjusted max_tokens from {old_max} to {available_tokens} to fit model {model} "
            f"(context window: {context_window}, input tokens: {input_tokens}, margin: {margin})"
        )
