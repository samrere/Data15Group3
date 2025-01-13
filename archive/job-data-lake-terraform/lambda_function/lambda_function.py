import json
import os
import re
import boto3
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from tiktoken import encoding_for_model

# Initialize the S3 client
s3 = boto3.client('s3')

# Function to count tokens in a given text
def count_tokens(text, model="gpt-4o-mini"):
    enc = encoding_for_model(model)
    return len(enc.encode(text))

# Function to split text into chunks based on token limits
def split_text_into_chunks(text, model="gpt-4o-mini", chunk_size=15000):
    enc = encoding_for_model(model)
    tokens = enc.encode(text)
    for i in range(0, len(tokens), chunk_size):
        yield enc.decode(tokens[i:i + chunk_size])

# Function to clean excessive spaces from text
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# Lambda handler function
def lambda_handler(event, context):
    # S3 bucket and file information from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    input_key = event['Records'][0]['s3']['object']['key']
    output_key = input_key.replace('raw/', 'processed/')

    # Read raw job data from S3
    raw_data = read_s3_file(bucket_name, input_key)
    if not raw_data:
        return {
            'statusCode': 400,
            'body': "No data found in the provided file."
        }

    # Clean the descriptions using GPT
    topic = "AWS and Data Engineering"
    api_key = os.environ["OPENAI_API_KEY"]
    cleaned_jobs = clean_descriptions_with_gpt(raw_data, topic, api_key)

    # Save cleaned data to S3 in the processed folder
    save_s3_file(bucket_name, output_key, cleaned_jobs)

    return {
        'statusCode': 200,
        'body': f"Cleaned data saved to {output_key} in bucket {bucket_name}."
    }

# Function to clean descriptions using GPT
def clean_descriptions_with_gpt(json_data, topic, api_key):
    print("Processing descriptions with GPT...")
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

    # Create a prompt template for summarizing the 'description' field
    description_prompt_template = """
    Summarize the following job description while keeping the most relevant details for the topic: "{topic}". 
    Ensure the summary is concise and retains the original context.

    Description:
    {text}
    """
    description_prompt = PromptTemplate(input_variables=["text", "topic"], template=description_prompt_template)

    # Create a chain for processing descriptions
    description_chain = LLMChain(llm=llm, prompt=description_prompt)

    cleaned_data = []

    for entry in json_data:
        # Summarize the description field
        description = entry.get("description", "")
        cleaned_description = ""
        for chunk in split_text_into_chunks(clean_text(description)):
            cleaned_chunk = description_chain.run({"text": chunk, "topic": topic})
            cleaned_description += cleaned_chunk

        # Update only the description field
        entry["description"] = cleaned_description.strip()
        cleaned_data.append(entry)

    return cleaned_data

# Function to read a JSON file from S3
def read_s3_file(bucket_name, key):
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        print(f"Error reading file from S3: {e}")
        return None

# Function to save a JSON object to S3
def save_s3_file(bucket_name, key, data):
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(data, indent=4),
            ContentType="application/json"
        )
        print(f"Data saved to S3: {bucket_name}/{key}")
    except Exception as e:
        print(f"Error saving file to S3: {e}")
