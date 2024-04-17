import re
import faiss
import numpy as np 
from io import BytesIO
from typing import Tuple
from typing import List
from typing import Any
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from router import EmbeddingHandler

class RetrievalAugmentedGeneration(EmbeddingHandler): 
    def __init__(self): 
        super().__init__()
        self.index = None
        self.documents = []

    def parse_text(self, text: str) -> str: 
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text
    
    def parse_pdf(self, file_bytes: BytesIO) -> Tuple[List[str], str]:
        pdf = PdfReader(file_bytes)
        return [self.parse_text(page.extract_text()) for page in pdf.pages]

    def text_to_docs(self, text: List[str]) -> List[Document]:
        if isinstance(text, str):
            text = [text]
        page_docs = [Document(page_content=page) for page in text]

        doc_chunks = []
        for doc in page_docs:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
                chunk_overlap=0,
            )
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks: 
                doc_chunks.append(chunk)
        return doc_chunks

    def docs_to_index(self):
        embeddings = np.array([self.get_embedding(d) for d in self.documents], dtype='float32')
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        return index

    def build_index(self, files: Any) -> None:
        pdf_files = [pdf.getvalue() for pdf in files]
        for pdf_file in pdf_files:
            text = self.parse_pdf(BytesIO(pdf_file))
            self.documents = self.documents + self.text_to_docs(text)
        self.index = self.docs_to_index()
    
    def search_index(self, query: str, k: int) -> List[str]: 
        assert self.index, 'The vector index does not exist.'
        assert len(self.documents) > 0, 'There are no documents.'

        query_embedding = np.array([self.get_embedding(query)], dtype='float32')
        distances, indices = self.index.search(query_embedding, k)
        return [self.documents[i] for _, i in zip(distances[0], indices[0])]
