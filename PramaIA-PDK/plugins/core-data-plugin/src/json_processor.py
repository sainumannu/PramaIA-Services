import json
import re
import logging
from typing import Dict, Any, Optional, List, Union
import logging
# Logger adapter: prefer local .logger, fallback to PramaIA LogService client, else stdlib
try:
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
    from .logger import flush as log_flush, close as log_close
except Exception:
    try:
        from PramaIA_LogService.clients.pramaialog import PramaIALogger

        _pl = PramaIALogger()

        def log_debug(*a, **k):
            try:
                _pl.debug(*a, **k)
            except Exception:
                pass

        def log_info(*a, **k):
            try:
                _pl.info(*a, **k)
            except Exception:
                pass

        def log_warning(*a, **k):
            try:
                _pl.warning(*a, **k)
            except Exception:
                pass

        def log_error(*a, **k):
            try:
                _pl.error(*a, **k)
            except Exception:
                pass
    except Exception:
        import logging as _std_logging

        _logger = _std_logging.getLogger(__name__)

        def log_debug(*a, **k):
            _logger.debug(*a, **k)

        def log_info(*a, **k):
            _logger.info(*a, **k)

        def log_warning(*a, **k):
            _logger.warning(*a, **k)

        def log_error(*a, **k):
            _logger.error(*a, **k)
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.exceptions import JsonPathParserError

class JsonProcessor:
    """
    Processore per elaborare e manipolare dati JSON.
    Supporta estrazione, trasformazione, filtro e unione.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        self.operation = config.get("operation", "extract")
        self.extraction_path = config.get("extraction_path", "")
        self.filter_condition = config.get("filter_condition", "")
        self.transform_template = config.get("transform_template", "")
        self.default_value = config.get("default_value", "")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora i dati JSON in base all'operazione configurata.
        
        Args:
            inputs: Dizionario con i dati JSON e opzionalmente un percorso di estrazione
            
        Returns:
            Dizionario con il risultato dell'elaborazione
        """
        if "data" not in inputs:
            raise ValueError("Input 'data' richiesto ma non fornito")
        
        data = inputs["data"]
        
        # Converte la stringa JSON in oggetto Python se necessario
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                self._log_warning("L'input non è un JSON valido, verrà trattato come testo")
        
        # Determina il percorso di estrazione dall'input o dalla configurazione
        path = inputs.get("path", self.extraction_path)
        
        # Esegue l'operazione selezionata
        if self.operation == "extract":
            result = self._extract_data(data, path)
        elif self.operation == "transform":
            result = self._transform_data(data, self.transform_template)
        elif self.operation == "filter":
            result = self._filter_data(data, self.filter_condition)
        elif self.operation == "merge":
            # Per l'operazione merge, si aspetta che i dati siano già una lista di oggetti
            if not isinstance(data, list):
                data = [data]
            result = self._merge_objects(data)
        else:
            raise ValueError(f"Operazione non supportata: {self.operation}")
        
        return {"result": result}
    
    def _extract_data(self, data: Any, path: str) -> Any:
        """
        Estrae dati da un oggetto JSON usando JSONPath.
        
        Args:
            data: Dati JSON da cui estrarre
            path: Percorso JSONPath
            
        Returns:
            Dati estratti o valore di default se l'estrazione fallisce
        """
        if not path:
            return data
        
        try:
            # Utilizza jsonpath-ng per l'estrazione
            jsonpath_expr = jsonpath_parse(path)
            matches = [match.value for match in jsonpath_expr.find(data)]
            
            if not matches:
                self._log_warning(f"Nessun dato trovato al percorso: {path}")
                return self._get_default_value()
            
            # Se c'è solo una corrispondenza, restituisci solo quella
            if len(matches) == 1:
                return matches[0]
            
            return matches
            
        except (JsonPathParserError, Exception) as e:
            self._log_error(f"Errore nell'estrazione con JSONPath '{path}': {str(e)}")
            return self._get_default_value()
    
    def _transform_data(self, data: Any, template: str) -> Any:
        """
        Trasforma i dati usando un template.
        
        Args:
            data: Dati da trasformare
            template: Template di trasformazione
            
        Returns:
            Dati trasformati
        """
        if not template:
            return data
        
        try:
            # Gestisce diversi tipi di dati
            if isinstance(data, dict):
                # Per oggetti, sostituisce i segnaposto con i valori delle proprietà
                result = template
                for key, value in data.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in result:
                        result = result.replace(placeholder, str(value))
                
                # Cerca di convertire in JSON se possibile
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return result
                    
            elif isinstance(data, list):
                # Per array, applica la trasformazione a ogni elemento
                return [self._transform_data(item, template) for item in data]
            else:
                # Per valori semplici, restituisce il template con il valore sostituito
                return template.replace("{{value}}", str(data))
                
        except Exception as e:
            self._log_error(f"Errore nella trasformazione dei dati: {str(e)}")
            return data
    
    def _filter_data(self, data: Any, condition: str) -> Any:
        """
        Filtra i dati in base a una condizione.
        
        Args:
            data: Dati da filtrare
            condition: Condizione di filtro
            
        Returns:
            Dati filtrati
        """
        if not condition:
            return data
        
        try:
            if isinstance(data, list):
                filtered_data = []
                for item in data:
                    # Per ogni elemento, valuta la condizione
                    if isinstance(item, dict):
                        # Sostituisce i riferimenti alle proprietà con i valori reali
                        eval_condition = condition
                        for key, value in item.items():
                            if isinstance(value, (int, float, bool)):
                                # Per i tipi numerici e booleani
                                eval_condition = re.sub(r'\b' + key + r'\b', str(value), eval_condition)
                            elif isinstance(value, str):
                                # Per le stringhe
                                eval_condition = re.sub(r'\b' + key + r'\b', f"'{value}'", eval_condition)
                        
                        # Valuta la condizione
                        try:
                            if eval(eval_condition):
                                filtered_data.append(item)
                        except Exception as e:
                            self._log_warning(f"Errore nella valutazione della condizione per l'elemento: {str(e)}")
                    else:
                        # Per elementi non dict, controlla se soddisfano direttamente la condizione
                        try:
                            value_condition = condition.replace("value", repr(item))
                            if eval(value_condition):
                                filtered_data.append(item)
                        except Exception as e:
                            self._log_warning(f"Errore nella valutazione della condizione per il valore: {str(e)}")
                
                return filtered_data
            else:
                self._log_warning("I dati non sono un array, il filtro funziona solo su array")
                return data
                
        except Exception as e:
            self._log_error(f"Errore nel filtraggio dei dati: {str(e)}")
            return data
    
    def _merge_objects(self, objects: List[Dict]) -> Dict:
        """
        Unisce più oggetti in un unico oggetto.
        
        Args:
            objects: Lista di oggetti da unire
            
        Returns:
            Oggetto unificato
        """
        if not objects:
            return {}
        
        try:
            result = {}
            for obj in objects:
                if isinstance(obj, dict):
                    result.update(obj)
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nell'unione degli oggetti: {str(e)}")
            return {}
    
    def _get_default_value(self) -> Any:
        """
        Restituisce il valore di default, convertendolo nel tipo appropriato se possibile.
        """
        default = self.default_value
        
        # Tenta di convertire il valore di default nel tipo appropriato
        try:
            # Prima prova a convertire in JSON
            return json.loads(default)
        except (json.JSONDecodeError, TypeError):
            # Se non è JSON valido, restituisci come stringa
            return default
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_warning(f"[JsonProcessor] ATTENZIONE: {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_error(f"[JsonProcessor] ERRORE: {message}")
        except Exception:
            pass
