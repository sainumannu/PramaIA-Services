"""
Processore per il nodo Gemini nel core-llm-plugin
"""

async def process(inputs, config):
    """
    Questo processore gestisce le richieste ai modelli Google Gemini.
    
    Args:
        inputs: Dict con gli input del nodo
            - prompt: Testo da inviare al modello
            - system (opzionale): Messaggio di sistema
        config: Dict con la configurazione del nodo
            - model: Modello Gemini da utilizzare
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
    model = config.get("model", "gemini-1.5-pro")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    
    # In un'implementazione reale, qui ci sarebbe la chiamata all'API Gemini
    # Esempio di codice (commentato):
    # import google.generativeai as genai
    # genai.configure(api_key="API_KEY")
    # model_instance = genai.GenerativeModel(model)
    # response = model_instance.generate_content(
    #     [system, prompt],
    #     generation_config={
    #         "max_output_tokens": max_tokens,
    #         "temperature": temperature
    #     }
    # )
    # result = response.text
    
    # Per ora, simuliamo una risposta
    result = f"Risposta Gemini simulata per: {prompt}"
    
    # Simuliamo anche una risposta completa dall'API
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
    
    return {
        "response": result,
        "full_response": full_response
    }
