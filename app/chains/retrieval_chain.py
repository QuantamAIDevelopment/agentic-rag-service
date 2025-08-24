"""LangChain HNSW Retrieval Chain."""

from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import SentenceTransformerEmbeddings

class HNSWRetrievalChain:
    def __init__(self):
        self.embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
        self.llm = ChatOpenAI(model="gpt-4")
        
        self.prompt = ChatPromptTemplate.from_template(
            "Context: {context}\nQuestion: {question}\nAnswer:"
        )
    
    def create_chain(self):
        return (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
        )

retrieval_chain = HNSWRetrievalChain()