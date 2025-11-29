# PramaIA Documentation Consolidation Plan

**Date:** November 26, 2025  
**Objective:** Consolidate all documentation under PramaIA-Docs with organized structure

---

## 📋 Current Documentation Audit

### Files Found (107 total .md files):

#### ✅ **Already in PramaIA-Docs (31 files)** - Keep as is
- ECOSYSTEM_OVERVIEW.md
- DEVELOPMENT_GUIDE.md
- EVENT_SOURCES_TRIGGERS_WORKFLOWS.md
- IMPLEMENTATION_STATUS.md
- PDK_PROXY_SOLUTION.md
- VECTORSTORE_API.md
- TEST_SUITE_GUIDE.md
- etc.

#### 📁 **Files to Migrate and Organize**

##### **1. PDK Core Documentation**
**Source:** `PramaIA-PDK/docs/` (12 files)
- ✅ `GUIDA_COMPLETA_CREAZIONE_PLUGIN_PDK.md` → `PDK/PLUGIN_DEVELOPMENT_GUIDE.md`
- ✅ `PDK-EVENT-SOURCES-DOCUMENTATION.md` → `PDK/EVENT_SOURCES_GUIDE.md`  
- ✅ `WORKFLOW_CREATION_GUIDE.md` → `PDK/WORKFLOW_CREATION_GUIDE.md`
- ✅ `WORKFLOW_TUTORIAL.md` → `PDK/WORKFLOW_TUTORIAL.md`
- ❌ `CONFIGURAZIONE_LOG_PDK.md` → Delete (covered by main docs)

##### **2. VectorStore Documentation**  
**Source:** `PramaIA-VectorstoreService/docs/` (3 files)
- ✅ `VECTORSTORE_ARCHITECTURE.md` → `SERVICES/VECTORSTORE_ARCHITECTURE.md`
- ✅ `INTEGRATION_GUIDE.md` → `SERVICES/VECTORSTORE_INTEGRATION.md`
- ✅ `DATABASE_MIGRATION.md` → `SERVICES/VECTORSTORE_MIGRATION.md`

##### **3. Service READMEs (Convert to Service Guides)**
**Source:** Various service folders
- ✅ `PramaIA-VectorstoreService/README.md` → `SERVICES/VECTORSTORE_SERVICE_GUIDE.md`
- ✅ `PramaIA-LogService/README.md` → `SERVICES/LOG_SERVICE_GUIDE.md` 
- ✅ `PramaIA-Reconciliation/README.md` → `SERVICES/RECONCILIATION_SERVICE_GUIDE.md`
- ❌ `PramaIA-PDK/server/README_LOGGING.md` → Delete (redundant)

##### **4. Plugin Documentation**
**Source:** `PramaIA-PDK/plugins/*/README.md` (8 files)
- ✅ `core-rag-plugin/README.md` → `PLUGINS/CORE_RAG_PLUGIN.md`
- ✅ `workflow-scheduler-plugin/README.md` → `PLUGINS/WORKFLOW_SCHEDULER_PLUGIN.md`
- ❌ Other plugin READMEs → Delete (outdated plugins)

##### **5. Workflow Templates**  
**Source:** `PramaIA-PDK/plugins/core-rag-plugin/workflow_templates/README.md`
- ✅ → `WORKFLOWS/TEMPLATES_GUIDE.md`

##### **6. Changelogs**
**Source:** Various services
- ✅ `PramaIA-VectorstoreService/CHANGELOG.md` → `CHANGELOGS/VECTORSTORE_CHANGELOG.md`
- ✅ `PramaIA-LogService/CHANGELOG.md` → `CHANGELOGS/LOG_SERVICE_CHANGELOG.md`

---

## 🗂️ **New PramaIA-Docs Structure**

