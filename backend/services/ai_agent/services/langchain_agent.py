from __future__ import annotations

import logging

from decouple import config, UndefinedValueError
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Eres un asistente de inventario para LiteThinking.
Tienes acceso a una base de datos de productos e inventario mediante la herramienta buscar_productos.

REGLAS OBLIGATORIAS:
1. SIEMPRE usa la herramienta buscar_productos antes de responder cualquier pregunta sobre productos, inventario o empresas.
2. Nunca respondas con información de tu conocimiento general sobre productos o empresas - solo usa lo que devuelve la herramienta.
3. Si el usuario pregunta por empresas, busca productos con una query genérica para ver qué empresas aparecen en los resultados.
4. Si la herramienta no retorna resultados, informa que no hay datos en el sistema para esa búsqueda.
5. Responde siempre en español. Sé conciso y útil."""


def _get_llm():
    """
    Returns the configured LLM.
    Priority: GROQ_API_KEY → ANTHROPIC_API_KEY → raises.
    """
    try:
        groq_key = config("GROQ_API_KEY")
        from langchain_groq import ChatGroq
        logger.info("LLM: Groq (llama-3.3-70b-versatile)")
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0,
        )
    except UndefinedValueError:
        pass

    try:
        anthropic_key = config("ANTHROPIC_API_KEY")
        from langchain_anthropic import ChatAnthropic
        logger.info("LLM: Anthropic (claude-sonnet-4-6)")
        return ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=anthropic_key,
            temperature=0,
        )
    except UndefinedValueError:
        pass

    raise RuntimeError(
        "No LLM configured. Set GROQ_API_KEY or ANTHROPIC_API_KEY in .env"
    )


def build_inventory_agent(db: Session) -> AgentExecutor:
    """
    Build a LangChain agent with pgvector semantic search tool.
    Uses Groq (primary) or Anthropic (fallback) as the LLM.
    """
    from services.embedding_service import semantic_search_productos

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
                f"- [{r['codigo']}] {r['nombre']}\n"
                f"  Empresa: {r['empresa_nombre']} (NIT: {r['empresa_nit']})\n"
                f"  Características: {r['caracteristicas'] or 'N/A'}\n"
                f"  Similitud: {r['similarity']:.2f}"
            )
        return "\n\n".join(formatted)

    llm = _get_llm()

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
    except RuntimeError as exc:
        logger.error("LLM not configured: %s", exc)
        return "El agente no está configurado. Revisa GROQ_API_KEY o ANTHROPIC_API_KEY en .env"
    except Exception as exc:
        logger.error("Agent error: %s", exc)
        return f"Error al procesar la consulta: {exc}"
