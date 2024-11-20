import streamlit as st

from streamlit_oauth import OAuth2Component
from streamlit_cookies_controller import CookieController

DISABLE_LOGIN = True
st.session_state['DISABLE_LOGIN'] = DISABLE_LOGIN

st.set_page_config(
    page_title='Seja bem-vindo a CTC Digital!',
    page_icon = 'media/ctc.png',
    layout="wide"
)

paginas = [
    st.Page("pages/rag_news.py", title="Noticias", icon="🗞️"),
    st.Page("pages/rag_pdf.py" , title="PDF's", icon="📄"),
    st.Page("pages/settings.py", title="Configurações", icon="⚙️")
]

pagina_atual = st.navigation(paginas)
pagina_atual.run()

import login_google

import logging
logging.basicConfig(level=logging.INFO)

controller = CookieController()

with st.sidebar:
    st.session_state["login"] = login_google.login(controller)

    if ( st.session_state['login'] and ( "auth" in st.session_state ) ) or DISABLE_LOGIN:
        st.success('Página carregada!')

#if 'login' in st.session_state:
    #if ( st.session_state['login'] and ( "auth" in st.session_state ) ) or DISABLE_LOGIN:
        #col1, col2 = st.columns(2)

        #col1.write('Ajuda?')
        #col2.write('Notícias!')

        #with col1:
            #st.write("Ajuda?")

        #with col2:
            #st.write("Notícias!")