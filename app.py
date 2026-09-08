"""Chat-style Streamlit user interface."""

import logging

import streamlit as st

from agents import process_query

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Cybersecurity Assistant",
    page_icon="🛡️",
    layout="centered",
)

st.title("🛡️ Cybersecurity Assistant")
st.caption(
    "Ask a cybersecurity question or describe a short cybersecurity incident."
)

# Store messages while the current Streamlit session remains open.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Keep the question box at the top of the page.
with st.form("question_form", clear_on_submit=True):
    query = st.text_area(
        "Your question or incident",
        placeholder=(
            "For example: What is broken access control?\n\n"
            "Or describe a suspicious cybersecurity incident."
        ),
        height=130,
    )

    answer_clicked = st.form_submit_button(
        "Answer",
        type="primary",
        use_container_width=True,
    )

# Process the submitted question.
if answer_clicked:
    cleaned_query = query.strip()

    if not cleaned_query:
        st.warning(
            "Please enter a cybersecurity question or incident description."
        )
    else:
        # Save the user's question.
        st.session_state.messages.append(
            {
                "role": "user",
                "content": cleaned_query,
            }
        )

        try:
            with st.spinner("Preparing an answer..."):
                result = process_query(cleaned_query)

            # Save the assistant's answer immediately after the question.
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["response"],
                }
            )

        except Exception:
            logger.exception(
                "Failed to process the cybersecurity query"
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "The request could not be processed. "
                        "Check the setup and try again."
                    ),
                }
            )

# Separate the form from the conversation history.
if st.session_state.messages:
    st.divider()

# Group each question with its corresponding answer.
conversation_pairs = [
    st.session_state.messages[index:index + 2]
    for index in range(0, len(st.session_state.messages), 2)
]

# Display the newest conversation first while keeping each question
# above its corresponding answer.
for conversation in reversed(conversation_pairs):
    for message in conversation:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])