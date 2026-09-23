"""Your chatbot. STUB. This is the file you actually write.

Two functions must exist with these exact names and signatures. Every
other line in this file, and every file under build/, is yours to
rewrite.
"""
from bot.llm import chat
from bot.store import get_store, query

# --------------------------------------------------------------------
# The prompt. Workshop 1 block 2 covers what each part is doing.
# --------------------------------------------------------------------
SYSTEM_PROMPT = """You answer factual questions about the Tam Wing Fan Innovation Wing.
Answer directly from the provided context. Where the context disagrees with what
you think you know, the context is correct.

Reply with the answer only. No explanation, no preamble and do NOT say  
"The context does not specify" or  "My best guess is".
If the context does not contain the answer, give your best guess anyway. Never reply that you do not know.

How to interpret the context:
1. Table Data: HTML tables are formatted with "|" separating columns. When reading a row, carefully map each value back to its exact corresponding column header from the top of the table.
2. Timelines: If a question specifies a year, extract the fact for that exact year and ignore past/future data.
3. Specificity: Return the exact names or values requested. For broad technologies, use the industry category. 

Output format:
- Return ONLY the exact short answer. No conversational filler.
- If asked for a count or capacity, output digits only."""

CONFIG = {
    "k": 18,
    "temperature": 0.0,
    "max_tokens": 128,
}


def retrieve(question: str, k: int = None, where: dict = None) -> list[dict]:
    """Return the k chunks most relevant to the question.

    Kept separate from rag_answer on purpose: it lets you check whether
    an answer was ever fetched at all, which is the only way to tell a
    retrieval failure from a prompt failure. Do not delete it even if
    you rewrite everything else.
    """
    store = get_store()
    return query(store, question, k=k or CONFIG["k"], where=where)


def rag_answer(question: str) -> str:
    """One question in, one answer out."""
    chunks = retrieve(question) 
    
    context_blocks = []
    seen_texts = set()
    
    for c in chunks:
        body = c['text'].strip()
        
        # Deduplicate
        if body in seen_texts:
            continue
        seen_texts.add(body)
        
        # Extract metadata
        src = c['metadata'].get('url', 'document')
        year = c['metadata'].get('year', 'Unknown')
        
        # Format for LLM
        doc_num = len(context_blocks) + 1
        context_blocks.append(f"[Document {doc_num} | Year: {year} | Source: {src}]\n{body}")
        
    context = "\n\n---\n\n".join(context_blocks)
    
    reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"},
    ])
    
    return reply.strip()

def rag_answer_batch(questions: list[str]) -> list[str]:
    """Many questions in, the same number of answers out, in order.

    Ships as a loop, which is correct and is all most teams will need.
    Replace it if you can share work across questions: one embedding
    call for every query rather than one per query, the store opened
    once, sub-queries running concurrently.

    Whatever you do, answers[i] must be the answer to questions[i].
    """
    return [rag_answer(q) for q in questions]
