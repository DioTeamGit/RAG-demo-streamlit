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

# Set your OpenAI Assistant ID here
assistant_id = 'asst_dy1sG6anYf0hvZzE7HFf4OcL'




st.set_page_config(page_title="Iniziamo!", page_icon=":speech_balloon:", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = st.secrets.openai_key_p

def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
    annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            cited_file = {'filename': 'cited_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}')
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

#st.write(st.session_state.chat_engine)


prompt=st.chat_input("Fai una domanda")
#se seleziono il prompt dai buttons lo sovracrivo
if st.session_state.selected_query != None:
    prompt=st.session_state.selected_query
    st.session_state.selected_query = None

if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Display existing messages in the chat
for message in st.session_state.messages:
with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Chat input for the user
if prompt := st.chat_input("Fai una domanda"):
# Add user message to the state and display it
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
      st.markdown(prompt)

# Add the user's message to the existing thread
client.beta.threads.messages.create(
    thread_id=st.session_state.thread_id,
    role="user",
    content=prompt
)

# Create a run with additional instructions
run = client.beta.threads.runs.create(
    thread_id=st.session_state.thread_id,
    assistant_id=assistant_id,
    instructions="Please answer the queries using the knowledge provided in the files.When adding other information mark it clearly as such.with a different color"
)

# Poll for the run to complete and retrieve the assistant's messages
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

# Process and display assistant messages
assistant_messages_for_run = [
    message for message in messages 
    if message.run_id == run.id and message.role == "assistant"
]
for message in assistant_messages_for_run:
    full_response = process_message_with_citations(message)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    with st.chat_message("assistant"):
        st.markdown(full_response, unsafe_allow_html=True)



with col2:
# If last message is not from assistant, generate a new response
    def reset_conversation():
        # Reset chat history and any other relevant state variables
        st.session_state.chat_history = []
        st.session_state.chat_engine.chat_history.clear()
        # Clear the screen by rerunning the app
        st.session_state.messages=[{"role": "assistant", "content": "Ciao, come posso esserti utile?"}]

    st.button('⟳', on_click=reset_conversation, help="Premi per fare il reset della conversazione")
