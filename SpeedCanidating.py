import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv, set_key
import pandas as pd
import os
import csv
import openai
from bs4 import BeautifulSoup
from datetime import datetime


st.set_page_config(layout="wide", page_icon="🇺🇸")


load_dotenv('.env')
openai.api_key = os.environ.get('OPENAI_API_KEY')

if not openai.api_key:
    openai.api_key = st.text_input("Enter OPENAI_API_KEY API key")
    set_key('.env', 'OPENAI_API_KEY', openai.api_key)

os.environ['OPENAI_API_KEY'] = openai.api_key


url = "https://raw.githubusercontent.com/NoDataFound/hackGPT/main/hackerParents/social_data.csv"
data = pd.read_csv(url)
new_row = pd.DataFrame({"Social Media": [" "], "Privacy Policy Link": [""]})
data = pd.concat([data, new_row], ignore_index=True)

with open("static/assets/css/ssc.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

PARTY_COLORS = {
    'Democrats': '#0a5f8a',
    'Republicans': '#c93e34',
    'Independent': 'white'
}

CANDIDATES = {
    'Democrats': ['Biden', 'Williamson', 'Uygur'],
    'Republicans': ['Trump', 'Haley', 'Ramaswamy', 'Hutchinson', 'Elder', 'Binkley', 'Scott', 'DeSantis', 'Pence', 'Christie', 'Burgum'],
    'Independent': ['Kennedy', 'West']
}

DATA_FILE = "log/questions_responses_log.csv"

def get_party(candidate):
    for party, candidates in CANDIDATES.items():
        if candidate in candidates:
            return party
        
    return None

def log_question(candidates, party, question, response):
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["candidate", "party", "question", "response"])

    for candidate in candidates:
        new_data = pd.DataFrame({
            "candidate": [candidate],
            "party": [party],
            "question": [question],
            "response": [response]
        })
        df = df.append(new_data, ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def get_candidate_text(candidate): 
    formatted_name = candidate.replace(' ', '_')
    file_path = f'training/candidates/{formatted_name}.txt'
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_response(candidate, question, text):
    chunk_size = 10000 
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    aggregated_response = ''
    
    for chunk in chunks:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant with the following information: {chunk}"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=1,
            max_tokens=200,  # Adjust to get a TLDR response
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        answer = response['choices'][0]['message']['content'].strip()  # Corrected key
        aggregated_response += answer + ' '
    
    # Now summarize the aggregated response
    summary_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant tasked with summarizing the following information."
            },
            {
                "role": "user",
                "content": aggregated_response
            }
        ],
        temperature=1,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    summary = summary_response['choices'][0]['message']['content'].strip()  # Corrected key
    return f"{candidate}: {summary}"

def get_response_table(responses):
    df = pd.DataFrame(responses.items(), columns=["Candidate", "Response"])
    df["Party"] = df["Candidate"].apply(get_party)
    # Rearrange columns
    df = df[["Party", "Candidate", "Response"]]
    return df

def display_table(df):
    # Replace newline characters with HTML line break tag
    df['Response'] = df['Response'].str.replace('\n', '<br>')

    # Convert DataFrame to HTML
    html = df.to_html(classes='table table-sm', escape=False, index=False, border=0, justify='left', header=True)

    # Use BeautifulSoup to manipulate the HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Update header row with 'active' class for a lighter color and uppercase, bold text
    header_row = soup.find('tr')
    header_row['class'] = 'active'
    for th in header_row.find_all('th'):
        th.string = th.text.upper()
        th['style'] = 'font-weight: bold;'

    # Update each data row with the appropriate class based on the party
    for tr, party in zip(soup.find_all('tr')[1:], df['Party']):  # Skip header row
        tr['class'] = 'table-danger' if party == 'Republicans' else 'table-info' if party == 'Democrats' else ''

    # Convert back to HTML and then to markdown
    html = str(soup)
    st.markdown(html, unsafe_allow_html=True)


def main():
    st.markdown(
        """
        <link
            rel="stylesheet"
            href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"
        >
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.image(os.path.join("resources", "images", "ballot_box-blue.png"), width=80)
        
        selected_party = st.selectbox('Select party:', list(CANDIDATES.keys()))
        selected_candidates = st.multiselect(f'Choose {selected_party} candidates:', CANDIDATES[selected_party])
        if selected_party  == 'Democrats':
            st.markdown("""<style>span[data-baseweb="tag"] {  background-color: #242529 !important;}</style>""",unsafe_allow_html=True,)
        if selected_party == 'Republicans':
            st.markdown("""<style>span[data-baseweb="tag"] {  background-color: #242529 !important;}</style>""",unsafe_allow_html=True,)
        
        additional_party_option = st.checkbox("Select another party?")
        
        if additional_party_option:
            remaining_parties = [party for party in CANDIDATES.keys() if party != selected_party]
            additional_party = st.selectbox('Select another party:', remaining_parties)
            additional_candidates = st.multiselect(f'Choose {additional_party} candidates:', CANDIDATES[additional_party])
            selected_candidates.extend(additional_candidates)

           
         
    with st.form("Ask Question"):
        question = st.text_input(label='',placeholder ="Ask your question")
        if selected_candidates:
            cols = st.columns(len(selected_candidates))
            for idx, candidate in enumerate(selected_candidates):
                party_of_candidate = get_party(candidate)
                img_path = os.path.join("resources", "images",f"{party_of_candidate}", f"{candidate.lower()}.png")
                cols[idx].image(img_path, caption=candidate, width=60)
        ask_all = st.checkbox("Ask all Presidential candidates")
        submit = st.form_submit_button("Submit")

        if submit and question:
            responses = {}
            for candidate in selected_candidates:
                candidate_text = get_candidate_text(candidate)
                response = get_response(candidate, question, candidate_text)
                responses[candidate] = response
                log_question([candidate], get_party(candidate), question, response)

            # Get the DataFrame and display it
            response_df = get_response_table(responses)
            display_table(response_df)

            # Save the DataFrame to a CSV file


    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        col1, col2 = st.columns(2)

        candidate_counts = df['candidate'].value_counts()
        candidate_colors = [PARTY_COLORS[get_party(candidate)] for candidate in candidate_counts.index]

        fig1 = go.Figure(data=[go.Bar(x=candidate_counts.index, y=candidate_counts, marker_color=candidate_colors)])
        fig1.update_layout(title="Question Counts per Canidate")
        col1.plotly_chart(fig1, use_container_width=True)

        party_counts = df['party'].value_counts()
        fig2 = go.Figure(data=[go.Pie(labels=party_counts.index, values=party_counts, hole=.3, marker_colors=[PARTY_COLORS[p] for p in party_counts.index])])
        fig2.update_layout(title="Party Question Distribution")
        col2.plotly_chart(fig2, use_container_width=True)

if __name__ == '__main__':
    main()
