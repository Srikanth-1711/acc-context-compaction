# ACC Architecture Guidelines

## Dependency Boundaries
To prevent the codebase from becoming tightly coupled, the following strict boundaries are enforced:

### The Rule of Dependency Injection
Lower-level components (Core, Schemas, Repositories) must **never** import higher-level components (API, Services, MCP). 

1. **`acc.core`**: Has no dependencies. Configs and Loggers.
2. **`acc.schemas`**: Can import `acc.core`. Used universally.
3. **`acc.filters`**: Pure functions. No external logic.
4. **`acc.memory` (Models & Repositories)**: Can import `acc.schemas`.
5. **`acc.compaction` (Proxy/Parsers)**: Can import `acc.filters`.
6. **`acc.services`**: Orchestrates logic. Can import `acc.schemas`, `acc.memory`, and `acc.compaction`.
7. **`acc.api`**: Can import `acc.services` and `acc.schemas`.
8. **`acc.mcp`**: Can import `acc.services` and `acc.schemas`.

If you find `acc.memory` importing `acc.api`, the build will fail code reviews. Keep modules independent and loosely coupled.
