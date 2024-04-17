import streamlit as st 
from typing import Optional 
from typing import Any 
from chat_generation import ChatGeneration
from doc_handler import RetrievalAugmentedGeneration

DEFAULT_BOT = "🧑‍💼 Assistant"
RESPONSE_CONTEXT = "Make sure to keep responses concise and conversational."

# Bot Config keys
BOT_OPTIONS_KEY = "bot_options"
BOT_PERSONALITIES_KEY = "bot_personalities"

# User Config keys
USER_AVATAR_KEY = "user_avatar"
USER_ABOUT_KEY = "user_about"
USER_NAME_KEY = "user_name"
USER_GENDER_KEY = "user_gender"
USER_AGE_KEY = "user_age"
USER_INFO_STRING_KEY = "user_info_string"
USER_CONFIG_KEYS_LIST = [USER_AVATAR_KEY, USER_NAME_KEY, USER_GENDER_KEY, USER_AGE_KEY, USER_ABOUT_KEY]


##### SESSION STATE VARIABLES #####
if 'show_create_bot_form' not in st.session_state: 
    st.session_state.show_create_bot_form = False

if 'show_user_settings_form' not in st.session_state: 
    st.session_state.show_user_settings_form = False

if 'bot_config' not in st.session_state: 
    st.session_state.bot_config = {
        BOT_OPTIONS_KEY: [DEFAULT_BOT],
        BOT_PERSONALITIES_KEY: {DEFAULT_BOT: f"You are a human-like, helpful assitant that listens to the user, offers practical advice, and helps the user in any way they need"}, 
    }

if 'user_config' not in st.session_state: 
    st.session_state.user_config = {
        USER_AVATAR_KEY: "🙂", 
        USER_ABOUT_KEY: "",
        USER_NAME_KEY: "", 
        USER_GENDER_KEY: "", 
        USER_AGE_KEY: "", 
        USER_INFO_STRING_KEY: "",
    }

if 'vector_db' not in st.session_state: 
    st.session_state.vector_db = {}

if 'openai_conn' not in st.session_state: 
    st.session_state.openai_conn = None

if 'api_key_given' not in st.session_state: 
    st.session_state.api_key_given = None

if "messages" not in st.session_state:
    st.session_state.messages = {DEFAULT_BOT: [{"role": "system", "content": st.session_state.bot_config[BOT_PERSONALITIES_KEY][DEFAULT_BOT]}, 
                                               {"role": "assistant", "content": "How may I assist you today?"}]}


def add_bot_to_session(emoji: str, name: str, description: str, pdf_files: Optional[Any]=None) -> None:
    for param in [name, description, emoji]:
        assert param != '' and not param.isspace(), "All fields need to be provided."
    
    bot_name = f'{emoji} {name}'
    st.session_state.bot_config[BOT_OPTIONS_KEY].append(bot_name)
    st.session_state.bot_config[BOT_PERSONALITIES_KEY].update({bot_name: description})
    st.session_state.messages[bot_name] = [{"role": "system", "content": description}, {"role": "assistant", "content": "Hey there!"}]
    
    if pdf_files: 
        rag = RetrievalAugmentedGeneration(st.session_state.api_key_given)
        rag.build_index(pdf_files)
        st.session_state.vector_db[bot_name] = rag

def get_bot_avatar(role: str) -> str: 
    return role.split(' ')[0]

# def write_api_key(key: str) -> None: 
#     with open('.env', 'w') as f: 
#         f.write(f'OPENAI_API_KEY={key}')
#     f.close()

st.title("🦄 Fantical")

# Side Bar (with form to create a new bot)
st.sidebar.title("🤖 Fantical bots")

def toggle_form(form):
    st.session_state[form] = not st.session_state[form]

