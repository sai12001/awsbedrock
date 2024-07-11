import json
import boto3
import base64

def lambda_handler(event, context):
    # Extract request body from the event
    request_body = event.get('body', {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What's aws for"
                    }
                ]
            }
        ]
    })

    # Create an S3 client
    s3_client = boto3.client('s3')

    # S3 bucket and image key details
    bucket_name = 'bedrocktest02'
    image_key = 'testimage.png'

    try:
        # Retrieve the image from S3
        s3_object = s3_client.get_object(Bucket=bucket_name, Key=image_key)
        image_data = s3_object['Body'].read()

        # Encode the image data to base64
        encoded_image_data = base64.b64encode(image_data).decode('utf-8')

        # Add image data to the request body
        request_body["messages"][0]["content"].append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": encoded_image_data
            }
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
