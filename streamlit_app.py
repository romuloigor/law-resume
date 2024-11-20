import streamlit as st

st.set_page_config(
    page_title='Seja bem-vindo a CTC Digital!',
    page_icon = 'media/ctc.png',
    layout="wide",
    initial_sidebar_state='collapsed',
    menu_items={
        'Get Help': 'mailto:romulo.conceicao@ctctech.com.br',
        'Report a Bug': "https://github.com/romuloigor/law-resume/issues",
        'About': "#INOVA.ai"
    }
)

from streamlit_oauth import OAuth2Component
from streamlit_cookies_controller import CookieController

import login_google

import logging
logging.basicConfig(level=logging.INFO)

controller = CookieController()

DISABLE_LOGIN = True
st.session_state['DISABLE_LOGIN'] = DISABLE_LOGIN

paginas = [
    st.Page("pages/rag_news.py", title="Noticias", icon="🗞️"),
    st.Page("pages/rag_pdf.py" , title="Documentos", icon="📄"),
    st.Page("pages/settings.py", title="Configurações", icon="⚙️")
]

pagina_atual = st.navigation(paginas)
pagina_atual.run()

with st.sidebar:
    st.session_state["login"] = login_google.login(controller)