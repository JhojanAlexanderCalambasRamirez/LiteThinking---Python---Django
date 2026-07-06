from __future__ import annotations

import logging

from decouple import config
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
from sqlalchemy.orm import Session

from services.embedding_service import semantic_search_productos

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Eres un asistente de inventario para LiteThinking.
Tu función es ayudar a los usuarios a encontrar información sobre productos y empresas en el sistema.
Usa las herramientas disponibles para buscar productos de forma semántica.
Responde siempre en español. Sé conciso y útil.
Si no encuentras resultados relevantes, indícalo claramente."""


def build_inventory_agent(db: Session) -> AgentExecutor:
    """
    Build a LangChain agent with pgvector semantic search tool.
    Uses Anthropic Claude as the LLM.
    """

    @tool
    def buscar_productos(query: str, empresa_nit: str | None = None) -> str:
        """
        Busca productos usando búsqueda semántica (pgvector).
        Usa esta herramienta cuando el usuario pregunte por productos, características, o inventario.
        Parámetros:
        - query: descripción o pregunta sobre el producto
        - empresa_nit: NIT de la empresa para filtrar (opcional)
        """
        results = semantic_search_productos(db, query, empresa_nit, top_k=5)
        if not results:
            return "No se encontraron productos relacionados con la búsqueda."
        formatted = []
        for r in results:
            formatted.append(
                f"- [{r['codigo']}] {r['nombre']} "
                f"(Empresa: {r['empresa_nit']}, "
                f"Similitud: {r['similarity']:.2f})\n"
                f"  Características: {r['caracteristicas'] or 'N/A'}"
            )
        return "\n".join(formatted)

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=config("ANTHROPIC_API_KEY"),
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    tools = [buscar_productos]
    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=5,
        handle_parsing_errors=True,
    )


async def run_agent_query(db: Session, query: str, empresa_nit: str | None = None) -> str:
    """Run a single query through the inventory agent."""
    try:
        agent_executor = build_inventory_agent(db)
        full_query = query
        if empresa_nit:
            full_query = f"{query} (filtrar por empresa NIT: {empresa_nit})"
        result = agent_executor.invoke({"input": full_query})
        return result.get("output", "No se pudo generar una respuesta.")
    except Exception as exc:
        logger.error("Agent error: %s", exc)
        return f"Error al procesar la consulta: {exc}"
