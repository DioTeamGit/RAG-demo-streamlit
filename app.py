import streamlit as st
import openai
import qdrant_client
from llama_index.llms.openai import OpenAI
try:
  from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
except ImportError:
  from llama_index.core import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader, StorageContext

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings

def initialize_llm():
    Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
    embed_model = OpenAIEmbedding()
    Settings.embed_model = embed_model
#inizializzo llm
#initialize_llm()
st.set_page_config(page_title="Q&A con documenti", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = st.secrets.openai_key_p
st.title("Q&A con documenti")
         
if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Inizia una chat con i tuoi documenti!"}
    ]
client = qdrant_client.QdrantClient('https://46e915dc-c126-4445-af6d-265c738b7848.us-east4-0.gcp.cloud.qdrant.io:6333', api_key=st.secrets["qdrant_key"])
vector_store = QdrantVectorStore(client=client, collection_name="RAG_2")
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)




if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(chat_mode="openai, verbose=True)

if prompt := st.chat_input("Fai una domanda"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt, tool_choice="query_engine_tool")
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history
