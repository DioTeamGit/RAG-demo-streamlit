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




col1, col2 = st.columns([5,1])
col1.title("Iniziamo!")
context= "Sei un avvocato. Devi usare sempre i documenti che hai a disposizione.\n" # contesto
         
st.sidebar.title("Personalizza le risposte")
selection = st.sidebar.multiselect(
    "Seleziona una o più collezioni di documenti:",
    ['CCNL e Sentenze cassazione', 'AI ACT e Data Governance Act']
)

# temperatura
temperature = st.sidebar.slider("Seleziona la temperatura della risposta", min_value=0.0, max_value=1.0, value=0.5, step=0.01, help= "La temperatura in un LLM regola la probabilità di scegliere parole o frasi durante la generazione di testo. Un valore di temperatura più alto rende il modello più propenso a fare scelte inaspettate o meno probabili, rendendo il testo più vario e talvolta più creativo. Al contrario, una temperatura bassa porta il modello a scegliere opzioni più sicure e prevedibili, risultando in risposte più coerenti e meno sorprendenti.")


# Settings

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")  

Settings.llm = OpenAI(model="gpt-4o", temperature=temperature)

# Formato
format = st.sidebar.radio("Seleziona formato della risposta", options=['Formato Libero','E-mail', 'Paragrafo', 'Lista'])

# Checkbox fonti
st.sidebar.write("Aggiungi le fonti alla risposta:")

fonti = st.sidebar.toggle("Cita le fonti")

#if fonti:
#    context = context + "Per ogni informazione cita sempre le fonti da cui hai preso questa informazione e mettile in grassetto."

# qui cerco di 


# Prompt preesitenti

if 'selected_query' not in st.session_state:
    st.session_state.selected_query = None

# Legal query buttons in Italian



st.write("Scegli un prompt")
#query_texts = {
#    "Termini del Contratto": "Spiega le considerazioni chiave per il seguente contratto nazionale",
#    "Diritti dei Dipendenti": "Descrivi i diritti dei dipendenti riguardo al pagamento degli straordinari.",
#    "Norme sul Licenziamento": "Riporta parola per parola ",
#    "Sicurezza sul Lavoro": "Riassumi le responsabilità del datore di lavoro per la sicurezza sul lavoro."
#}

query_texts = {
    "Parere legale sul licenziamento del dipendente": "Redigi un parere legale in merito alla legittimità del licenziamento disciplinare di un dipendente che ha violato il regolamento aziendale, includendo le prove necessarie e le procedure che l'azienda deve seguire in caso di impugnazione del provvedimento.",
    "Parere legale sul trattamento della maternità/paternità": "Redigi un parere legale sui diritti dei lavoratori durante il periodo di maternità o paternità, analizzando le disposizioni normative relative ai congedi, alla retribuzione e al mantenimento della posizione lavorativa.",
    "Parere legale sulla discriminazione sul lavoro": "Scrivi un parere legale in merito a un caso di presunta discriminazione sul lavoro basata su genere, includendo l'analisi delle normative vigenti e applicabili e le possibili azioni legali che il dipendente può intraprendere.",
    "Parere legale sugli straordinari non pagati": "Redigi un parere legale relativo a una situazione in cui un dipendente non ha ricevuto il pagamento per gli straordinari effettuati, esaminando le disposizioni normative e le possibili sanzioni per il datore di lavoro.",
    "Parere legale sulla privacy dei dipendenti": "Redigi un parere legale sui limiti del controllo dei dipendenti da parte del datore di lavoro, analizzando le normative sulla privacy, la normativa relativa all’utilizzo di sistemi di sorveglianza e il monitoraggio delle comunicazioni elettroniche relative all’ambiente di lavoro.",
    "Parere legale sul diritto di sciopero": "Scrivi un parere legale riguardante il diritto di sciopero dei lavoratori, includendo le procedure legali per indire uno sciopero, le tutele per i lavoratori che vi aderiscono e non e le possibili azioni legali del datore di lavoro in risposta allo sciopero."
  }


for key, value in query_texts.items():
    if st.button(key):
        st.session_state.selected_query = value

# Display the response in the main area if a query is selected

if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ciao, come posso esserti utile?"}
    ]
client = qdrant_client.QdrantClient('https://46e915dc-c126-4445-af6d-265c738b7848.us-east4-0.gcp.cloud.qdrant.io:6333', api_key=st.secrets["qdrant_key"])
vector_store_4 = QdrantVectorStore(client=client, collection_name="RAG_4")
index = VectorStoreIndex.from_vector_store(vector_store=vector_store_4)

print(index)



if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(chat_mode="openai", verbose=True)

#st.write(st.session_state.chat_engine)


prompt=st.chat_input("Fai una domanda")
#se seleziono il prompt dai buttons lo sovracrivo
if st.session_state.selected_query != None:
    prompt=st.session_state.selected_query
    st.session_state.selected_query = None

if prompt: # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content":  prompt})
    st.session_state_selected_query=None

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Sto elaborando una risposta..."):
            response = st.session_state.chat_engine.chat(prompt+"\n Utilizza come formato:"+ format , tool_choice="query_engine_tool") #query engine tool forza la ricerca
            #response = st.session_state.chat_engine.chat(prompt)
            sources = set([response.source_nodes[i].node.metadata["file_name"] for i in range(0,len(response.source_nodes))])
            if fonti:
                messaggio = response.response + "\nFonti:" + str(sources)
                message = {"role": "assistant", "content": messaggio}
            else:
                messaggio = response.response
                message = {"role": "assistant", "content": response.response}
            st.write(messaggio)
            st.write(response)
            st.write(response.source_nodes)
            st.write(response.source_nodes[0].text)
            st.session_state.messages.append(message) # Add response to message history




with col2:
# If last message is not from assistant, generate a new response
    def reset_conversation():
        # Reset chat history and any other relevant state variables
        st.session_state.chat_history = []
        st.session_state.chat_engine.chat_history.clear()
        # Clear the screen by rerunning the app
        st.session_state.messages=[{"role": "assistant", "content": "Ciao, come posso esserti utile?"}]

    st.button('⟳', on_click=reset_conversation, help="Premi per fare il reset della conversazione")
