import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
import re

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

TONE_OPTIONS = {
    "professional": "professional and formal",
    "casual": "casual and conversational",
    "humorous": "humorous and witty",
    "inspirational": "inspirational and motivational",
    "educational": "educational and informative",
    "personal": "personal and intimate",
    "analytical": "analytical and data-driven"
}

# Param extractor function
def extract_params(prompt: str) -> dict:
    default_params = {
        "persona": 'Human',
        "audience": "LinkedIn Fam",
        "topic": prompt,
        "region": "India",
        "tone": st.session_state.selected_tone
    }

    prompt_lower = prompt.lower()

    persona_match = re.search(r'as (?:a[n]? )?([a-z\s]+?)(?: for| to| on| about|$)', prompt_lower)
    persona = persona_match.group(1).strip().title() if persona_match else default_params['persona']

    audience_match = re.search(r'for ([a-z\s]+?)(?: on| about| as| to|$)', prompt_lower)
    audience = audience_match.group(1).strip().title() if audience_match else default_params['audience']

    topic_match = re.search(r'(?:write|post|explain|talk)[^a-zA-Z0-9]*(?:me|us)?[^a-zA-Z0-9]*(?:about|on)?[^a-zA-Z0-9]*([a-z\s\(\)]+)', prompt_lower)
    topic = topic_match.group(1).strip().capitalize() if topic_match else default_params['topic']

    region = default_params['region']

    return {
        "persona": persona,
        "audience": audience,
        "topic": topic,
        "region": region,
        "tone": default_params['tone']
    }

# Generate formal text
def generate_formal_text(params):
    linkedin_prompt = (
    """Generate a LinkedIn post about {topic} for {audience} in a {tone} tone.  
    **Follow these rules strictly:**  
    - Only output the post text.  
    - No "Here’s your post", no headings, no disclaimers.  
    - No explanations, reasoning, or notes.  
    - If you add anything extra, I will ask you to rewrite it.  

    Post:"""  
)
    response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {"role": "user", "content": linkedin_prompt.format(**params)}
        ],
        temperature=0.7,
        max_tokens=800
    )

    return re.sub(r"<think>.*?</think>", "", response.choices[0].message.content, flags=re.DOTALL).strip()

# Humanize AI text
def humanize_text(ai_text, params):
    humanization_prompt = """Take the following AI-generated content and rewrite it in a human-like tone.
Instructions:
                    - Start with a strong, catchy, attention grabbing hook that grabs attention in the first few milliseconds (1–2 lines max).
                    - Create a hook for this then seperate the story and information first tell the story and then give this insights and keep it very short so that everyone reads it because if it's too long every one are lazy so they won't read.
                    - Voice: {persona} speaking to {audience} about {topic} in a {tone} tone
                    - Add A LOT OF cultural nods to {region}
                    - Include A LOT OF human traits (like mid-sentence restarts or casual contractions)
                    - Use varied sentence lengths (5-28 words)
                    - Sprinkle in 5-6 trending slang terms from 2023-2025
                    - Keep 12% natural repetition
                    - Avoid robotic tone, generic analogies, or perfect grammar
                    - Do not use markdown or formatting like *, **, or _ 
                    - Output only the post content. Do not add summaries or commentary.
                    - Strictly DO NOT include introductory lines like "Here's the rewritten text" or "Here's your post"
                    - Keep the length flexible, but do NOT exceed 200 words, add emoticons and emojis to make it more engaging
                    - Don't write reasoning for the post, just write the post

Original AI Text:
\"\"\"{ai_text}\"\"\"
"""

    prompt = humanization_prompt.format(ai_text=ai_text, **params)

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": """You are a humanization expert that transforms robotic AI content into casual, relatable writing. Your main aim is to create undetected AI-generated content.
                    
                """
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.95,
        max_tokens=1024,
        top_p=0.95,
    )

    return response.choices[0].message.content

# Streamlit UI
st.title("🧠 LinkedIn Post Generator")

# Initialize session state variables if they don't exist
if 'ai_text' not in st.session_state:
    st.session_state.ai_text = ""
if 'humanized_text' not in st.session_state:
    st.session_state.humanized_text = ""
if 'params' not in st.session_state:
    st.session_state.params = {}
if 'selected_tone' not in st.session_state:
    st.session_state.selected_tone = "casual"

# Add tone selector

prompt = st.text_area("✍️ Enter your topic or prompt:", height=150)

st.session_state.selected_tone = st.selectbox(
    "🎭 Select Tone of Voice",
    options=list(TONE_OPTIONS.keys()),
    format_func=lambda x: TONE_OPTIONS[x].title()
)
if st.button("Generate LinkedIn Post"):
    if not prompt.strip():
        st.warning("Please enter a prompt before generating.")
    else:
        with st.spinner("Extracting parameters..."):
            st.session_state.params = extract_params(prompt)
            st.write("🧾 **Extracted Parameters**", st.session_state.params)

        with st.spinner("Generating formal LinkedIn post..."):
            st.session_state.ai_text = generate_formal_text(st.session_state.params)
            st.success("Formal post generated.")

        with st.spinner("Humanizing the post..."):
            st.session_state.humanized_text = humanize_text(st.session_state.ai_text, st.session_state.params)
            st.success("Humanized version ready!")

# Create two columns for the posts
col1, col2 = st.columns(2)

with col1:
    st.subheader("🤖 AI-Generated Post")
    st.text_area("AI Post", st.session_state.ai_text, height=400, key="ai_text_area", label_visibility="collapsed")

with col2:
    st.subheader("😎 Humanized Post")
    st.text_area("Humanized Post", st.session_state.humanized_text, height=400, key="humanized_text_area", label_visibility="collapsed")

# Add buttons below the posts
st.markdown("---")  # Add a horizontal line for separation
col3, col4 = st.columns(2)

with col3:
    if st.button("✏️ Rewrite AI Post"):
        if st.session_state.params:
            with st.spinner("Rewriting the AI post..."):
                st.session_state.ai_text = generate_formal_text(st.session_state.params)
                st.success("AI post rewritten!")
                st.rerun()
        else:
            st.warning("Please generate a post first before rewriting.")

with col4:
    if st.button("🔄 Rehumanize"):
        if st.session_state.ai_text:
            with st.spinner("Rehumanizing the post..."):
                st.session_state.humanized_text = humanize_text(st.session_state.ai_text, st.session_state.params)
                st.success("Rehumanized version ready!")
                st.rerun()
        else:
            st.warning("Please generate a post first before rehumanizing.")
