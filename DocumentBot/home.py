import numpy as np
import os
import streamlit as st 
import tempfile

#import locali
from indexer import index_document, loader, remove_faiss, add_document
from blob_management import new_blob_index,add_blob_index,blob_reader, upload_blob_file
from retriever import asking
from speech_transcription import audio_transcription

#streamlit run c:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\home.py
i = 0
j = 0
documents = []
end_documents = []
file_names = []
if "messages" not in st.session_state:
    st.session_state.messages =  []
if "old_document" not in st.session_state:
    st.session_state.old_document = False
if "new_document" not in st.session_state:
    st.session_state.new_document = False
if "files" not in st.session_state:
    st.session_state.files = []
if "file_names" not in st.session_state:
    st.session_state.file_names = []
with st.sidebar:
    st.write("DocumentBot")
    indicizzati = blob_reader()
    print(f"questi sono i documenti indicizzati: {indicizzati}")
    #se ci sono file indicizzati ne scrivo il nome e cambio lo stato di 'document' perchè sono già presenti documenti
    if indicizzati != " ":
        st.write("Questi sono i documenti caricati:")
        st.write(indicizzati)
        st.session_state.old_document = True
    else:
        st.write("Non ci sono documenti indicizzati al momento")

    if st.session_state.old_document == True or st.session_state.new_document == True:
        rimuovi = st.button("rimuovi le indicizzazioni correnti")
        if rimuovi:
            new_blob_index(" ")
            remove_faiss()
            st.session_state.old_document = False
            st.session_state.new_document = False
    
    
    if st.session_state.new_document == False:
        files = st.file_uploader("Carica i tuoi file PDF", accept_multiple_files= True)
        indicizza = st.button(label = "finisci indicizzazione")
        if not indicizza:
            for file_uploaded in files:
                    #inserisco il contenuto del file caricato in uno temporaneo. Perchè le mie funzioni accettano in input path ed è l'unico modo che ho trovato per otternerne uno
                    tempdir = tempfile.mkdtemp()
                    path = os.path.join(tempdir, file_uploaded.name)
                    with open(path, "wb")as f:
                        f.write(file_uploaded.getvalue())
                    filename = os.path.basename(path)[:-4]
                    if path.endswith(".mp3") or path.endswith(".wav"):
                        upload_blob_file(path)
                        audio_transcription(filename)
                        st.session_state.files.extend(loader(r".\audio_transcription.txt"))
                    else:
                        st.session_state.files.extend(loader(path))
                    print("documento caricato: \n")
                    st.session_state.file_names.append(filename)
                    i += 1

    
    if indicizza:
        try:
            st.session_state.new_document = True
            if st.session_state.old_document == True:
                add_document(st.session_state.files)
                for name in st.session_state.file_names:
                    print(f"questo è il nome del file: {name}")
                    add_blob_index(name)
            else:
                for name in st.session_state.file_names:
                    if j == 0:
                        new_blob_index(name)
                        print(f"questo è il nome del file: {name}") 
                        j+=1
                    else:
                        add_blob_index(name)     
                index_document(st.session_state.files)
            st.success("il documento è stato indicizzato con successo, è possibile iniziare la chat")
        except Exception as e:
            st.error(f"non è stato possibile indicizzare il documento a causa di: {e}. Ricarica la pagina")




prompt = st.chat_input("chiedi informazioni")
if prompt:
    if st.session_state.old_document == True or st.session_state.new_document == True:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            answer = asking(prompt)
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.error("Devi caricare almeno un documento!!!")