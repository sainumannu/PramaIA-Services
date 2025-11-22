# TEMPLATE: Documentazione Plugin PDK

## Panoramica
Breve descrizione del plugin e della sua funzionalità principale.

## Identificativo
- **ID Plugin**: `nome-plugin`
- **ID Nodo**: `nome_nodo`
- **Tipo**: `input/processing/output/control`
- **Categoria**: `Categoria del nodo`

## Ingressi
- **input1**: Descrizione del primo input
- **input2**: Descrizione del secondo input

## Uscite
- **output1**: Descrizione della prima uscita
- **output2**: Descrizione della seconda uscita

## Configurazione
Descrizione dei principali parametri di configurazione.

### Parametro 1
```json
{
  "param1": "valore1"
}
```
Spiegazione del parametro 1.

### Parametro 2
```json
{
  "param2": {
    "subparam1": "valore",
    "subparam2": 42
  }
}
```
Spiegazione del parametro 2.

## Esempio completo
```json
{
  "id": "esempio_nodo",
  "type": "pdk_nome-plugin_nome_nodo",
  "config": {
    "param1": "valore1",
    "param2": {
      "subparam1": "valore",
      "subparam2": 42
    }
  }
}
```

## Note di utilizzo
- Nota 1
- Nota 2
- Nota 3

## Compatibilità
- Versione PDK richiesta: x.y.z o superiore
- Compatibilità con altri nodi/plugin
