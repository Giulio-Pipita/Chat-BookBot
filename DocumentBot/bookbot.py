import base64
import os
import streamlit as st
import pandas as pd
import tempfile
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from langchain.callbacks import get_openai_callback
from langchain.document_loaders import PyPDFLoader
#from PyPDF2 import PdfReader
from streamlit_extras.add_vertical_space import add_vertical_space
from time import sleep

from asker import ask_summary
from indexer import remove_faiss, ePub_to_Pdf, loader, chopper, index_document, index_for_summary
from retriever import asking


def show_bookbot_page():
    domande = []
    document = []
    analysis  = []
    progress_value = 0
    returned_analysis = ""  
    title_container = st.container()
    with title_container:
        st.header("BookBot")
    with st.sidebar:
        if "chat_ready" not in st.session_state:
            st.session_state.chat_ready = False
        if "get_analysis" not in st.session_state:
            st.session_state.get_analysis = True
        if "progress_bar" not in st.session_state:
            st.session_state.progress_bar = True
        file = st.file_uploader("Carica un fle ePub", accept_multiple_files=False)
        if st.session_state.chat_ready == False:
            if file:
                #progress bar
                try:
                    remove_faiss()
                except:
                    print("non c'è nessun indice")
                print("faiss rimosso")
                tempdir = tempfile.mkdtemp()
                path = os.path.join(tempdir, file.name)
                with open(path, "wb") as f:
                    f.write(file.getvalue())
                print("file riscritto")
                path_to_pdf = ePub_to_Pdf(path)
                #path_to_pdf = f".\epub_to_pdf\{file.name[:-4]}pdf"
                document.extend(loader(path_to_pdf))
                chunks = chopper(document)
                index_document(chunks)
                index_for_summary(chunks)

                if(progress_value == 1):
                    st.write(f"Indicizzazione di {file.name[:-5]} completata!!!")
                    st.session_state.progress_bar = False
                st.session_state.chat_ready = False
                st.session_state.get_analysis = True

    st.write("Analizzerò i libri per te!")
    query = st.chat_input("Fai domande sul tuo file pdf")

    if st.session_state.get_analysis == True:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        with open (r".\epub_to_pdf\riassunto_lungo.txt", "r", encoding = 'utf-8') as summary:
            riassunto = summary.read()
        with st.chat_message("assistant"):
                st.markdown(riassunto)
        st.session_state.messages.append({"role": "assistant", "content": riassunto})
        filenames = os.listdir(".\epub_to_pdf")
        for filename in filenames:
            if filename.endswith(".pdf"):
                    file = filename[:-4]

        autore = asking(f"voglio sapere chi è l'autore di {file}")
        with open(r".\epub_to_pdf\riassunto_corto.txt", "r", encoding = 'utf-8') as riass:
            trama = riass.read()       
        piani_narrativi = ask_summary("I piani narrativi sono una parte importante della struttura di un romanzo. Essi si riferiscono ai diversi livelli di narrazione che un autore può utilizzare per raccontare la storia.I piani narrativi includono la fabula e l'intreccio, i piani temporali della narrazione, lo stile e i personaggi, identificali in questo testo")
        tematiche = ask_summary("voglio sapere le tematiche di questo libro")
        comprensione = ask_summary("questo testo può essere di difficile comprensione?")
        stile = ask_summary("come è utilizzata la punteggiature? il testo è ricco di aggettivi, similitudini o metafore? è formale, informale o simile al parlato? ci sono molti dialoghi o descrizioni?")
        coerenza = ask_summary("Ci cono evidenti incoerenze in questo libro? ")


        data = {'Attributi':['Autore', 'Trama', 'Piani Narrativi', 'Tematiche', 'Comprensione', 'Stile', 'Coerenza'],
                'Valore' : [autore, trama, piani_narrativi, tematiche, comprensione, stile, coerenza]}
        scheda_libro = pd.DataFrame(data)
        scheda_libro.set_index('Attributi', inplace=True)
        table_markdown = scheda_libro.to_markdown()



        
        st.write(table_markdown, unsafe_allow_html=True)


        directory = st.text_input("Inserisci il percorso della directory di salvataggio:")
        save_table = st.button(label="Salva la scheda su un file di testo") 
        save_summary = st.button(label = "Salva il riassunto")
        if save_table:
            if directory:
                schema_file_name = f"scheda di {file}"
                schema_file_path = os.path.join(directory, f"{schema_file_name}.txt")
                with open(schema_file_path, 'w')as f1:
                    f1.write(table_markdown)
                st.write()
            else:
                st.write("Inserisci un percorso valido per la directory di salvataggio!!!")
        if save_summary:
            if directory:
                summary_file_name = f"riassunto di {file}"
                summary_file_path = os.path.join(directory, f"{summary_file_name}.txt")
                with open(summary_file_path, "w")as f2:
                    f2.write(riassunto)

    if query:
        if(st.session_state.chat_ready == True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            with st.chat_message("user"):
                st.markdown(query)      
            st.session_state.messages.append({"role": "user", "content": query})
            answer = asking(query)
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})