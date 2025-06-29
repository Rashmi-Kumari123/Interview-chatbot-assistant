import streamlit as st
from supabase import create_client, Client
from groq import Groq

def get_conn():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    return supabase

def get__groq_cred():
    if 'GROQ_API_KEY' in st.secrets:
        api_key = st.secrets['GROQ_API_KEY']
    else:
        st.sidebar.error("Please add your GROQ_API_KEY in secrets.toml")
        st.stop()
    client = Groq(api_key=api_key)
    
    return client