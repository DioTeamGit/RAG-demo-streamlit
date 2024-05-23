import streamlit as st
import openai
import qdrant_client
from llama_index.llms.openai import OpenAI
try:
  from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
except ImportError:
  from llama_index.core import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader, StorageContext

from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.core import Settings



st.set_page_config(page_title="Q&A con documenti", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = st.secrets.openai_key
st.title("Q&A con documenti")
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")
         
if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Inizia una chat con i tuoi documenti!"}
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the Streamlit docs – hang tight! This should take 1-2 minutes."):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        # llm = OpenAI(model="gpt-3.5-turbo", temperature=0.5, system_prompt="You are an expert o$
        # index = VectorStoreIndex.from_documents(docs)
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.5, system_prompt="Sei un avvocato specializzato in diritto del lavoro e il tuo compito è rispondere a domande tecniche in questo ambito relative ai documenti forniti. Mantieni le mie risposte tecniche e basate su fonti, senza inventare aspetti non supportati dalla legge. Rispondi solo in Italiano"))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

def load_data_qdrant():
  client = QdrantClient('https://46e915dc-c126-4445-af6d-265c738b7848.us-east4-0.gcp.cloud.qdrant.io', port=443, api_key=st.secrets.qdrant_key)
  reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
  documents = reader.load_data()
  collection_name = "RAG"
  vector_store = QdrantVectorStore(
      client=client,
      collection_name=collection_name,
      enable_hybrid=True,
  )

  storage_context = StorageContext.from_defaults(vector_store=vector_store)
  index = VectorStoreIndex.from_documents(
      documents,
      storage_context=storage_context,
  )
  return index

index = load_data_qdrant()




if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history
