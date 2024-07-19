import streamlit as st
import base64
import json
import openpyxl
import csv
from io import BytesIO
import boto3
from myfunction import process_event  # Import the process_event function
import time

def main():
    st.title("Upload File and Enter Prompt")

    # User input: Prompt
    user_prompt = st.text_area("Enter your prompt:")

    # User input: File upload
    uploaded_file = st.file_uploader("Choose a file", type=['xlsx','csv',])

    # S3 Client
    s3_client = boto3.client('s3')
    bucket_name = 'bedrocktest03'

    # Get list of files in S3 bucket
    s3_files = []
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            s3_files = [obj['Key'] for obj in response['Contents']]
    except Exception as e:
        st.error(f"Error fetching S3 files: {e}")

    # Add "None" option to allow unselecting S3 file
    s3_file_selected = st.selectbox("Select a file from S3 bucket", ["None"] + s3_files)

    # Placeholder for timer
    timer_placeholder = st.empty()

    if st.button("Process"):
        with st.spinner("Querying..."):
            if user_prompt:
                start_time = time.time()
                timer_running = True
                
                if uploaded_file is not None:
                    # Read the uploaded file
                    file_contents = uploaded_file.read()
                    filetype = uploaded_file.type.split('/')[-1]
                    
                elif s3_file_selected != "None":
                    # Read the selected S3 file
                    s3_object = s3_client.get_object(Bucket=bucket_name, Key=s3_file_selected)
                    file_contents = s3_object['Body'].read()
                    filetype = s3_file_selected.split('.')[-1]
                else:
                    file_contents = None
                    filetype = ''  # Default filetype when no file is uploaded

                # Process the event using the local function
                result = process_event(user_prompt, file_contents, filetype)

                # Stop the timer
                elapsed_time = time.time() - start_time
                timer_running = False

                # Display the generated text
                st.subheader("Generated Text:")
                st.write(result.get('generated_text', ''))
                st.subheader("Response:")
                st.write(result.get('response', '').get('content', [])[0].get('text', ''))
            

                # Display elapsed time
                timer_placeholder.write(f"Elapsed time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
