FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Install ACC with tree-sitter file slicer support
RUN pip install .[slicer]

# Expose port for REST API mode (used with docker-compose)
EXPOSE 8000

# Default to stdio MCP mode
ENTRYPOINT ["acc-mcp"]
