import os
import sys
import numpy as np
import pandas as pd
import requests
import streamlit as st
import boto3
import openpyxl
import csv
import io
import base64
import json
import logging
from io import BytesIO
from streamlit_chat import message

logging.basicConfig(level=logging.DEBUG)

# Hide traceback
st.set_option('client.showErrorDetails', False)

# Setting page title and header
st.set_page_config(page_title="CSV BOT", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>CSV BOT - Ask questions to your data</h1>", unsafe_allow_html=True)

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# Allow user to upload CSV file
uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    # Read uploaded file as a Pandas DataFrame
    dataframe = pd.read_csv(uploaded_file)
    st.write(dataframe)
    data_quality_check = st.checkbox('Request Data Quality Check')
    
    if data_quality_check:
        st.write("The following data quality analysis has been made")
        st.markdown("**1. The dataset column names have been checked for trailing spaces**")
        trailing_spaces = dataframe.columns[dataframe.columns.str.contains("\s+$", regex=True)]
        if trailing_spaces.empty:
            st.markdown('*Columns_ names_ are_ found_ ok*')
        else:
            st.markdown("*Columns with trailing spaces:* ")
            st.write(f"{', '.join(trailing_spaces)}")

        # Check data type of columns with name 'date'
        st.markdown("**2. The dataset's date columns have been checked for the correct data type**")
        date_cols = dataframe.select_dtypes(include="object").filter(regex="(?i)date").columns
        for col in date_cols:
            if pd.to_datetime(dataframe[col], errors="coerce").isna().sum() > 0:
                st.write(f"Column {col} should contain dates but has wrong data type")
            else:
                st.write("Columns with date are of the correct data type")
        st.markdown("**:red[CSV BOT recommends fixing data quality issues prior to querying your data]**")

# Define function to generate response from user input using AWS Bedrock Claude model
def generate_response(prompt, file_contents=None, filetype=None):
    try:
        logging.debug(f"Prompt: {prompt}")
        logging.debug(f"Filetype: {filetype}")

        if file_contents:
            logging.debug("Processing file contents...")
            if filetype.lower() in ['xlsx', 'xls', "vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                # Read Excel file
                excel_file = BytesIO(file_contents)
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active

                # Process Excel data
                excel_info = []
                for row in sheet.iter_rows(values_only=True):
                    excel_info.append(list(row))

                # Convert Excel data to a readable string format
                excel_data_text = "\n".join([", ".join(map(str, row)) for row in excel_info])
                logging.debug(f"Excel data text: {excel_data_text}")

                # Add Excel data as text to the request body
                prompt += f"\ndata:\n{excel_data_text}"

            elif filetype.lower() == 'csv':
                # Read CSV file
                csv_data = file_contents.decode('utf-8')
                csv_reader = csv.reader(io.StringIO(csv_data))

                # Process CSV rows
                csv_info = []
                for row in csv_reader:
                    csv_info.append(row)

                # Convert CSV data to a readable string format
                csv_data_text = "\n".join([", ".join(map(str, row)) for row in csv_info])
                logging.debug(f"CSV data text: {csv_data_text}")

                # Add CSV data as text to the request body
                prompt += f"\ndata:\n{csv_data_text}"

            else:
                logging.debug(f"Unhandled file type: {filetype}")

        prompt += "Retrieve information from the DataFrame based on the given query if it involves manipulation. The answer should be in three lines. Do not provide any code."

        # Create a request body for Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 900,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        logging.debug(f"Request Body: {json.dumps(request_body)}")

        # Create a Bedrock runtime client
        client = boto3.client('bedrock-runtime')

        # Set the model ID for Claude 3 Sonnet
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Send the request to Bedrock using the 'invoke' API method
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        # Read the content from the StreamingBody
        response_payload = response['body'].read().decode('utf-8')
        logging.debug(f"Response Payload: {response_payload}")

        payload = json.loads(response_payload)
        generated_text = payload.get('completions', [{}])[0].get('text', '')

        # Return the generated text
        return {
            'generated_text': generated_text,
            'response': payload
        }

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {
            'error': str(e)
        }

# container for chat history
response_container = st.container()

# container for text box
input_container = st.container()

with input_container:
    # Create a form for user input
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        # If user submits input, generate response and store input and response in session state variables
        try:
            file_contents = uploaded_file.getvalue() if uploaded_file else None
            filetype = uploaded_file.type if uploaded_file else None
            query_response = generate_response(user_input, file_contents, filetype)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(query_response['generated_text'])
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if st.session_state['generated']:
    # Display chat history in a container
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
