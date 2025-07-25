import streamlit as st
import db_connection
import db_connection.connection
import chat_history.chat

# Initialize chat history session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Function to add message to history
def add_message(sender, message):
    st.session_state.history.append((sender, message))

supabase = db_connection.connection.get_conn()
client = db_connection.connection.get__groq_cred()

if "user" not in st.session_state:
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    def toggle_mode():
        if st.session_state.auth_mode == "login":
            st.session_state.auth_mode = "signup"
        else:
            st.session_state.auth_mode = "login"

    # Show Switch button only if user is not logged in
    st.sidebar.button(
        "Switch to Signup" if st.session_state.auth_mode == "login" else "Switch to Login",
        on_click=toggle_mode
    )

# Signup Screen
if st.session_state.auth_mode == "signup" and "user" not in st.session_state:
    st.title("🔑 Signup")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        if email and password:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.write(res)  # Debug output
            if res.user:
                st.success("Account created. ")

                user_id = res.user.id
                if user_id:
                    try:
                        data = supabase.table('users').insert({
                            "id": user_id,
                            "email": email
                        }).execute()
                        st.info(f"Inserted user to DB: {data}")
                    except Exception as e:
                        st.warning(f"Signup succeeded but user insert failed: {e}")
                else:
                    st.warning("User ID not returned. Email confirmation pending?")

                st.session_state.auth_mode = "login"
        else:
            st.warning("Please enter email and password")

# Login Screen
elif st.session_state.auth_mode == "login" and "user" not in st.session_state:
    st.title("🔒 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email and password:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.write(res)  # Debug output
            if res.user:
                st.session_state.user = res.user
                st.success(f"Welcome {email} 👋")
                st.rerun()  # Refresh app to load chat screen immediately
            else:
                st.error("Invalid credentials")
        else:
            st.warning("Please enter email and password")

# Chat Screen (Only visible after login)
elif "user" in st.session_state:
    # Sidebar layout
    with st.sidebar:
        # Logout Button
        if st.button("Logout"):
            st.session_state.pop("user")
            st.rerun()

        st.write(f"Welcome {st.session_state.user.email}")

        # Interview Preparation Chatbot section
        st.title('🤖 Interview Preparation Chatbot')
        role = st.selectbox(
            'Select your interview role:',
            ['Select', 'Software Engineer', 'Frontend Developer', 'Backend Developer', 'ML Engineer']
        )
        if role == 'Select':
            st.warning("Please select a role to begin.", icon="⚠️")
        if 'previous_role' not in st.session_state:
            st.session_state.previous_role = role

        if role != st.session_state.previous_role:
            st.session_state.previous_role = role
            st.session_state.messages = []
            st.session_state.history = []
            st.rerun()

        # ✅ Chat History at bottom
        if st.button("Show Chat History"):
            if "messages" in st.session_state and st.session_state.messages:
                st.subheader("💬 Current Session Chat History")
                for msg in st.session_state.messages:
                    sender = "You" if msg["role"] == "user" else "Bot"
                    st.markdown(f"**{sender}:** {msg['content']}")
            else:
                st.info("No chat history in this session yet.")


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
        add_message("Bot", first_question)  # ✅ Add bot message to history
        chat_history.chat.store_conversation(st.session_state.user.id, role, first_question, "")

    # Display main chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input prompt
    if prompt := st.chat_input("Your response here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        add_message("You", prompt)  # ✅ Add user message to history
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
        add_message("Bot", full_response)  # ✅ Add bot message to history
        chat_history.chat.store_conversation(
            st.session_state.user.id, role,
            st.session_state.messages[-2]["content"], prompt
        )
