from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma

from dotenv import load_dotenv
from prompt import template

from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import RunnablePassthrough
load_dotenv()

#Chuyển các data về dạng document
loader = DirectoryLoader(
    path="./data",
    glob="**/*.pdf",
    loader_cls=PyPDFLoader,
    show_progress=True,
    use_multithreading=True
)

docs = loader.load()

# print(docs)
# print(len(docs))

MARKDOWN_SEPARATORS = [
    "\n#{1,6} ",
    "```\n",
    "\n\\*\\*\\*+\n",
    "\n--+\n",
    "\n___+\n",
    "\n\n",
    "\n",
    " ",
    "",
]

text_splitter = RecursiveCharacterTextSplitter(
    #Số lượng kí tự mỗi chunk
    chunk_size = 1200,

    chunk_overlap = 200,
    add_start_index = True,
    strip_whitespace = True,
    separators = MARKDOWN_SEPARATORS

)

#data sau khi chunking
splits = text_splitter.split_documents(docs)

#model để embedding
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

vector_store = Chroma(
    collection_name="My_document",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
        collection_configuration={
        "hnsw": {"space": "cosine"}
    },

)

#model thực hiện embedding sau đó được lưu vào db vector
vector_store.add_documents(documents=splits)

retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 5,
        "score_threshold": 0.2,
    },
)

prompt = ChatPromptTemplate.from_template(template)

llm = ChatGoogleGenerativeAI(
    model = "gemini-3.6-flash",
)

rag_chatbot = (
    {"context":retriever,"question":RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

question = input("Question: ")

answer = rag_chatbot.invoke(question)

print(answer)