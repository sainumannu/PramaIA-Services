"""
Processore per il nodo Anthropic nel core-llm-plugin
"""

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli Anthropic Claude.
    
    Args:
        inputs: Dict con gli input del nodo
            - prompt: Testo da inviare al modello
            - system (opzionale): Messaggio di sistema
        config: Dict con la configurazione del nodo
            - model: Modello Anthropic da utilizzare
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
    model = config.get("model", "claude-3-sonnet-20240229")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    
    # In un'implementazione reale, qui ci sarebbe la chiamata all'API Anthropic
    # Esempio di codice (commentato):
    # from anthropic import Anthropic
    # client = Anthropic()
    # response = client.messages.create(
    #     model=model,
    #     system=system,
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=max_tokens,
    #     temperature=temperature
    # )
    # result = response.content[0].text
    
    # Per ora, simuliamo una risposta
    result = f"Risposta Claude simulata per: {prompt}"
    
    # Simuliamo anche una risposta completa dall'API
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
    
    return {
        "response": result,
        "full_response": full_response
    }
