import streamlit as st
from chatapp import show_chatapp_page
from bookbot import show_bookbot_page
#streamlit run c:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\main.py
if "show_buttons" not in st.session_state:
    st.session_state.show_buttons  = True
if "show_chatapp" not in st.session_state:
    st.session_state.show_chatapp = False
if "show_bookbot" not in st.session_state:
    st.session_state.show_bookbot = True

if st.session_state.show_buttons == True:
    
    chat_app_btn = st.button("Chatta con i tuoi documenti")
    book_bot_btn = st.button("Crea schede libro")
    if chat_app_btn:
        st.session_state.show_buttons = False   
        st.session_state.show_chatapp = True     
        st.rerun()
        
    if book_bot_btn:
        st.session_state.show_buttons = False
        st.session_state.show_bookbot = True
        st.rerun()

if st.session_state.show_chatapp == True:
    show_chatapp_page()
if st.session_state.show_bookbot == True:
    show_bookbot_page()
        
        