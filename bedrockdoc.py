import json
import boto3
import openpyxl
from io import BytesIO

def lambda_handler(event, context):
    print(event)
    user_prompt=event['prompt']
    
    # Extract request body from the event
    request_body = event.get('body', {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 50,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]
    })

    # Create an S3 client
    s3_client = boto3.client('s3')

    # S3 bucket and file key details
    bucket_name = 'bedrocktest03'
    file_key = 'Employee_Details-2.xlsx'

    try:
        # Retrieve the file from S3
        s3_object = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_data = s3_object['Body'].read()

        # Read the Excel file
        excel_file = BytesIO(file_data)
        workbook = openpyxl.load_workbook(excel_file)
        sheet = workbook.active

        # Extract information from the Excel file
        excel_info = []
        for row in sheet.iter_rows(values_only=True):
            excel_info.append(list(row))

        # Convert Excel data to a readable string format
        excel_data_text = "\n".join([", ".join(map(str, row)) for row in excel_info])

        # Add Excel data as text to the request body
        request_body["messages"][0]["content"].append({
            "type": "text",
            "text": f"Excel file contents:\n{excel_data_text}"
        })

        # Create a Bedrock runtime client (replace with your region)
        client = boto3.client('bedrock-runtime', region_name='us-east-1')

        # Set the model ID for Claude 3 Sonnet
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Send the request to Bedrock using the 'invoke' API method
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        # Read the content from the StreamingBody
        response_payload = response['body'].read().decode('utf-8')
        print("Full Response Payload:", response_payload)

        # Parse the payload
        payload = json.loads(response_payload)
        generated_text = payload.get('completions', [{}])[0].get('text', '')

        # Return the generated text
        return {
            'statusCode': 200,
            'body': json.dumps({'generated_text': generated_text, 'response': payload})
        }

    except Exception as e:
        # Handle any errors that occurred during the process
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
