# ADR-001: Backend Architecture Freeze

## Status
Accepted

## Context
Multiple backend runtime paths were being used during development. 
This creates confusion and deployment risk.

## Decision
The canonical backend repository will be the single production backend path.

All duplicate or experimental runtime paths are deprecated.

## Target Architecture
- Django
- Django REST Framework
- PostgreSQL
- Docker
- Celery (if used)
- MinIO (if used)

## Consequences
- Only one backend will be maintained
- All team members will use the same runtime path
- Deployment process becomes stable and predictable