# Archive

**Archived PramaIA Documentation**

Historical and obsolete documentation preserved for reference. This content is no longer actively maintained but kept for legacy reference and migration purposes.

---

## 📚 **Archive Purpose**

This archive contains:
- **Obsolete Documentation** - Superseded by newer versions
- **Legacy System Docs** - Pre-refactoring system documentation  
- **Deprecated Features** - Documentation for removed functionality
- **Historical References** - Important historical context

---

## ⚠️ **Important Notice**

**Content in this archive may be outdated, incorrect, or no longer applicable.**

For current documentation, please refer to:
- [Current Documentation Index](../README.md)
- [Implementation Status](../IMPLEMENTATION/IMPLEMENTATION_STATUS.md)
- [Services Documentation](../SERVICES/README.md)

---

## 📁 **Archive Structure**

### **Legacy Node Documentation**
*Archived during PDK Universal Architecture refactoring (2024 Q4)*
- `old-node-specifications/` - Pre-generic processor node documentation
- `deprecated-api-reference/` - Legacy API documentation
- `workflow-migration-notes/` - Notes from workflow migration process

### **Obsolete Setup Guides**
*Replaced by current setup procedures*
- `legacy-installation-guides/` - Outdated installation procedures
- `old-configuration-files/` - Superseded configuration examples
- `deprecated-environment-setup/` - Legacy development environment setup

### **Historical Architecture**
*Pre-microservices architecture documentation*  
- `monolithic-architecture-docs/` - Original system design documentation
- `legacy-database-schemas/` - Pre-vectorstore database designs
- `old-integration-patterns/` - Superseded integration approaches

---

## 🗂️ **Archive Index**

### **Recently Archived (2024)**

#### **PDK Legacy Nodes Documentation**
**Archived:** November 2024  
**Reason:** Replaced by Generic Processors  
**Migration Info:** See [PDK Refactoring Report](../IMPLEMENTATION/REFACTORING_REPORTS/)

- `specific-text-nodes.md` - Individual text processing nodes
- `document-specific-handlers.md` - Format-specific document processors  
- `vectorstore-specific-operations.md` - Database-specific vector operations
- `llm-provider-specific-nodes.md` - Provider-specific LLM integrations
- `system-task-specific-nodes.md` - Task-specific system operations

#### **Legacy Configuration Examples**
**Archived:** November 2024  
**Reason:** Configuration format changed  
**Migration Info:** See [Configuration Migration Guide](../IMPLEMENTATION/MIGRATION_GUIDES/)

- `old-plugin-configuration-examples.md`
- `legacy-workflow-definitions.md`
- `deprecated-service-configurations.md`

### **Older Archives (2024 Q1-Q3)**

#### **Pre-Microservices Documentation**
**Archived:** September 2024  
**Reason:** System architecture refactoring  

- `monolithic-deployment-guide.md`
- `single-service-architecture.md`
- `legacy-database-setup.md`

#### **Obsolete Development Guides**
**Archived:** June 2024  
**Reason:** Development process improvements  

- `old-plugin-development-tutorial.md`
- `legacy-testing-procedures.md`
- `deprecated-debugging-guides.md`

---

## 🔍 **Finding Archived Content**

### **Search Guidelines**
1. **Check Current Documentation First** - Most questions are answered in current docs
2. **Use Implementation Status** - See what's been replaced or updated
3. **Review Migration Guides** - Understand changes from legacy systems
4. **Archive Search** - Only if current docs don't have historical context needed

### **Archive Access**
```bash
# Archive is preserved in git history
git log --oneline --name-only | grep -E "\.md$"

# Find specific archived files
git log --follow -- path/to/archived/file.md

# Compare current vs archived versions
git diff HEAD~10 -- documentation/file.md
```

---

## ⚡ **Quick Migration Reference**

### **Node System Changes**
**Old:** Specific hardcoded nodes (e.g., `pdf-text-extractor`)  
**New:** Generic configurable processors (e.g., `generic-document-processor` with PDF config)  
**Migration:** [PDK Migration Guide](../IMPLEMENTATION/MIGRATION_GUIDES/PDK_2.0_MIGRATION.md)

### **Configuration Changes**
**Old:** Node-specific configuration files  
**New:** Universal processor configuration with strategies  
**Migration:** [Configuration Migration Guide](../IMPLEMENTATION/MIGRATION_GUIDES/CONFIGURATION_MIGRATION.md)

### **API Changes**  
**Old:** Node-specific endpoints  
**New:** Generic processor endpoints with configuration  
**Migration:** [API Migration Guide](../IMPLEMENTATION/MIGRATION_GUIDES/API_MIGRATION.md)

---

## 🗃️ **Archive Maintenance**

### **Archival Policy**
- **Major Version Changes** - Previous version documentation archived
- **Feature Deprecation** - Deprecated feature docs moved to archive
- **Architecture Changes** - Superseded architecture docs archived
- **Configuration Updates** - Old configuration examples archived

### **Retention Policy**
- **Recent Archives (0-1 year)** - Full preservation
- **Historical Archives (1-3 years)** - Selective preservation  
- **Ancient Archives (3+ years)** - Summary preservation only

### **Archive Updates**
Archives are **read-only** and not updated. For corrections or clarifications:
1. Update current documentation to clarify differences from legacy
2. Add notes in current documentation referencing archive content
3. Update migration guides to address specific archive content questions

---

## 🆘 **Using Archived Content**

### **When to Use Archives**
- **Understanding Legacy Systems** - Historical context for migrations
- **Debugging Legacy Issues** - Troubleshooting older installations
- **Architectural Evolution** - Understanding design decision history
- **Migration Planning** - Comparing old vs new implementations

### **When NOT to Use Archives**
- **Current Development** - Always use current documentation
- **New Installations** - Follow current setup procedures
- **Feature Implementation** - Use current API and configuration docs
- **Troubleshooting Active Systems** - Use current service documentation

---

## 🔗 **Archive References**

- **Current Documentation:** [Main Documentation](../README.md)
- **Migration Guides:** [Implementation/Migration Guides](../IMPLEMENTATION/MIGRATION_GUIDES/)
- **Change History:** [Changelogs](../CHANGELOGS/README.md)
- **Implementation Status:** [Implementation Documentation](../IMPLEMENTATION/README.md)

---

## 📞 **Archive Support**

For questions about archived content:
1. **Check Current Docs** - Verify if information is available in current documentation
2. **Review Migration Guides** - Most archive questions are answered in migration docs
3. **Implementation Status** - Check what's been replaced and why
4. **Development Guide** - General development questions should be directed to current guides

**Note:** Archived content is preserved as-is and may contain outdated or incorrect information. Always prefer current documentation for active development.