import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.vector_store import build_vector_store, get_retriever


def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


def build_rag_chain(transcript: str, k: int = 4):
    """
    Builds the Chroma vector store from the transcript and returns a retriever.
    This retriever is what gets stored as r['rag_chain'] in app.py.
    """
    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k=k)
    return retriever


def ask_question(rag_chain, question: str) -> str:
    """
    rag_chain here is the retriever returned by build_rag_chain.
    Retrieves relevant chunks from Chroma, then asks the LLM to answer
    using only that context.
    """
    llm = get_llm()

    docs = rag_chain.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Answer the question using only the meeting transcript context below. "
            "If the answer isn't in the context, say you don't know.\n\n"
            "Context:\n{context}",
        ),
        ("human", "{question}"),
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"context": context, "question": question})