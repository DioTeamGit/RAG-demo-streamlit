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
import datetime

def reset_conversation():
    # Reset chat history and any other relevant state variables
    st.session_state.chat_history = []
    st.session_state.chat_engine.chat_history.clear()
    # Clear the screen by rerunning the app
    st.session_state.messages=[{"role": "assistant", "content": "Ciao, come posso esserti utile?"}]

def handle_changes():
    reset_conversation()
    vector_store_4 = QdrantVectorStore(client=client, collection_name=selection_dict[selection])
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store_4)
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="openai", verbose=True)


st.set_page_config(page_title="Iniziamo!", page_icon="⚖️", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = st.secrets.openai_key_p




col1, col2 = st.columns([5,1])
col1.title("Iniziamo!")

# context da selezionare in base alla demo che serve 


context= "Sei un avvocato. Devi usare sempre i documenti che hai a disposizione.\n" # contesto

#context = "Sei un esperto in procedure aziendali. Devi usare sempre il manuale delle procedure per rispondere alle domande che ti vengono fatte"
         
st.sidebar.title("Personalizza le risposte")
selection = st.sidebar.selectbox(
    "Seleziona una collezione di documenti:",
    ['CCNL e Sentenze cassazione', 
     'AI ACT e Data Governance Act', 
    # 'FISGR'
    ]
)

selection_dict = { 'CCNL e Sentenze cassazione':"RAG_4",
                  'AI ACT e Data Governance Act': "ai_act&data_governance_act"}
st.sidebar.button('Aggiorna documenti', on_click=handle_changes, help="Aggiorna la collezione di documenti su cui fare la ricerca")

# st.write(selection_dict[selection])
# temperatura
temperature = st.sidebar.slider("Seleziona la temperatura della risposta", min_value=0.0, max_value=1.0, value=0.5, step=0.01, 
                                help= "Selezionando temperatura = 0, il modello genera risposte prevedibili e deterministiche, mentre Con temperatura = 1, le risposte sono più diverse e creative.")


# Settings

#Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")  

Settings.llm = OpenAI(model="gpt-4o", temperature=temperature)

# Formato
format = st.sidebar.radio("Seleziona formato della risposta", options=['Formato Libero','E-mail', 'Paragrafo', 'Lista'])

# Checkbox fonti
st.sidebar.write("Aggiungi le fonti alla risposta:")

fonti = st.sidebar.toggle("Cita le fonti", value=True)

#if fonti:
#    context = context + "Per ogni informazione cita sempre le fonti da cui hai preso questa informazione e mettile in grassetto."

# qui cerco di 


# Prompt preesitenti

if 'selected_query' not in st.session_state:
    st.session_state.selected_query = None

# Legal query buttons in Italian

today = datetime.datetime.now()
this_year = today.year
jan_1 = datetime.date(this_year, 1, 1)
dec_31 = datetime.date(this_year, 12, 31)

d = st.sidebar.date_input(
    "Seleziona l'intervallo di date in cui vuoi fare ricerca",
    (jan_1, datetime.date(this_year, 1, 7)),
    jan_1,
    dec_31,
    format="MM.DD.YYYY",
)

st.write("Scegli un prompt")
query_texts_ccnl_cass = {
    "Termini del CCNL Sanità": "Spiega le considerazioni chiave per il seguente contratto nazionale sanità",
    "Diritti dei Dipendenti": "Descrivi i diritti dei dipendenti riguardo al pagamento degli straordinari.",
    "Minimi tabellari ccnl commercio": "Riporta i minimi tabellari del CCNL commercio ",
    "Precedenti Giuridici cassazione": "Quali precedenti giuridici sono stati considerati dalla Cassazione nella sentenza di denigrazione su Facebook?",
    "Implicazioni legali contenuti denigratori":"Quali sono le implicazioni legali per un dipendente che pubblica contenuti denigratori su Facebook nei confronti del proprio datore di lavoro?",
    "Bilanciamento libertà di espressione dipendente e responsabilità": "Qual è il bilanciamento tra la libertà di espressione del dipendente e le responsabilità verso il datore di lavoro in un contesto lavorativo?"
}

# da scegliere in base a interlocutore

query_texts_mic = {
    "Parere legale sul licenziamento del dipendente": "Redigi un parere legale in merito alla legittimità del licenziamento disciplinare di un dipendente che ha violato il regolamento aziendale, includendo le prove necessarie e le procedure che l'azienda deve seguire in caso di impugnazione del provvedimento.",
    "Parere legale sul trattamento della maternità/paternità": "Redigi un parere legale sui diritti dei lavoratori durante il periodo di maternità o paternità, analizzando le disposizioni normative relative ai congedi, alla retribuzione e al mantenimento della posizione lavorativa.",
    "Parere legale sulla discriminazione sul lavoro": "Scrivi un parere legale in merito a un caso di presunta discriminazione sul lavoro basata su genere, includendo l'analisi delle normative vigenti e applicabili e le possibili azioni legali che il dipendente può intraprendere.",
    "Parere legale sugli straordinari non pagati": "Redigi un parere legale relativo a una situazione in cui un dipendente non ha ricevuto il pagamento per gli straordinari effettuati, esaminando le disposizioni normative e le possibili sanzioni per il datore di lavoro.",
    "Parere legale sulla privacy dei dipendenti": "Redigi un parere legale sui limiti del controllo dei dipendenti da parte del datore di lavoro, analizzando le normative sulla privacy, la normativa relativa all’utilizzo di sistemi di sorveglianza e il monitoraggio delle comunicazioni elettroniche relative all’ambiente di lavoro.",
    "Parere legale sul diritto di sciopero": "Scrivi un parere legale riguardante il diritto di sciopero dei lavoratori, includendo le procedure legali per indire uno sciopero, le tutele per i lavoratori che vi aderiscono e non e le possibili azioni legali del datore di lavoro in risposta allo sciopero."
  }

query_texts_fisgr = {"Controllo interno e funzioni specifiche": "Come viene gestito il controllo interno e quali sono le funzioni specifiche di Risk Management e Compliance?",
    "Selezione e monitoraggio outsourcer": "Quali sono i passaggi principali nella procedura di selezione e monitoraggio degli outsourcer di funzioni essenziali come descritto nel documento?",
    "Procedura gestione rischi operativi": "Spiega le procedure adottate per la gestione e la valutazione dei rischi operativi come delineato nel Manuale.",
    "Monitoraggio e revisione del Budget": "Descrivi il processo di monitoraggio e revisione del Budget annuale della Società.",
    "Gestione del personale": "Quali sono le linee guida e le responsabilità specificate per la gestione del personale, inclusi assunzioni e formazioni?"
}

query_texts_dgai = {
    "Panoramica AI Act": "Scrivi un articolo approfondito che fornisca una panoramica del AI Act dell'Unione Europea. Includi gli obiettivi principali, le disposizioni maggiori e i potenziali impatti su imprese e consumatori. Discuti come classifica i sistemi di IA in base al rischio e i requisiti di conformità per i sistemi di IA ad alto rischio.",
    "Spiegazione Data Governance Act": "Spiega lo scopo e i componenti chiave del Data Governance Act. Descrivi come mira a migliorare la condivisione dei dati attraverso l'UE, le sue disposizioni per l'altruismo dei dati e l'istituzione di un quadro di governance dei dati. Dettaglia i ruoli e le responsabilità degli intermediari dei dati.",
    "Confronto tra AI Act e GDPR": "Confronta e contrappone l'AI Act con il Regolamento Generale sulla Protezione dei Dati (GDPR). Concentrati sui loro approcci normativi, ambito di applicazione e i tipi di protezioni fornite da ciascuno. Discuti come le imprese operanti nell'UE dovranno adeguare le loro pratiche per conformarsi a entrambe le normative.",
    "Impatto del Data Governance Act sul Settore Pubblico": "Analizza l'impatto del Data Governance Act sul settore pubblico. Discuti come promuove la condivisione dei dati del settore pubblico all'interno dell'UE, i benefici per l'amministrazione pubblica e i servizi, e le sfide e considerazioni nell'implementazione di queste disposizioni."
}


query_texts_dict = {"FISGR":query_texts_fisgr, "CCNL e Sentenze cassazione":query_texts_ccnl_cass, "AI ACT e Data Governance Act":query_texts_dgai}

query_texts= query_texts_dict[selection]
for key, value in query_texts.items():
    if st.button(key):
        st.session_state.selected_query = value

# Display the response in the main area if a query is selected

if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ciao, come posso esserti utile?"}
    ]
client = qdrant_client.QdrantClient('https://46e915dc-c126-4445-af6d-265c738b7848.us-east4-0.gcp.cloud.qdrant.io:6333', api_key=st.secrets["qdrant_key"])
vector_store_4 = QdrantVectorStore(client=client, collection_name=selection_dict[selection])
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
