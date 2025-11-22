from typing import Dict, Any, List, Optional, Union

class DataMerger:
    """
    Processore per unire più fonti di dati.
    Supporta concatenazione, join, zip e unione di oggetti.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        self.merge_type = config.get("merge_type", "concat")
        self.join_key = config.get("join_key", "id")
        self.join_type = config.get("join_type", "inner")
        self.flatten_result = config.get("flatten_result", False)
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unisce i dati in base alla configurazione.
        
        Args:
            inputs: Dizionario con i dati da unire
            
        Returns:
            Dizionario con il risultato dell'unione
        """
        if "data1" not in inputs or "data2" not in inputs:
            raise ValueError("Input 'data1' e 'data2' richiesti ma non forniti")
        
        data1 = inputs["data1"]
        data2 = inputs["data2"]
        data3 = inputs.get("data3", None)
        
        # Raccogli tutti i dati non nulli
        all_data = [data for data in [data1, data2, data3] if data is not None]
        
        try:
            # Esegue l'operazione di unione selezionata
            if self.merge_type == "concat":
                result = self._concat_data(all_data)
            elif self.merge_type == "join":
                result = self._join_data(data1, data2, data3)
            elif self.merge_type == "zip":
                result = self._zip_data(all_data)
            elif self.merge_type == "merge_objects":
                result = self._merge_objects(all_data)
            else:
                raise ValueError(f"Tipo di unione non supportato: {self.merge_type}")
            
            # Appiattisce il risultato se richiesto
            if self.flatten_result:
                result = self._flatten(result)
            
            return {"result": result}
            
        except Exception as e:
            self._log_error(f"Errore nell'unione dei dati: {str(e)}")
            return {"result": []}
    
    def _concat_data(self, data_list: List[Any]) -> List[Any]:
        """
        Concatena più liste in una singola lista.
        
        Args:
            data_list: Lista di dati da concatenare
            
        Returns:
            Lista concatenata
        """
        result = []
        
        for data in data_list:
            if isinstance(data, list):
                result.extend(data)
            else:
                # Se non è una lista, aggiungilo come elemento singolo
                result.append(data)
        
        return result
    
    def _join_data(self, data1: Any, data2: Any, data3: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Esegue un join tra liste di dizionari.
        
        Args:
            data1: Prima lista di dizionari
            data2: Seconda lista di dizionari
            data3: Terza lista di dizionari (opzionale)
            
        Returns:
            Lista di dizionari risultante dal join
        """
        # Converte in lista se non lo è già
        if not isinstance(data1, list):
            data1 = [data1] if isinstance(data1, dict) else []
        if not isinstance(data2, list):
            data2 = [data2] if isinstance(data2, dict) else []
        if data3 is not None and not isinstance(data3, list):
            data3 = [data3] if isinstance(data3, dict) else []
        
        # Costruisce indici per un join efficiente
        index2 = self._build_index(data2, self.join_key)
        index3 = self._build_index(data3, self.join_key) if data3 is not None else {}
        
        result = []
        
        # Esegue il join in base al tipo selezionato
        if self.join_type in ["inner", "left"]:
            # Per inner join e left join, iteriamo su data1
            for item1 in data1:
                key_value = item1.get(self.join_key)
                if key_value in index2:
                    # Abbiamo una corrispondenza in data2
                    item2 = index2[key_value]
                    if data3 is not None and key_value in index3:
                        # Abbiamo anche una corrispondenza in data3
                        item3 = index3[key_value]
                        merged_item = {**item1, **item2, **item3}
                    else:
                        # Solo data1 e data2
                        merged_item = {**item1, **item2}
                    result.append(merged_item)
                elif self.join_type == "left":
                    # Per left join, includiamo comunque l'elemento di data1
                    if data3 is not None and key_value in index3:
                        # Abbiamo una corrispondenza in data3 ma non in data2
                        item3 = index3[key_value]
                        merged_item = {**item1, **item3}
                    else:
                        # Solo data1
                        merged_item = {**item1}
                    result.append(merged_item)
        
        if self.join_type in ["right", "full"]:
            # Per right join e full join, iteriamo su data2
            for item2 in data2:
                key_value = item2.get(self.join_key)
                if key_value not in index2:
                    # Salta gli elementi già processati durante l'iterazione su data1
                    continue
                
                if key_value not in self._build_index(data1, self.join_key):
                    # Elemento in data2 ma non in data1
                    if data3 is not None and key_value in index3:
                        # Abbiamo una corrispondenza in data3
                        item3 = index3[key_value]
                        merged_item = {**item2, **item3}
                    else:
                        # Solo data2
                        merged_item = {**item2}
                    result.append(merged_item)
        
        if self.join_type == "full" and data3 is not None:
            # Per full join, aggiungiamo anche gli elementi solo in data3
            for key_value, item3 in index3.items():
                if key_value not in self._build_index(data1, self.join_key) and key_value not in index2:
                    # Elemento solo in data3
                    result.append({**item3})
        
        return result
    
    def _build_index(self, data: List[Dict[str, Any]], key: str) -> Dict[Any, Dict[str, Any]]:
        """
        Costruisce un indice per i dati in base a una chiave.
        
        Args:
            data: Lista di dizionari
            key: Chiave per l'indice
            
        Returns:
            Dizionario con chiave -> elemento
        """
        if not isinstance(data, list):
            return {}
            
        index = {}
        for item in data:
            if isinstance(item, dict) and key in item:
                index[item[key]] = item
        return index
    
    def _zip_data(self, data_list: List[Any]) -> List[List[Any]]:
        """
        Combina più liste elemento per elemento.
        
        Args:
            data_list: Lista di liste da combinare
            
        Returns:
            Lista di liste combinate
        """
        # Converte ogni elemento in lista se non lo è già
        lists = []
        for data in data_list:
            if isinstance(data, list):
                lists.append(data)
            else:
                lists.append([data])
        
        # Usa zip per combinare gli elementi
        return list(map(list, zip(*lists)))
    
    def _merge_objects(self, data_list: List[Any]) -> Dict[str, Any]:
        """
        Unisce più dizionari in un unico dizionario.
        
        Args:
            data_list: Lista di dizionari da unire
            
        Returns:
            Dizionario unificato
        """
        result = {}
        
        for data in data_list:
            if isinstance(data, dict):
                # Unisce i dizionari
                result.update(data)
            elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                # Se è una lista di dizionari, unisce tutti i dizionari
                for item in data:
                    result.update(item)
        
        return result
    
    def _flatten(self, data: Any) -> List[Any]:
        """
        Appiattisce dati annidati in una lista semplice.
        
        Args:
            data: Dati da appiattire
            
        Returns:
            Lista appiattita
        """
        result = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    # Appiattisce ricorsivamente le liste annidate
                    result.extend(self._flatten(item))
                else:
                    result.append(item)
        else:
            result.append(data)
        
        return result
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        print(f"[DataMerger] ATTENZIONE: {message}")
    
    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        print(f"[DataMerger] ERRORE: {message}")
