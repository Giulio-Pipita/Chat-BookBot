import numpy as np
import os
import streamlit as st 
import tempfile
from time import sleep
#import locali
from blob_management import new_blob_index,add_blob_index,blob_reader, upload_blob_file
from indexer import index_document, loader, chopper, remove_faiss, add_document, delete_indexed_files
from images import extract_images, delete_image_index, create_image_index, text_image_query, check_if_images
from retriever import asking
from speech_transcription import audio_transcription

#streamlit run c:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\chatapp.py
def show_chatapp_page():
    i = 0
    j = 0
    documents = []
    end_documents = []
    file_names = []
    file_path_images = ""
    if "messages" not in st.session_state:
        st.session_state.messages =  []
    if "documents" not in st.session_state:
        st.session_state.documents = False
    if "files" not in st.session_state:
        st.session_state.files = []
    if "file_names" not in st.session_state:
        st.session_state.file_names = []
    if "image_index" not in st.session_state:
        st.session_state.image_index = False  
    if "images" not in st.session_state:
        st.session_state.images = check_if_images()
    if "filepath_to_image" not in st.session_state:
        st.session_state.filepath_to_image = ""

    with st.sidebar:
        st.write("DocumentBot")
        indicizzati = blob_reader()
        print(f"questi sono i documenti indicizzati: {indicizzati}")
        #se ci sono file indicizzati ne scrivo il nome e cambio lo stato di 'document' perchè sono già presenti documenti
        if indicizzati != " ":
            st.write("Questi sono i documenti caricati:")
            st.write(indicizzati)
            st.session_state.documents = True
        else:
            st.write("Non ci sono documenti indicizzati al momento")

        if st.session_state.documents == True:
            rimuovi = st.button("rimuovi le indicizzazioni correnti")
            if rimuovi:
                new_blob_index(" ")
                remove_faiss()
                delete_image_index()
                delete_indexed_files()
                st.session_state.documents = False
                st.rerun()
                
        
        
        
        files = st.file_uploader("Carica i tuoi file PDF", accept_multiple_files= True)
        images = st.checkbox("carica anche le immagini (super-beta)")
        indicizza = st.button("finisci indicizzazione")
        if not indicizza:
            for file_uploaded in files:
                    #inserisco il contenuto del file caricato in uno temporaneo. Perchè le mie funzioni accettano in input path ed è l'unico modo che ho trovato per otternerne uno
                    #tempdir = tempfile.mkdtemp()
                    #path = os.path.join(tempdir, file_uploaded.name)
                    path = os.path.join(r".\indexed_documents", file_uploaded.name)
                    filename = os.path.basename(path)[:-4]
                    st.session_state.filepath_to_image = path
                    if filename not in st.session_state.file_names:
                        with open(path, "wb")as f:
                            f.write(file_uploaded.getvalue())
                        if path.endswith(".mp3") or path.endswith(".wav"):
                            upload_blob_file(path)
                            audio_transcription(filename)
                            st.session_state.files.extend(loader(r".\audio_transcription.txt"))
                        else:
                            st.session_state.files.extend(loader(path))
                        print(f"documento caricato: {filename}\n")
                        st.session_state.file_names.append(filename)
                    else:
                        print(f"{filename}file già caricato")
                    i += 1
        if images:
            if st.session_state.documents == True or len(st.session_state.file_names) != 1:
                st.error("L'indicizzazione delle immagini può essere effettuata solo con un documento")
            else:
                st.success("Oh yeah")
                st.session_state.image_index = True
        
        if indicizza:
            if st.session_state.file_names:
                try:
                    if st.session_state.image_index == True:
                        print("inizio processo indicizzazione immagini")
                        create_image_index()
                        extract_images(st.session_state.filepath_to_image)
                    else:
                        print("non ci sono immagini da indicizzare \n")
                    if st.session_state.documents == True:
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
                        chopped = chopper(st.session_state.files)     
                        #index_document(st.session_state.files)
                        index_document(chopped)
                    st.success("il documento è stato indicizzato con successo, è possibile iniziare la chat")
                    sleep(5)
                    st.session_state.file_names = []
                    st.session_state.files = []
                    st.rerun()
                except Exception as e:
                    st.error(f"non è stato possibile indicizzare il documento a causa di: {e}. Verrà ricaricata la pagina in 5 secondi massimo")
                    sleep(5)
                    st.rerun()
            else:
                st.error("seleziona almeno un documento da caricare")



    
    prompt = st.chat_input("chiedi informazioni")
    if prompt:
        if st.session_state.documents == True:
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
                print(st.session_state.images)
                if st.session_state.images == True:
                    returned_image = text_image_query(prompt)
                    if returned_image:
                        with st.chat_message("assistant"):
                            st.image(returned_image, caption='immagine di risposta')    
                        st.session_state.messages.append({"role": "assistant", "content": returned_image})
        else:
            st.error("Devi caricare almeno un documento!!!")