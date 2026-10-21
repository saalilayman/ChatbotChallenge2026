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

Reply with the answer only. No explanation, no preamble and do NOT say "The context does not specify" or  "My best guess is".
If the context does not contain the answer, give your best guess anyway. Never reply that you do not know.

How to interpret the context:
Table Data: HTML tables are formatted with "|" separating columns. When reading a row, carefully map each value back to its exact corresponding column header from the top of the table.
Timelines: If a question specifies a year, extract the fact for that exact year and ignore past/future data.
Specificity: Return the exact names or values requested. For broad technologies, use the industry category.
Exhaustive Extraction: If asked for items, read the ENTIRE context chunk and list EVERY matching item. Never stop at the first partial match.
Multi-part Questions: If a question asks for multiple things (e.g., a number AND an object), ensure your answer addresses all parts.

Output format:
Reply with ONLY the final concise answer or comma-separated list. No conversational filler.
Include modifiers like "at least" or "about" if present in the text.
"""

CONFIG = {
    "k": 5,
    "temperature": 0.0,
    "max_tokens": 256,
}

test_questions = [
"What time was the robot arm challenge held at?",
"How many chairs are in the Tam Wing Fan Inno Wing Two?",
"How many people won the pitch competition on grand challenge engineering, and what award did they win?", 
"What is club grenade?", 
"What are the themes for the pitching contest for engineering msc students?",
"Who was the speaker for the techtalk, and which room was it held in?",
"How many people visited UNSW Sydney on the study tour?",
"How many people attended the ASTAR course?",
"Who were the sponsors for the HKU racing team's (HKUR) racecar?",
"How many people built a plane as part of the HKU design, build and fly club?",
]

test_questions_2 = [
"How many people visited UNSW Sydney on the study tour?",
"How many people attended the ASTAR course?",
]

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
    """One question in, one answer out.

    Runs once per question with a 30 second budget. Anything expensive
    belongs in build/, not here.
    """
    chunks = retrieve(question)

    # TODO [W2 b4] once this works: decompose compound questions,
    # TODO retrieve wide then filter, or filter by metadata before
    # TODO searching.

    context = "\n\n".join(
        f"[{c['metadata'].get('url', '?')}]\n{c['text']}" for c in chunks
    )

    reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ])

    # TODO check the format of what came back: if you asked for a
    # TODO number, make sure you got one, and strip any stray prose.
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


print(rag_answer(test_questions[8]))