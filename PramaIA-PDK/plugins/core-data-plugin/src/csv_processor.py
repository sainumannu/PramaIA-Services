import csv
import io
import re
import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Union

class CsvProcessor:
    """
    Processore per elaborare e manipolare dati CSV.
    Supporta parsing, filtro, selezione colonne e conversione di formato.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        self.has_header = config.get("has_header", True)
        self.delimiter = config.get("delimiter", ",")
        self.output_format = config.get("output_format", "array")
        self.filter_expression = config.get("filter_expression", "")
        self.selected_columns = config.get("selected_columns", "")
        
        # Converte selected_columns in una lista se è una stringa
        if isinstance(self.selected_columns, str) and self.selected_columns:
            self.selected_columns = [col.strip() for col in self.selected_columns.split(",")]
        else:
            self.selected_columns = []
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora i dati CSV in base alla configurazione.
        
        Args:
            inputs: Dizionario con i dati CSV e opzionalmente una query
            
        Returns:
            Dizionario con il risultato dell'elaborazione
        """
        if "data" not in inputs:
            raise ValueError("Input 'data' richiesto ma non fornito")
        
        data = inputs["data"]
        query = inputs.get("query", "")
        
        try:
            # Converte i dati in un DataFrame pandas per una facile manipolazione
            df = self._to_dataframe(data)
            
            # Applica query SQL-like se specificata
            if query:
                df = self._apply_query(df, query)
            # Altrimenti applica filtro e selezione colonne dalla configurazione
            else:
                # Applica filtro se specificato
                if self.filter_expression:
                    df = self._apply_filter(df, self.filter_expression)
                
                # Seleziona colonne se specificate
                if self.selected_columns:
                    df = self._select_columns(df, self.selected_columns)
            
            # Converte il risultato nel formato richiesto
            result = self._convert_output(df)
            
            return {"result": result}
            
        except Exception as e:
            self._log_error(f"Errore nell'elaborazione dei dati CSV: {str(e)}")
            return {"result": []}
    
    def _to_dataframe(self, data: Union[str, List]) -> pd.DataFrame:
        """
        Converte i dati in un DataFrame pandas.
        
        Args:
            data: Dati CSV come stringa o percorso file o lista
            
        Returns:
            DataFrame pandas
        """
        if isinstance(data, str):
            # Controlla se è un percorso file o una stringa CSV
            if "\n" in data or "," in data or ";" in data:
                # Sembra essere una stringa CSV
                return pd.read_csv(
                    io.StringIO(data),
                    header=0 if self.has_header else None,
                    delimiter=self.delimiter
                )
            else:
                # Probabilmente un percorso file
                try:
                    return pd.read_csv(
                        data,
                        header=0 if self.has_header else None,
                        delimiter=self.delimiter
                    )
                except Exception as e:
                    self._log_error(f"Errore nella lettura del file CSV: {str(e)}")
                    raise ValueError(f"Impossibile leggere il file CSV: {str(e)}")
        elif isinstance(data, list):
            # Se è già una lista, converte in DataFrame
            if data and isinstance(data[0], dict):
                # Lista di dizionari
                return pd.DataFrame(data)
            else:
                # Lista di liste
                return pd.DataFrame(
                    data,
                    columns=data[0] if self.has_header else None
                ).iloc[1:] if self.has_header else pd.DataFrame(data)
        else:
            raise ValueError("Formato dati non supportato. Deve essere stringa CSV, percorso file o lista.")
    
    def _apply_query(self, df: pd.DataFrame, query: str) -> pd.DataFrame:
        """
        Applica una query SQL-like al DataFrame.
        
        Args:
            df: DataFrame pandas
            query: Query SQL-like
            
        Returns:
            DataFrame filtrato
        """
        try:
            # Utilizzo della funzionalità query di pandas
            return df.query(query)
        except Exception as e:
            self._log_warning(f"Errore nell'applicazione della query: {str(e)}. Query ignorata.")
            return df
    
    def _apply_filter(self, df: pd.DataFrame, filter_expression: str) -> pd.DataFrame:
        """
        Applica un'espressione di filtro al DataFrame.
        
        Args:
            df: DataFrame pandas
            filter_expression: Espressione di filtro
            
        Returns:
            DataFrame filtrato
        """
        try:
            # Utilizzo della funzionalità query di pandas
            return df.query(filter_expression)
        except Exception as e:
            self._log_warning(f"Errore nell'applicazione del filtro: {str(e)}. Filtro ignorato.")
            return df
    
    def _select_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Seleziona colonne specifiche dal DataFrame.
        
        Args:
            df: DataFrame pandas
            columns: Lista di nomi di colonne
            
        Returns:
            DataFrame con solo le colonne selezionate
        """
        # Filtra per includere solo le colonne esistenti
        valid_columns = [col for col in columns if col in df.columns]
        
        if not valid_columns:
            self._log_warning("Nessuna delle colonne specificate esiste nei dati. Tutte le colonne saranno incluse.")
            return df
        
        return df[valid_columns]
    
    def _convert_output(self, df: pd.DataFrame) -> Any:
        """
        Converte il DataFrame nel formato di output richiesto.
        
        Args:
            df: DataFrame pandas
            
        Returns:
            Dati nel formato richiesto
        """
        if self.output_format == "array":
            # Converti in lista di dizionari (array di oggetti)
            return df.to_dict(orient="records")
        elif self.output_format == "json":
            # Converti in stringa JSON
            return df.to_json(orient="records")
        elif self.output_format == "csv":
            # Converti in stringa CSV
            return df.to_csv(index=False)
        else:
            # Default: lista di dizionari
            return df.to_dict(orient="records")
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    logging.getLogger(__name__).warning(f"[CsvProcessor] ATTENZIONE: {message}")
    
    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    logging.getLogger(__name__).error(f"[CsvProcessor] ERRORE: {message}")
