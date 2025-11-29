# Configurazione Exchange/Office 365 Plugin

## Setup Azure AD App Registration

### 1. Registrazione Applicazione Azure AD

1. Vai al **Azure Portal** (portal.azure.com)
2. Naviga su **Azure Active Directory** > **App registrations**
3. Clicca **New registration**
4. Configura:
   - **Name**: `PramaIA Email Plugin`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Lascia vuoto per ora (necessario solo per web apps)
5. Clicca **Register**

### 2. Configurazione Permessi API

1. Nell'app appena creata, vai su **API permissions**
2. Clicca **Add a permission** > **Microsoft Graph** > **Delegated permissions**
3. Aggiungi i seguenti permessi:
   - `Mail.Read` - Lettura email dell'utente
   - `Mail.ReadWrite` - Lettura e scrittura email dell'utente  
   - `Mail.Send` - Invio email per conto dell'utente
   - `MailboxSettings.Read` - Lettura impostazioni mailbox
4. Per **shared mailbox**, aggiungi anche:
   - `Mail.Read.Shared` - Lettura email shared mailbox
   - `Mail.ReadWrite.Shared` - Scrittura email shared mailbox
   - `Mail.Send.Shared` - Invio da shared mailbox
5. Clicca **Grant admin consent** (se sei admin del tenant)

### 3. Configurazione Authentication

1. Vai su **Authentication**
2. Per **Public client applications**:
   - Clicca **Add a platform** > **Mobile and desktop applications**
   - Seleziona: `https://login.microsoftonline.com/common/oauth2/nativeclient`
3. Per **Client secrets** (confidential client):
   - Vai su **Certificates & secrets** > **Client secrets**
   - Clicca **New client secret**
   - Aggiungi descrizione e seleziona durata
   - **COPIA IL SECRET** (mostrato solo una volta)

### 4. Annotare Valori Necessari

Dal tuo **Azure AD App**:
- **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`  
- **Client secret**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (se necessario)

Dal tuo **Office 365 Environment**:
- **User Principal Name**: `user@yourdomain.com`
- **Shared Mailbox**: `shared@yourdomain.com` (se necessario)

## Metodi di Autenticazione Supportati

### 1. Device Code Flow (Raccomandato per test)
```python
success = await processor.authenticate_exchange_oauth2(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    use_device_flow=True
)
```

**Vantaggi:**
- Non richiede client secret
- Sicuro per test e sviluppo
- Supporta MFA

**Svantaggi:**
- Richiede interazione utente
- Non adatto per automazione

### 2. Username/Password Flow (ROPC)
```python
success = await processor.authenticate_exchange_oauth2(
    client_id="your-client-id",
    tenant_id="your-tenant-id", 
    username="user@domain.com",
    password="user-password"
)
```

**Vantaggi:**
- Completamente automatico
- Semplice da implementare

**Svantaggi:**
- Meno sicuro (password in chiaro)
- Deve essere abilitato in Azure AD
- Non supporta MFA
- **Microsoft sta deprecando questo flow**

### 3. Client Credentials Flow
```python
success = await processor.authenticate_exchange_oauth2(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    client_secret="your-client-secret"
)
```

**Vantaggi:**
- Sicuro per applicazioni server
- Completamente automatico
- Non richiede credenziali utente

**Svantaggi:**
- Richiede permessi Application (non Delegated)
- Accesso a tutte le mailbox del tenant
- Richiede admin consent

### 4. IMAP/SMTP Fallback
```python
success = await processor.authenticate_exchange_imap_smtp(
    email="user@domain.com",
    password="app-password-or-normal-password"
)
```

**Vantaggi:**
- Non richiede Azure AD setup
- Compatibile con client email tradizionali

**Svantaggi:**
- Meno funzionalità rispetto a Graph API
- Potrebbe richiedere App Password
- Microsoft preferisce Graph API

## Configurazioni Avanzate

### Shared Mailbox Access

Per accedere a shared mailbox, usa Graph API con sintassi:
```
/users/{shared-mailbox-email}/messages
```

Invece di:
```
/me/messages
```

### Custom Tenant Configuration

Per tenant personalizzati o Azure Government:
```python
EXCHANGE_CONFIGS['custom'] = {
    'authority': 'https://login.microsoftonline.us',  # Government cloud
    'graph_endpoint': 'https://graph.microsoft.us/v1.0'
}
```

### Proxy Configuration

Se necessario configurare proxy:
```python
import requests
session = requests.Session()
session.proxies = {'https': 'http://proxy:8080'}
# Passa session personalizzata alle chiamate Graph
```

## Esempi di Utilizzo

### Esempio Completo Device Flow
```python
import asyncio
from email_processor import EmailProcessor

async def test_exchange():
    processor = EmailProcessor()
    
    # Autentica con Device Flow
    success = await processor.authenticate_exchange_oauth2(
        client_id="12345678-1234-1234-1234-123456789012",
        tenant_id="87654321-4321-4321-4321-210987654321",
        use_device_flow=True
    )
    
    if success:
        # Lista email recenti  
        result = await processor._list_emails({
            'folder': 'INBOX',
            'max_emails': 10,
            'unread_only': True,
            'include_body': True
        })
        
        print(f"Trovate {result['data']['email_count']} email")
        
        # Invia email
        send_result = await processor._send_email({
            'to': 'recipient@domain.com',
            'subject': 'Test da Exchange Plugin',
            'body': 'Questo è un test di invio via Exchange Graph API'
        })
        
        print(f"Invio: {send_result['message']}")

asyncio.run(test_exchange())
```

## Troubleshooting

### Errori Comuni

1. **AADSTS70011: Invalid_scope**
   - Verifica che i permessi API siano configurati correttamente
   - Controlla che sia stato dato admin consent

2. **AADSTS50020: User account is not a valid user**  
   - Verifica username/password
   - Controlla che l'utente esista nel tenant

3. **AADSTS65001: Invalid client**
   - Verifica client_id e tenant_id
   - Controlla che l'app sia registrata correttamente

4. **Token expired or invalid (401)**
   - Il token è scaduto, riautentica
   - Verifica che i permessi siano sufficienti

### Debug Graph API

Per debug dettagliato delle chiamate Graph API:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Verifica Permessi

Per verificare i permessi del token corrente:
```bash
# Usa Graph Explorer: https://developer.microsoft.com/graph/graph-explorer
GET https://graph.microsoft.com/v1.0/me/oauth2PermissionGrants
```

## Sicurezza

1. **Non hardcodare mai** client secret nel codice
2. Usa **Azure Key Vault** per produzione
3. Implementa **token refresh** per session lunghe
4. Considera **certificate authentication** invece di client secret
5. Monitora l'accesso con **Azure AD logs**

## Risorse Utili

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Azure AD App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Graph Explorer](https://developer.microsoft.com/graph/graph-explorer) - Test interattivo API