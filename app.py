import streamlit as st
from ai_backend import process_input

st.title("RACCOON Documentation Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if input_message := st.chat_input("Ask me anything about RACCOON..."):
    # Save + display user message
    st.chat_message("user").markdown(input_message)
    st.session_state.messages.append({"role": "user", "content": input_message})

    # Get assistant response from rag_chain
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_box = st.empty()
            streamed_response = ""

            for chunk in process_input(input_message):
                streamed_response += chunk
                response_box.markdown(streamed_response)

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": streamed_response})