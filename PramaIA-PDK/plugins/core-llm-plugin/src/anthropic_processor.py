"""
Processore per il nodo Anthropic nel core-llm-plugin
"""

import logging

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli Anthropic Claude.
    """
    logger = logging.getLogger("anthropic_processor")
    entry_msg = f"[Anthropic] INGRESSO nodo: prompt={inputs.get('prompt', '')[:30]}..."
    logger.info(entry_msg)
    prompt = inputs.get("prompt", "")
    system = inputs.get("system", "Sei un assistente AI utile, preciso e conciso.")
    model = config.get("model", "claude-3-sonnet-20240229")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    # Simulazione risposta
    result = f"Risposta Claude simulata per: {prompt}"
    full_response = {
        "id": "msg_012345abcdef",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": result
            }
        ],
        "model": model,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(result) // 4
        }
    }
    exit_msg = f"[Anthropic] USCITA nodo (successo): model={model}"
    logger.info(exit_msg)
    return {
        "response": result,
        "full_response": full_response
    }
