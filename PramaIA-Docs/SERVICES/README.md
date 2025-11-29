# Services Documentation

**PramaIA Microservices Architecture**

Independent, scalable services that form the PramaIA ecosystem. Each service is designed for specific functionality and can be deployed separately.

---

## 🎯 **Active Services**

### **Core Services**
- **[VectorStore Service](VECTORSTORE_SERVICE_GUIDE.md)** - Vector database management
- **[Log Service](LOG_SERVICE_GUIDE.md)** - Centralized logging and monitoring  
- **[Reconciliation Service](RECONCILIATION_SERVICE_GUIDE.md)** - Data synchronization and consistency

### **Support Services**
- **PDK Server** - Plugin execution engine (see [PDK Documentation](../PDK/README.md))
- **Document Monitor Agent** - File system monitoring (see [Agents](../../PramaIA-Agents/README.md))

---

## 📖 **Documentation Index**

### **Architecture & Integration**
- **[VectorStore Architecture](VECTORSTORE_ARCHITECTURE.md)** - Complete vectorstore system design
- **[VectorStore Integration](VECTORSTORE_INTEGRATION.md)** - Integration patterns and APIs
- **[VectorStore Migration](VECTORSTORE_MIGRATION.md)** - Migration and upgrade procedures

### **Service Guides**
- **[VectorStore Service Guide](VECTORSTORE_SERVICE_GUIDE.md)** - Setup, configuration, and operation
- **[Log Service Guide](LOG_SERVICE_GUIDE.md)** - Logging service configuration and usage
- **[Reconciliation Service Guide](RECONCILIATION_SERVICE_GUIDE.md)** - Data reconciliation workflows

---

## 🏗️ **Service Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDK Server    │    │  VectorStore    │    │   Log Service   │
│   :3001         │◄──►│  Service :3002  │◄──►│   :3003         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │ Reconciliation  │
                    │ Service :3004   │
                    └─────────────────┘
```

---

## 🚀 **Quick Start**

### **Start All Services**
```bash
# From workspace root
.\start-all.ps1
```

### **Individual Service Management**
```bash
.\start-vectorstore.ps1     # VectorStore Service
.\start-backend.ps1         # PDK Server  
.\start-document-monitor.ps1 # Document Monitor
```

---

## 🔗 **Service Endpoints**

| Service | Port | Endpoint | Documentation |
|---------|------|----------|---------------|
| PDK Server | 3001 | http://localhost:3001/api | [PDK API](../PDK/API_DOCUMENTATION.md) |
| VectorStore | 3002 | http://localhost:3002/api | [VectorStore API](VECTORSTORE_INTEGRATION.md) |
| Log Service | 3003 | http://localhost:3003/logs | [Log Service API](LOG_SERVICE_GUIDE.md) |
| Reconciliation | 3004 | http://localhost:3004/reconcile | [Reconciliation API](../RECONCILIATION_API.md) |

---

## 📊 **Service Dependencies**

### **VectorStore Service**
- **Dependencies:** ChromaDB, OpenAI API
- **Data:** Vector embeddings, metadata
- **Integrations:** PDK workflows, document processing

### **Log Service** 
- **Dependencies:** SQLite database
- **Data:** Application logs, error tracking
- **Integrations:** All services for logging

### **Reconciliation Service**
- **Dependencies:** Service APIs
- **Data:** Cross-service state verification
- **Integrations:** Data consistency monitoring

---

## 🆘 **Troubleshooting**

- [Service Configuration](../CONFIGURATION_ENDPOINTS_SUMMARY.md) - Common configuration issues
- [Testing Guide](../TESTING/README.md) - Service testing procedures  
- [Implementation Status](../IMPLEMENTATION/IMPLEMENTATION_STATUS.md) - Current feature status

---

## 🔄 **Updates & Changes**

- [VectorStore Changelog](../CHANGELOGS/VECTORSTORE_CHANGELOG.md)
- [Log Service Changelog](../CHANGELOGS/LOG_SERVICE_CHANGELOG.md)
- [System Changelog](../CHANGELOGS/SYSTEM_CHANGELOG.md)