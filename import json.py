import json
import boto3

def lambda_handler(event, context):
    # Extract user prompt and (optional) image data from the event object
    user_prompt = event.get('prompt', None)
    image_data = event.get('image_data', None)

    # Construct the request body for Bedrock API
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
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
    }

    # If image data is provided, include it in the request
    if image_data:
        request_body["messages"][0]["content"].append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_data
            }
        })

    # Create a Bedrock runtime client (replace with your region)
    client = boto3.client('bedrock-runtime', region_name='us-east-1')

    # Set the model ID for Claude 3.5 Sonnet
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    # Send the request to Bedrock using the 'invoke' API method
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(request_body)
    )

    # Extract the generated response from the payload
    generated_text = response['payload'].get('completions', [{}])[0].get('text', '')

    # Return the generated text
    return {
        'statusCode': 200,
        'body': json.dumps({'generated_text': generated_text})
    }
