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
import openai
import streamlit as st
from bs4 import BeautifulSoup
import requests
import pdfkit
import time
import os


client = openai
openai.api_key = st.secrets.openai_key_p
# Set your OpenAI Assistant ID here
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

# ASSISTANT_ID is stored in a .env file at local level and as a github secret at remote level
assistant_id = st.secrets.assistant_key
thread = client.beta.threads.create()

#st.write("thread id: ", thread.id)



st.set_page_config(page_title="Iniziamo!", page_icon=":speech_balloon:", layout="centered", initial_sidebar_state="auto", menu_items=None)

st.session_state.thread_id = thread.id




def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
    annotations = message_content.annotations if hasattr(message_content, 'annotations') else []

    st.write(annotations)
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')
        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            st.write(file_citation.file_id)
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            cited_file = {'filename': 'cited_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] {file_citation.file_id} from {cited_file["filename"]}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            # Placeholder for file download citation
            cited_file = {'filename': 'downloaded_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}')  # The download link should be replaced with the actual download path

    # Add footnotes to the end of the message content
    full_response = message_content.value + '\n\n' + '\n'.join(citations)
    return full_response


col1, col2 = st.columns([5,1])
col1.title("Iniziamo!")
context= "Sei un avvocato. Devi usare sempre i documenti che hai a disposizione.\n" # contesto
         
st.sidebar.title("Personalizza le risposte")

# temperatura
temperature = st.sidebar.slider("Seleziona la temperatura della risposta", min_value=0.0, max_value=1.0, value=0.5, step=0.01, help= "La temperatura in un LLM regola la probabilità di scegliere parole o frasi durante la generazione di testo. Un valore di temperatura più alto rende il modello più propenso a fare scelte inaspettate o meno probabili, rendendo il testo più vario e talvolta più creativo. Al contrario, una temperatura bassa porta il modello a scegliere opzioni più sicure e prevedibili, risultando in risposte più coerenti e meno sorprendenti.")


# Settings

#Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")  

Settings.llm = OpenAI(model="gpt-4o")

# Formato
format = st.sidebar.radio("Seleziona formato della risposta", options=['Formato Libero','E-mail', 'Paragrafo', 'Lista'])

# Checkbox fonti
st.sidebar.write("Aggiungi le fonti alla risposta:")

fonti = st.sidebar.toggle("Cita le fonti")

#if fonti:
#    context = context + "Per ogni informazione cita sempre le fonti da cui hai preso questa informazione e mettile in grassetto."

# qui cerco di 



# Legal query buttons in Italian



st.write("Scegli un prompt")
#query_texts = {
#    "Termini del Contratto": "Spiega le considerazioni chiave per il seguente contratto nazionale",
#    "Diritti dei Dipendenti": "Descrivi i diritti dei dipendenti riguardo al pagamento degli straordinari.",
#    "Norme sul Licenziamento": "Riporta parola per parola ",
#    "Sicurezza sul Lavoro": "Riassumi le responsabilità del datore di lavoro per la sicurezza sul lavoro."
#}

query_texts_fisgr = {"Controllo interno e funzioni specifiche": "Come viene gestito il controllo interno e quali sono le funzioni specifiche di Risk Management e Compliance?",
    "Selezione e monitoraggio outsourcer": "Quali sono i passaggi principali nella procedura di selezione e monitoraggio degli outsourcer di funzioni essenziali come descritto nel documento?",
    "Procedura gestione rischi operativi": "Spiega le procedure adottate per la gestione e la valutazione dei rischi operativi come delineato nel Manuale.",
    "Monitoraggio e revisione del Budget": "Descrivi il processo di monitoraggio e revisione del Budget annuale della Società.",
    "Gestione del personale": "Quali sono le linee guida e le responsabilità specificate per la gestione del personale, inclusi assunzioni e formazioni?"
}

query_texts_ccnl_cass = {
    "Riassunto punti chiave CCNL Sanità": "Riassumi punti chiave CCNL sanità",
    "Diritti dei Dipendenti": "Descrivi i diritti dei dipendenti riguardo al pagamento degli straordinari.",
    "Minimi tabellari CCNL commercio": "Riporta i minimi tabellari del CCNL commercio ",
    "Precedenti Giuridici cassazione": "Quali precedenti giuridici sono stati considerati dalla Cassazione nella sentenza di denigrazione su Facebook?",
    "Implicazioni legali contenuti denigratori":"Quali sono le implicazioni legali per un dipendente che pubblica contenuti denigratori su Facebook nei confronti del proprio datore di lavoro?",
    "Bilanciamento libertà di espressione dipendente e responsabilità": "Qual è il bilanciamento tra la libertà di espressione del dipendente e le responsabilità verso il datore di lavoro in un contesto lavorativo?"
}

query_texts = query_texts_ccnl_cass
for key, value in query_texts.items():
    if st.button(key):
        st.session_state.selected_query = value

# Display the response in the main area if a query is selected

if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ciao, come posso esserti utile?"}
    ]

#st.write(st.session_state.chat_engine)
if 'selected_query' not in st.session_state:
    st.session_state.selected_query = None

prompt=st.chat_input("Fai una domanda")
#se seleziono il prompt dai buttons lo sovracrivo
if st.session_state.selected_query != None:
    prompt=st.session_state.selected_query
    #st.write(st.session_state.selected_query)
    st.session_state.selected_query = None



if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"
if "messages" not in st.session_state:
        st.session_state.messages = []


if prompt: # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content":  prompt})

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Sto elaborando una risposta..."):
            client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
            )
            run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            instructions="Per favore, rispondi alle domande utilizzando le informazioni fornite nei file. Quando aggiungi altre informazioni, segnale chiaramente come tali, con un colore diverso. Con il seguente formato: "+format)
            while run.status != 'completed':
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

            # Retrieve messages added by the assistant
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )

            
            st.session_state.messages.append({"role": "user", "content":  prompt})
            st.session_state_selected_query=None

        # Add the user's message to the existing thread
            assistant_messages_for_run = [
                message for message in messages 
                if message.run_id == run.id and message.role == "assistant"
            ]
            for message in assistant_messages_for_run:
                full_response = process_message_with_citations(message)
                #full_response = message
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                with st.chat_message("assistant"):
                    st.markdown(full_response, unsafe_allow_html=True)

# Display existing messages in the chat
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])


with col2:
# If last message is not from assistant, generate a new response
    def reset_conversation():
        # Reset chat history and any other relevant state variables
        st.session_state.chat_history = []
        #st.session_state.chat_messag.chat_history.clear()
        # Clear the screen by rerunning the app
        st.session_state.messages=[{"role": "assistant", "content": "Ciao, come posso esserti utile?"}]

    st.button('⟳', on_click=reset_conversation, help="Premi per fare il reset della conversazione")
