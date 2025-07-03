import db_connection
import db_connection.connection
import streamlit as st
supabase = db_connection.connection.get_conn()
client = db_connection.connection.get__groq_cred()


def store_conversation(user_id, domain, question, answer):
    data = {
        "user_id": user_id,
        "domain": domain,
        "question": question,
        "answer": answer
    }
    supabase.table("interview_conversations").insert(data).execute()
    

def get_conversations_by_domain(user_id, domain):
    response = supabase.table("interview_conversations") \
                       .select("*") \
                       .eq("user_id", user_id) \
                       .eq("domain", domain) \
                       .order("created_at", desc=False) \
                       .execute()
    return response.data

def delete_conversation_by_id(convo_id):
    try:
        supabase.table("interview_conversations").delete().eq("id", convo_id).execute()
        return True
    except Exception as e:
        print(f"Delete failed: {e}")
        return False