```
PramaIA-Docs/
├── README.md (Master index)
├── ECOSYSTEM_OVERVIEW.md (Keep)
├── QUICK_START_GUIDE.md (Keep/rename)
├── 
├── PDK/
│   ├── README.md
│   ├── PLUGIN_DEVELOPMENT_GUIDE.md (from GUIDA_COMPLETA_CREAZIONE_PLUGIN_PDK.md)
│   ├── EVENT_SOURCES_GUIDE.md (from PDK-EVENT-SOURCES-DOCUMENTATION.md)
│   ├── WORKFLOW_CREATION_GUIDE.md (moved from docs)
│   ├── WORKFLOW_TUTORIAL.md (moved from docs)
│   ├── API_DOCUMENTATION.md (consolidated)
│   └── NODES_REFERENCE.md (consolidated)
│
├── SERVICES/
│   ├── README.md
│   ├── VECTORSTORE_ARCHITECTURE.md (from VectorstoreService/docs)
│   ├── VECTORSTORE_INTEGRATION.md (from VectorstoreService/docs)
│   ├── VECTORSTORE_MIGRATION.md (from VectorstoreService/docs)
│   ├── VECTORSTORE_SERVICE_GUIDE.md (from README)
│   ├── LOG_SERVICE_GUIDE.md (from LogService/README)
│   └── RECONCILIATION_SERVICE_GUIDE.md (from Reconciliation/README)
│
├── WORKFLOWS/
│   ├── README.md
│   ├── TEMPLATES_GUIDE.md (from plugin templates)
│   ├── EXAMPLES/ (move workflow examples)
│   └── BEST_PRACTICES.md (new)
│
├── PLUGINS/
│   ├── README.md
│   ├── CORE_RAG_PLUGIN.md (from plugin README)
│   ├── WORKFLOW_SCHEDULER_PLUGIN.md (from plugin README)
│   └── DEVELOPMENT_GUIDE.md (link to PDK guide)
│
├── TESTING/
│   ├── README.md
│   ├── TEST_SUITE_GUIDE.md (keep)
│   ├── TEST_SUITE_INDEX.md (keep)
│   └── INTEGRATION_TESTS.md (consolidated)
│
├── CHANGELOGS/
│   ├── README.md
│   ├── VECTORSTORE_CHANGELOG.md
│   ├── LOG_SERVICE_CHANGELOG.md
│   └── SYSTEM_CHANGELOG.md (consolidated)
│
├── IMPLEMENTATION/
│   ├── README.md
│   ├── IMPLEMENTATION_STATUS.md (keep)
│   ├── METADATA_IMPLEMENTATION_INDEX.md (keep)
│   ├── REFACTORING_REPORTS/ (for major changes)
│   └── MIGRATION_GUIDES/ (service migration guides)
│
└── ARCHIVE/ (obsolete documentation)
    ├── README.md (index of archived docs)
    └── [obsolete files moved here]
```

---

## 🎯 **Migration Actions**

### Phase 1: Create New Structure ✅
1. Create directory structure in PramaIA-Docs
2. Create README files for each category

### Phase 2: Migrate Content ✅
1. Copy and adapt important files
2. Update internal links
3. Consolidate similar content  

### Phase 3: Clean Up ✅
1. Remove duplicated files from original locations
2. Update references in code
3. Add redirects where necessary

### Phase 4: Maintenance ✅
1. Update main README with new structure
2. Create contribution guidelines
3. Set up documentation maintenance process

---

## ❌ **Files to Delete (Obsolete/Redundant)**

1. **PDK/docs/CONFIGURAZIONE_LOG_PDK.md** - Covered by main docs
2. **PDK/server/README_LOGGING.md** - Redundant logging info
3. **PDK/server/DEBUG_EXAMPLES.md** - Outdated debug examples
4. **Individual plugin READMEs** - Except core-rag and workflow-scheduler
5. **Event-source READMEs** - Consolidated into main event sources guide
6. **Test READMEs** - Consolidated into main testing guide
7. **Workflow example docs** - Consolidated into workflow guide
8. **Template README** - Merged into plugin development guide
9. **Outdated Add_New_Nodes_HOWTO.md** - Replaced by generic processors

---

## 📝 **Content Guidelines**

### Keep:
- Architecture documentation
- API references  
- Setup and configuration guides
- Migration guides
- Current implementation status
- Active plugin documentation

### Consolidate:
- Multiple similar guides
- Fragmented documentation on same topics
- READMEs with substantial content

### Delete:
- Outdated setup instructions
- Deprecated features documentation
- Empty or minimal READMEs
- Duplicated content
- Obsolete implementation details

---

**Next Steps:** Begin implementation of migration plan