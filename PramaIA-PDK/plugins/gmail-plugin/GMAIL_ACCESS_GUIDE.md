# 🔐 GMAIL: Username/Password - Guida Completa

## ❌ **Gmail NON accetta più password normali**

Dal **30 maggio 2022**, Google ha **disabilitato l'accesso con password normale** per app di terze parti per motivi di sicurezza.

## ✅ **3 METODI SUPPORTATI per Gmail**

---

## 🥇 **METODO 1: App Password (CONSIGLIATO)**

**✅ FUNZIONA**: Gmail permette "App Password" speciali per applicazioni esterne.

### Setup App Password:

1. **Abilita 2FA** (obbligatorio):
   - Vai su [myaccount.google.com](https://myaccount.google.com)
   - "Sicurezza" → "Verifica in due passaggi" → **ABILITA**

2. **Genera App Password**:
   - Sempre in "Sicurezza" → "Password per le app"
   - Seleziona "Posta" + "Computer Windows"
   - **Copia la password di 16 caratteri** (es: `abcd efgh ijkl mnop`)

3. **Configura nel plugin**:
```powershell
$env:GMAIL_USERNAME = "tuaemail@gmail.com"
$env:GMAIL_APP_PASSWORD = "abcd efgh ijkl mnop"
```

4. **Test**:
```powershell
python simple_gmail_test.py
```

### ✅ **Vantaggi App Password**:
- Semplice da configurare
- Funziona con IMAP/SMTP
- Non richiede OAuth2 complesso
- Accesso diretto alle email

---

## 🥈 **METODO 2: OAuth2 (PIÙ SICURO)**

Per accesso completo alle API Gmail (non solo IMAP).

### Setup OAuth2:

1. **Google Cloud Console**:
   - Crea progetto → Abilita Gmail API
   - Crea credenziali OAuth2
   - Scarica `credentials.json`

2. **Configura nel plugin**:
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

### ✅ **Vantaggi OAuth2**:
- Massima sicurezza
- Accesso completo API Gmail
- Tokens auto-refresh
- Controllo granulare permessi

---

## 🥉 **METODO 3: Account Google Workspace**

Solo per organizzazioni con Google Workspace.

### Setup Workspace:
- Admin console → Security → API controls
- Abilita "Less secure app access" (sconsigliato)

---

## 🔍 **CONFRONTO METODI**

| Metodo | Difficoltà | Sicurezza | IMAP | API Gmail | Consigliato |
|--------|-----------|-----------|------|-----------|-------------|
| **App Password** | 🟢 Facile | 🟡 Media | ✅ | ❌ | **✅ SÌ** |
| **OAuth2** | 🟡 Media | 🟢 Alta | ✅ | ✅ | 🟡 Avanzati |
| **Workspace** | 🔴 Difficile | 🔴 Bassa | ✅ | ❌ | ❌ NO |

---

## 🧪 **TEST RAPIDO**

Verifica quale metodo hai configurato:

```powershell
cd "C:\PramaIA-Services\PramaIA-PDK\plugins\email-reader-plugin"

# Test App Password
python simple_gmail_test.py

# Test completo plugin
python real_email_tests.py --gmail-test
```

---

## ❓ **DOMANDE FREQUENTI**

### **Q: "Can I use my normal Gmail password?"**
**A**: ❌ NO. Gmail ha bloccato questo metodo dal 2022. Devi usare App Password o OAuth2.

### **Q: "Dove trovo l'App Password?"**
**A**: [myaccount.google.com](https://myaccount.google.com) → Sicurezza → Password per le app (dopo aver abilitato 2FA).

### **Q: "L'App Password è sicura?"**
**A**: ✅ SÌ. È progettata specificamente per app esterne e ha permessi limitati.

### **Q: "Posso usare password normale con altri provider?"**
**A**: ✅ SÌ. Outlook/Hotmail e altri provider IMAP accettano ancora password normali.

---

## 🔧 **RISOLUZIONE PROBLEMI**

### Errore "Invalid credentials":
1. ✅ Verifica 2FA abilitata su Gmail
2. ✅ Usa App Password (non password normale)
3. ✅ Controlla IMAP abilitato: Gmail Settings → Forwarding/IMAP

### Errore "Connection refused":
1. ✅ Controlla connessione internet
2. ✅ Verifica firewall/antivirus
3. ✅ Prova porta 993 (IMAP SSL)

### App Password non funziona:
1. ✅ Verifica App Password corretta (16 caratteri, con spazi)
2. ✅ Rimuovi spazi se presenti: `abcdefghijklmnop`
3. ✅ Rigenera App Password se necessario

---

## 🎯 **RACCOMANDAZIONE**

**Per iniziare subito**: Usa **App Password** (Metodo 1)
- ⚡ Setup veloce (5 minuti)
- 🔒 Sufficientemente sicuro
- 🎯 Funziona perfettamente per lettura email

**Per produzione enterprise**: Usa **OAuth2** (Metodo 2)
- 🔐 Massima sicurezza
- 📊 Controllo completo
- 🚀 Scalabile per molti utenti

---

*Gmail ha fatto queste modifiche per migliorare la sicurezza. App Password è il metodo ufficiale raccomandato da Google per applicazioni esterne.*