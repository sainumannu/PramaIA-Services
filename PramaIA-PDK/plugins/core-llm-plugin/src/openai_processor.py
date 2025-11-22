"""
Processore per il nodo OpenAI nel core-llm-plugin
"""

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli OpenAI.
    
    Args:
        inputs: Dict con gli input del nodo
            - prompt: Testo da inviare al modello
            - system (opzionale): Messaggio di sistema
        config: Dict con la configurazione del nodo
            - model: Modello OpenAI da utilizzare
            - max_tokens: Numero massimo di token nella risposta
            - temperature: Controllo della creatività
    
    Returns:
        Dict con l'output del nodo
            - response: Testo della risposta
            - full_response: Risposta completa con metadati
    """
    # Estrai i valori di input
    prompt = inputs.get("prompt", "")
    system = inputs.get("system", "Sei un assistente AI utile, preciso e conciso.")
    
    # Estrai la configurazione
    model = config.get("model", "gpt-3.5-turbo")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    
    # In un'implementazione reale, qui ci sarebbe la chiamata all'API OpenAI
    # Esempio di codice (commentato):
    # from openai import OpenAI
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": system},
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=max_tokens,
    #     temperature=temperature
    # )
    # result = response.choices[0].message.content
    
    # Per ora, simuliamo una risposta
    result = f"Risposta simulata per: {prompt}"
    
    # Simuliamo anche una risposta completa dall'API
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
    
    return {
        "response": result,
        "full_response": full_response
    }
