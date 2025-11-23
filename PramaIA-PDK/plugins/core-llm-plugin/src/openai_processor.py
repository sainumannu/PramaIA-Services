"""
Processore per il nodo OpenAI nel core-llm-plugin
"""

import logging

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli OpenAI.
    """
    logger = logging.getLogger("openai_processor")
    entry_msg = f"[OpenAI] INGRESSO nodo: prompt={inputs.get('prompt', '')[:30]}..."
    logger.info(entry_msg)
    prompt = inputs.get("prompt", "")
    system = inputs.get("system", "Sei un assistente AI utile, preciso e conciso.")
    model = config.get("model", "gpt-3.5-turbo")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    # Simulazione risposta
    result = f"Risposta simulata per: {prompt}"
    full_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": model,
        "usage": {
            "prompt_tokens": len(prompt) // 4,
            "completion_tokens": len(result) // 4,
            "total_tokens": (len(prompt) + len(result)) // 4
        },
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": result
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }
    exit_msg = f"[OpenAI] USCITA nodo (successo): model={model}"
    logger.info(exit_msg)
    return {
        "response": result,
        "full_response": full_response
    }