# Create a new bot
st.sidebar.button("➕ Create bot", on_click=toggle_form, args=('show_create_bot_form',))
if st.session_state.show_create_bot_form:
    with st.sidebar.form("create_bot_form"):
        st.header("Create a new bot")
        
        if st.form_submit_button("🎲 Surprise me!"):
            with st.spinner("Generating..."):
                rand_emoji, rand_name, rand_description = st.session_state.openai_conn.generate_random_bot()
            add_bot_to_session(rand_emoji, rand_name, rand_description)

        emoji = st.text_input(label="Choose an avatar!", placeholder="Enter an emoji (⌃ + ⌘ + space)")
        name = st.text_input(label="Give it a name", placeholder="Chai bot")
        description = st.text_area(label="Give it some personality", placeholder="Chai bot is cool!")
        pdf_files = st.file_uploader("🧠 Add intelligence? (w/ RAG)", type="pdf", accept_multiple_files=True)
        
        if st.form_submit_button("✅"): 
            add_bot_to_session(emoji, name, description, pdf_files)

# User settings 
st.sidebar.button("👤 Settings", on_click=toggle_form, args=('show_user_settings_form',))
if st.session_state.show_user_settings_form: 
    with st.sidebar.form("user_settings_form"):
        st.header("User Settings")
        st.write(f"Current avatar: {st.session_state.user_config[USER_AVATAR_KEY]}")

        emoji = st.text_input(label="Choose an avatar!", placeholder="Enter an emoji (⌃ + ⌘ + space)")
        name = st.text_input(label="Enter your name", placeholder="Cool")
        gender = st.selectbox("Select gender", options=["Male", "Female", "Transgender", "Non-binary"])
        age = st.slider('Select your age', min_value=0, max_value=100, value=0, step=1)
        about = st.text_area(label="Tell us about yourself", placeholder="I am cool!")

        if st.form_submit_button("✅"):
            for i, field in enumerate([emoji, name, gender, str(age), about]):
                if field != "" and not field.isspace(): 
                    st.session_state.user_config[USER_CONFIG_KEYS_LIST[i]] = field
            
            st.session_state.user_config[USER_INFO_STRING_KEY] = f"For context, the user's name is {name}, who is a {gender} and is {age} years old. Here is a quick description of the user: {about}. Use this information if (and only if) the context is right and it helps th conversation!"

# Selection Menus (bot, voice)
role = st.sidebar.selectbox("Select your bot", options=st.session_state.bot_config[BOT_OPTIONS_KEY], key="choose_bot")
voice = None #st.sidebar.selectbox("Select a voice for your bot", options=[None, '🛠️ Alloy ', '🔊 Echo', '📖 Fable', '💎 Onyx', '🌟 Nova', '✨ Shimmer'])

openai_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
if openai_key: 
    # write_api_key(openai_key)
    st.session_state.api_key_given = openai_key
    st.session_state.openai_conn = ChatGeneration(openai_key)

if st.session_state.api_key_given:
    # Display or clear chat messages
    for message in st.session_state.messages[role]:
        message_role = message["role"]
        if message_role != "system":
            avatar = st.session_state.user_config[USER_AVATAR_KEY] if message_role == 'user' else get_bot_avatar(role)
            with st.chat_message(message_role, avatar=avatar):
                st.write(message["content"])

    # Read any chat inputs
    if prompt := st.chat_input():
        st.session_state.messages[role].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=st.session_state.user_config[USER_AVATAR_KEY]):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[role][-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar=get_bot_avatar(role)):
            with st.spinner("Thinking..."):
                # Augment prompt
                original_prompt = st.session_state.messages[role][-1]["content"]
                aug_prompt = f"\n{RESPONSE_CONTEXT}.\n{st.session_state.user_config[USER_INFO_STRING_KEY]}"
                if role in st.session_state.vector_db:
                    results = st.session_state.vector_db[role].search_index(original_prompt, k=2)
                    doc_content = "\n ".join([res for res in results])
                    aug_prompt += f'\nHere is some relevant content you can use to give a more accurate response:\n{doc_content}'
                st.session_state.messages[role][-1]["content"] += aug_prompt

                # Generate response
                response = st.session_state.openai_conn.generate_response(st.session_state.messages[role])

                # Remove augmented prompt from original prompt 
                st.session_state.messages[role][-1]["content"] = original_prompt
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        if voice:
            print(voice.split(' ')[1].lower())
            st.session_state.openai_conn.speak(full_response, voice.split(' ')[1].lower())
        st.session_state.messages[role].append({"role": "assistant", "content": full_response})