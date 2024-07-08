import boto3
import json
import base64

def lambda_handler(event, context):
    # S3 and Bedrock clients
    s3 = boto3.client('s3')
    bedrock = boto3.client('bedrock-runtime', region_name="ap-south-1")

    # S3 bucket and file details
    bucket_name = "excel"  # Replace with your S3 bucket name
    file_key = "Conditional Monitoring Meter Master.xlsx"  # Replace with your file name

    try:
        # Read the file from S3
        s3_object = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = s3_object['Body'].read()

        # Encode the file content in base64
        encoded_file_content = base64.b64encode(file_content).decode('utf-8')

        # Define the message content with the file
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": "I'm going to give you a document"
                    },
                    {
                        "file": {
                            "name": file_key,
                            "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "data": encoded_file_content
                        }
                    }
                ]
            }
        ]

        # Define inference configuration
        inference_config = {
            "maxTokens": 2000,
            "temperature": 0
        }

        # Define additional model request fields
        additional_model_request_fields = {
            "top_k": None
        }

        # Construct the request payload
        payload = {
            "messages": messages,
            "inferenceConfig": inference_config,
            "additionalModelRequestFields": additional_model_request_fields
        }

        # Convert payload to JSON
        body = json.dumps(payload)

        # Specify model ID
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Invoke the model
        response = bedrock.invoke_model(
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
        )

        # Parse and extract response
        response_body = json.loads(response['body'].read())
        response_text = response_body['completions'][0]['data']['text']

        return {
            'statusCode': 200,
            'body': json.dumps(response_text)
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing the file')
        }
