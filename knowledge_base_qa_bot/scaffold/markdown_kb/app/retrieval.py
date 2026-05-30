import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from . import indexer


# Design decision: Hallucination defense for raw Markdown context.
#
# Hints:
# 1. Only answer using the provided CONTEXT.
# 2. Cite only exact source IDs shown in [Source: ...].
#    Each source ID uses filename#heading format.
# 3. Define fallback behavior when the context lacks the answer.
# 4. Explicitly prohibit guessing or outside knowledge.
SYSTEM_PROMPT = """You are a highly precise, factual, and helpful Knowledge Base Q&A Assistant. Your task is to answer the user's question using ONLY the provided CONTEXT.

To prevent hallucinations and guarantee absolute correctness, you MUST strictly adhere to the following rules:

1. STRICT GROUNDEDNESS:
   - Your answers must be derived entirely from the facts directly mentioned in the provided CONTEXT.
   - Do NOT use any outside knowledge, assumptions, or general training knowledge.
   - Do NOT extrapolate or guess. If a fact is not explicitly stated in the CONTEXT, treat it as entirely unknown.

2. FALLBACK BEHAVIOR:
   - If the CONTEXT does not contain the answer to the user's question, or if the provided CONTEXT is empty or insufficient, you must reply exactly with: 
     "I cannot confirm from the knowledge base."
   - Do NOT try to answer using general knowledge or offer advice when the context lacks the answer.

3. SOURCE CITATIONS:
   - You must cite the source for every factual statement or claim you make.
   - Use the format `[filename#heading]` for citations (e.g., `[refund_policy.md#refund-timeline]`).
   - Place these citations naturally at the end of the sentence or clause that refers to that source.
   - Use only the filenames and headings provided in the CONTEXT. Never invent or assume sources.

4. STYLE & FORMATTING:
   - Keep your responses direct, clear, objective, and professional.
   - Avoid conversational filler or meta-commentary (e.g., do not say "Based on the context provided...").
"""

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            timeout=20,
            max_retries=0,
        )
    return _llm


def build_prompt(query: str, ranked_sections: list) -> str:
    # Design decision: Put raw Markdown sections into CONTEXT with citations.
    #
    # Hints:
    # 1. Include [Source: filename#heading] before each section.
    # 2. Include heading_path so the model sees the document structure.
    # 3. Include only top sections passed into this function.
    # 4. Place CONTEXT before QUESTION.
    context_parts = []
    for section, score in ranked_sections:
        heading_structure = " > ".join(section.heading_path)
        context_parts.append(
            f"[Source: {section.id}]\n"
            f"Document Path: {heading_structure}\n"
            f"Content:\n{section.content.strip()}"
        )
    
    context_str = "\n\n---\n\n".join(context_parts)
    
    return (
        f"CONTEXT:\n{context_str}\n\n"
        f"QUESTION:\n{query}"
    )


def query(question: str) -> dict:
    if not indexer.sections:
        return {
            "answer": "The knowledge base has not been indexed yet. Call POST /index first.",
            "sources": [],
        }

    ranked_sections = indexer.search(question, k=3)
    if not ranked_sections:
        return {
            "answer": "I cannot confirm from the knowledge base.",
            "sources": [],
        }

    response = get_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_prompt(question, ranked_sections)),
    ])

    sources = [
        {
            "source": section.id,
            "heading": " > ".join(section.heading_path),
            "score": round(score, 3),
            "content": section.content[:240],
        }
        for section, score in ranked_sections
    ]

    return {
        "answer": response.content,
        "sources": sources,
    }
