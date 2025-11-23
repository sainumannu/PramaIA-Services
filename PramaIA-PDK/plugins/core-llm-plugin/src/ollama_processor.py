"""
Processore per il nodo Ollama nel core-llm-plugin
"""

import logging

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli Ollama self-hosted.
    """
    logger = logging.getLogger("ollama_processor")
    entry_msg = f"[Ollama] INGRESSO nodo: prompt={inputs.get('prompt', '')[:30]}..."
    logger.info(entry_msg)
    prompt = inputs.get("prompt", "")
    system = inputs.get("system", "Sei un assistente AI utile, preciso e conciso.")
    model = config.get("model", "llama3")
    endpoint = config.get("endpoint", "http://localhost:11434")
    temperature = config.get("temperature", 0.7)
    # Simulazione risposta
    result = f"Risposta Ollama simulata per: {prompt}"
    full_response = {
        "model": model,
        "message": {
            "role": "assistant",
            "content": result
        },
        "done": True,
        "total_duration": 1234567890,
        "load_duration": 123456789,
        "prompt_eval_count": len(prompt) // 4,
        "prompt_eval_duration": 123456789,
        "eval_count": len(result) // 4,
        "eval_duration": 123456789
    }
    exit_msg = f"[Ollama] USCITA nodo (successo): model={model}"
    logger.info(exit_msg)
    return {
        "response": result,
        "full_response": full_response
    }
