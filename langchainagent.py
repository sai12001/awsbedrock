import streamlit as st
import boto3
import pandas as pd
from langchain_community.chat_models import BedrockChat
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Streamlit app
st.title("Pandas DataFrame Agent with Claude")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])
query = st.text_input("Enter your query")

# Set up the BedrockChat model
client = boto3.client('bedrock-runtime', region_name='us-east-1')

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
model_kwargs = {
    "max_tokens": 2048,
    "temperature": 0.0,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}

model = BedrockChat(
    client=client,
    model_id=model_id,
    model_kwargs=model_kwargs
)

if uploaded_file is not None:
    # Read the file into a DataFrame
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    
    st.write("DataFrame Preview:")
    st.write(df.head())

    # Create the agent
    agent = create_pandas_dataframe_agent(model, df, verbose=True, allow_dangerous_code=True)

    if query:
      with st.spinner("Processing your query..."):  
        try:
            result = agent.run(query)
            st.write("Result:")
            st.write(result)
        except Exception as e:
            st.error(f"An error occurred while processing the query: {e}")
else:
    if query:
     with st.spinner("Processing your query..."):
        try:

            system_template = "Answer the question precisely using your {Knowledge}"
            prompt_template = ChatPromptTemplate.from_messages([
                ('system', system_template),
                ('user', '{text}')
            ])
            parser = StrOutputParser()

            chain = prompt_template | model | parser

            # Chain Invoke
            result = chain.invoke({"Knowledge":"Prior Knowledge","text":query})
            st.write("Result:")
            st.write(result)
        except Exception as e:
            st.error(f"An error occurred while processing the query: {e}")
