"""
Processore per il nodo Ollama nel core-llm-plugin
"""

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli Ollama self-hosted.
    
    Args:
        inputs: Dict con gli input del nodo
            - prompt: Testo da inviare al modello
            - system (opzionale): Messaggio di sistema
        config: Dict con la configurazione del nodo
            - model: Modello Ollama da utilizzare
            - endpoint: URL dell'endpoint Ollama
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
    model = config.get("model", "llama3")
    endpoint = config.get("endpoint", "http://localhost:11434")
    temperature = config.get("temperature", 0.7)
    
    # In un'implementazione reale, qui ci sarebbe la chiamata all'API Ollama
    # Esempio di codice (commentato):
    # import json
    # import aiohttp
    #
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(
    #         f"{endpoint}/api/chat",
    #         headers={"Content-Type": "application/json"},
    #         json={
    #             "model": model,
    #             "messages": [
    #                 {"role": "system", "content": system},
    #                 {"role": "user", "content": prompt}
    #             ],
    #             "options": {
    #                 "temperature": temperature
    #             }
    #         }
    #     ) as response:
    #         result_json = await response.json()
    #         result = result_json["message"]["content"]
    
    # Per ora, simuliamo una risposta
    result = f"Risposta Ollama simulata per: {prompt}"
    
    # Simuliamo anche una risposta completa dall'API
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
    
    return {
        "response": result,
        "full_response": full_response
    }
