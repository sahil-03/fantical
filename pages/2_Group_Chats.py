import streamlit as st 
import time
from typing import List
from typing import Dict
from router import MessageRouter
from Homepage import toggle_form
from Homepage import get_bot_avatar
from Homepage import USER_AVATAR_KEY
from Homepage import BOT_PERSONALITIES_KEY
from Homepage import BOT_OPTIONS_KEY

GROUP_CHATS_KEY = "group_chats"
GROUP_CHAT_MEMBERS_KEY = "group_chat_members"
GROUP_CHAT_ROUTER_KEY = "group_chat_router"
GROUP_CHAT_TOPIC_KEY = "group_chat_topic"

if 'group_chat_messages' not in st.session_state: 
    st.session_state.group_chat_messages = {} # Dict[str, List[Dict[str, str]]] 

if 'show_new_group_form' not in st.session_state: 
    st.session_state.show_new_group_form = False

if 'group_config' not in st.session_state: 
    st.session_state.group_config = {
        GROUP_CHATS_KEY: [], 
        GROUP_CHAT_MEMBERS_KEY: {},
        GROUP_CHAT_ROUTER_KEY: {},
        GROUP_CHAT_TOPIC_KEY: "",
    }

if 'last_message_timestamp' not in st.session_state:
    # Supposed to be used to do bot-to-bot replies, but doesn't work as intended under the streamlit framework 
    st.session_state.last_message_timestamp = -1

def add_new_group_chat(group_name: str, group_members: List[str], group_topic: str) -> None:
    assert group_name != "" and not group_name.isspace(), "Group name must be given"
    assert len(group_members) > 1, "There must be at least 3 members in a group (including you)."

    mr = MessageRouter(group_members, st.session_state.api_key_given)
    st.session_state.group_config[GROUP_CHATS_KEY].append(group_name)
    st.session_state.group_config[GROUP_CHAT_MEMBERS_KEY].update({group_name: group_members})
    st.session_state.group_config[GROUP_CHAT_ROUTER_KEY].update({group_name: mr})
    st.session_state.group_config[GROUP_CHAT_TOPIC_KEY] = group_topic
    st.session_state.group_chat_messages[group_name] = [] 

    # Add bot personalities as embeddings into the group's MessageRouter
    for member in group_members: 
        mr.add_embedding(member, st.session_state.bot_config[BOT_PERSONALITIES_KEY][member])

def format_messages(group_chat_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    formatted_messages = []
    for message in group_chat_messages: 
        formatted_messages.append({"role": message["role"], "content": message["content"]})
    return formatted_messages

def time_since_last_message() -> float: 
    return time.time() - st.session_state.last_message_timestamp

def toggle_form(form: str) -> None: 
    st.session_state[form] = not st.session_state[form]


st.title("🦄 Group Chats")

# Sidebar (with form(s) for creating new group chats) 
st.sidebar.title("⛺️ Fantical Rooms")

st.sidebar.button("➕ Create group", on_click=toggle_form, args=('show_new_group_form',))
if st.session_state.show_new_group_form: 
    with st.sidebar.form("create_new_group_chat_form"):
        st.header("Create group chat")
        
        group_name = st.text_input(label="Name your group", placeholder="Cool group!")
        group_members = st.multiselect('Choose your bots', st.session_state.bot_config[BOT_OPTIONS_KEY])
        group_topic = st.text_area('Enter a group topic', placeholder='This group is fun!')

        if st.form_submit_button("✅"):
            add_new_group_chat(group_name, group_members, group_topic)
            

# Select group chat
group_chat = st.sidebar.selectbox("Select a group chat", options=st.session_state.group_config[GROUP_CHATS_KEY])

if st.session_state.api_key_given:
    # Display and process chat message
    if group_chat in st.session_state.group_chat_messages:
        for message in st.session_state.group_chat_messages[group_chat]: 
            message_role = message["role"]
            avatar = st.session_state.user_config[USER_AVATAR_KEY] if message_role == 'user' else get_bot_avatar(message["name"])
            with st.chat_message(message_role, avatar=avatar):
                st.write(message["content"])

        if prompt := st.chat_input():
            st.session_state.group_chat_messages[group_chat].append({"role": "user", "name": "user", "content": prompt})
            with st.chat_message("user", avatar=st.session_state.user_config[USER_AVATAR_KEY]):
                st.write(prompt)
            st.session_state.last_message_timestamp = time.time()

        if len(st.session_state.group_chat_messages[group_chat]) > 0:
            if st.session_state.group_chat_messages[group_chat][-1]["role"] != "assistant":
                sender, message = st.session_state.group_chat_messages[group_chat][-1]["name"], st.session_state.group_chat_messages[group_chat][-1]["content"] 
                bot = st.session_state.group_config[GROUP_CHAT_ROUTER_KEY][group_chat].message_router(sender, message)
                with st.chat_message("assistant", avatar=get_bot_avatar(bot)):
                    with st.spinner("Thinking..."):
                        messages = format_messages(st.session_state.group_chat_messages[group_chat])
                        if st.session_state.group_config[GROUP_CHAT_TOPIC_KEY] != "":
                            messages[-1]["content"] += f'\nFor context, here is the group chat topic:\n{st.session_state.group_config[GROUP_CHAT_TOPIC_KEY]}'
                        response = st.session_state.openai_conn.generate_response(messages)
                        placeholder = st.empty()
                        full_response = ''
                        for item in response:
                            full_response += item
                            placeholder.markdown(full_response)
                        placeholder.markdown(full_response)
                st.session_state.group_chat_messages[group_chat].append({"role": "assistant", "name": bot, "content": response})
                st.session_state.group_config[GROUP_CHAT_ROUTER_KEY][group_chat].add_embedding(bot, full_response)
                st.session_state.last_message_timestamp = time.time()