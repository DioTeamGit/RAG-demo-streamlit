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




st.set_page_config(page_title="Iniziamo!", page_icon="⚖️", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = st.secrets.openai_key_p
st.title("Iniziamo!")

         
st.sidebar.title("Seleziona i parametri di input")
selection = st.sidebar.selectbox(
    "Seleziona una collezione di documenti:",
    ['RAG_4', 'ai_act&data_governance_act']
)
temperature = st.sidebar.slider("Seleziona la creatività della risposta", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

# Creazione del widget a tendina



Settings.llm = OpenAI(model="gpt-4o", temperature=temperature)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")  

    # Response format options
format = st.sidebar.radio("Seleziona formato della risposta", options=['Formato Libero','E-mail', 'Paragrafo', 'Lista'])
    
    # Legal query options
   # Use session state to store the selected query
if 'selected_query' not in st.session_state:
    st.session_state.selected_query = None

# Legal query buttons in Italian
st.write("Scegli un prompt")
query_texts = {
    "Termini del Contratto": "Spiega le considerazioni chiave per il seguente contratto nazionale",
    "Diritti dei Dipendenti": "Descrivi i diritti dei dipendenti riguardo al pagamento degli straordinari.",
    "Norme sul Licenziamento": "Quali sono le basi legali per il licenziamento?",
    "Sicurezza sul Lavoro": "Riassumi le responsabilità del datore di lavoro per la sicurezza sul lavoro."
}

for key, value in query_texts.items():
    if st.button(value):
        st.session_state.selected_query = key

# Display the response in the main area if a query is selected

if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Inizia una chat con i tuoi documenti!"}
    ]
client = qdrant_client.QdrantClient('https://46e915dc-c126-4445-af6d-265c738b7848.us-east4-0.gcp.cloud.qdrant.io:6333', api_key=st.secrets["qdrant_key"])
vector_store_4 = QdrantVectorStore(client=client, collection_name=selection)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store_4)

print(index)

if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(chat_mode="openai", verbose=True)

print(st.session_state.selected_query)

if st.session_state.selected_query != None:
  prompt=st.session_state.selected_query
else:
  prompt=st.chat_input("Fai una domanda")
  
if prompt: # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content":  prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

context= "Sei un avvocato. Devi usare sempre i documenti che hai a disposizione. cita sempre tutti i documenti che stai usando. \n"
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(context+prompt+"\n Utilizza come formato:"+ format , tool_choice="query_engine_tool") #query engine tool forza la ricerca
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history


# If last message is not from assistant, generate a new response
def reset_conversation():
    # Reset chat history and any other relevant state variables
    st.session_state.chat_history = []
    st.session_state.chat_engine.chat_history.clear()
    # Clear the screen by rerunning the app
    st.session_state.messages=[{"role": "assistant", "content": "Inizia una chat con i tuoi documenti!"}]

st.button('Reset Chat', on_click=reset_conversation)
