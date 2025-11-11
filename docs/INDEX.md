# Documentation Index

Welcome to the City Rides Analytics Dashboard documentation!

**Project Status:** Phase 3 Complete (API Layer) | Phase 4 In Progress (Dashboards)

## 📚 For Human Collaborators

Navigate to the `human/` folder for user-facing documentation:

### Getting Started

- **[README.md](human/README.md)** - Project overview, quick start, and architecture
- **[SETUP.md](human/SETUP.md)** - Detailed installation and configuration guide
- **[IMPLEMENTATION_GUIDE.md](human/IMPLEMENTATION_GUIDE.md)** - Complete step-by-step implementation guide with 25 steps

### Technical Reference

- **[DATABASE.md](human/DATABASE.md)** - Database schema, tables, indexes, and maintenance
- **[ANALYTICS.md](human/ANALYTICS.md)** - SQL query examples and analytics patterns
- **[API.md](human/API.md)** - REST API documentation and endpoints (13 endpoints)
- **[METABASE_SETUP.md](human/METABASE_SETUP.md)** - Metabase installation and dashboard creation guide

## 🤖 For AI Assistants

Navigate to the `ai/` folder for AI-optimized context:

### AI Context Files

- **[PROJECT_CONTEXT.md](ai/PROJECT_CONTEXT.md)** - Architecture, design decisions, and project structure
- **[DEVELOPMENT_GUIDE.md](ai/DEVELOPMENT_GUIDE.md)** - Coding standards, patterns, and best practices
- **[SCHEMA_REFERENCE.md](ai/SCHEMA_REFERENCE.md)** - Quick database schema reference with query patterns
- **[PROGRESS.md](ai/PROGRESS.md)** - Detailed project progress and completion status
- **[PHASE3_SUMMARY.md](ai/PHASE3_SUMMARY.md)** - FastAPI implementation summary
- **[PHASE4_SUMMARY.md](ai/PHASE4_SUMMARY.md)** - Metabase dashboard specifications

## 🎯 Quick Navigation by Task

### "I want to set up the project"

→ Start with [human/SETUP.md](human/SETUP.md)

### "I want to understand the implementation plan"

→ Read [human/IMPLEMENTATION_GUIDE.md](human/IMPLEMENTATION_GUIDE.md)

### "I want to write SQL queries"

→ Check [human/ANALYTICS.md](human/ANALYTICS.md) and [ai/SCHEMA_REFERENCE.md](ai/SCHEMA_REFERENCE.md)

### "I want to understand the database"

→ See [human/DATABASE.md](human/DATABASE.md)

### "I want to use the API"

→ Review [human/API.md](human/API.md)

### "I want to create dashboards"

→ See [human/METABASE_SETUP.md](human/METABASE_SETUP.md) and [ai/PHASE4_SUMMARY.md](ai/PHASE4_SUMMARY.md)

### "I'm an AI helping with this project"

→ Read all files in `ai/` folder first, then reference `human/` as needed

## 📊 Documentation Structure

```text
docs/
├── INDEX.md (this file)
├── human/                          # For people
│   ├── README.md                  # Project overview
│   ├── SETUP.md                   # Setup instructions
│   ├── IMPLEMENTATION_GUIDE.md    # Step-by-step guide (25 steps)
│   ├── DATABASE.md                # Database documentation
│   ├── ANALYTICS.md               # Query examples
│   ├── API.md                     # API documentation
│   └── METABASE_SETUP.md          # Dashboard setup
└── ai/                             # For AI assistants
    ├── PROJECT_CONTEXT.md         # Architecture & decisions
    ├── DEVELOPMENT_GUIDE.md       # Coding standards
    ├── SCHEMA_REFERENCE.md        # Quick schema reference
    ├── PROGRESS.md                # Project progress tracking
    ├── PHASE2_SUMMARY.md          # Analytics phase summary
    ├── PHASE3_SUMMARY.md          # API phase summary
    └── PHASE4_SUMMARY.md          # Dashboard phase summary
```

## 🔄 Keeping Documentation Updated

When making changes to the project:

1. **Schema changes** → Update `human/DATABASE.md` and `ai/SCHEMA_REFERENCE.md`
2. **New queries** → Add to `human/ANALYTICS.md`
3. **API changes** → Update `human/API.md`
4. **Architecture changes** → Update `ai/PROJECT_CONTEXT.md`
5. **New features** → Update `human/README.md` and `human/IMPLEMENTATION_GUIDE.md`

## 📝 Documentation Standards

- Use Markdown format
- Include code examples
- Keep examples up-to-date
- Add verification steps
- Document design decisions
- Update last modified date

---

**Last Updated:** November 9, 2025
**Project Version:** 1.0.0
