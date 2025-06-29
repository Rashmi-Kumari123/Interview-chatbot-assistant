from groq import Groq
import streamlit as st

# Initialize Groq client
if 'GROQ_API_KEY' in st.secrets:
    api_key = st.secrets['GROQ_API_KEY']
else:
    st.sidebar.error("Please add your GROQ_API_KEY in secrets.toml")
    st.stop()

client = Groq(api_key=api_key)

# Sidebar for role selection
with st.sidebar:
    st.title('🤖Interview Preparation Chatbot')
    role = st.selectbox(
        'Select your interview role:',
        ['Select', 'Software Engineer', 'Frontend Developer', 'Backend Developer', 'ML Engineer']
    )
    if role == 'Select':
        st.warning("Please select a role to begin.", icon="⚠️")

# Initialize chat session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Start with a role-specific greeting and question if no prior messages
if role != 'Select' and not st.session_state.messages:
    domain_prompt = f"""
    You are an expert interviewer for the {role} role. 
    Start the conversation by asking a relevant technical question for this domain.
    Keep it clear and concise.
    """
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "system", "content": domain_prompt}]
    )
    first_question = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": first_question})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input prompt
if prompt := st.chat_input("Your response here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Create prompt for feedback and improvement based on user's answer
        feedback_prompt = f"""
        You are an expert {role} interviewer. The candidate answered: "{prompt}".
        - First, provide direct feedback on their answer.
        - Then, provide an improved version of their answer if necessary.
        - Finally, ask the next question for the {role} interview.
        Structure your response clearly with headings: Feedback, Improved Answer, Next Question.
        """

        response_stream = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": feedback_prompt}
            ],
            stream=True
        )

        for chunk in response_stream:
            full_response += chunk.choices[0].delta.content or ""
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
