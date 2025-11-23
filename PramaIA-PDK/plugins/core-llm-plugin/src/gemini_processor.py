"""
Processore per il nodo Gemini nel core-llm-plugin
"""

import logging

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli Google Gemini.
    """
    logger = logging.getLogger("gemini_processor")
    entry_msg = f"[Gemini] INGRESSO nodo: prompt={inputs.get('prompt', '')[:30]}..."
    logger.info(entry_msg)
    prompt = inputs.get("prompt", "")
    system = inputs.get("system", "Sei un assistente AI utile, preciso e conciso.")
    model = config.get("model", "gemini-1.5-pro")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    # Simulazione risposta
    result = f"Risposta Gemini simulata per: {prompt}"
    full_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": result
                        }
                    ],
                    "role": "model"
                },
                "finishReason": "STOP",
                "index": 0,
                "safetyRatings": []
            }
        ],
        "promptFeedback": {
            "safetyRatings": []
        }
    }
    exit_msg = f"[Gemini] USCITA nodo (successo): model={model}"
    logger.info(exit_msg)
    return {
        "response": result,
        "full_response": full_response
    }
