from datetime import datetime, timedelta
from airflow import DAG
from airflow.models import Variable
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.time_delta import TimeDeltaSensor
import json

def get_lambda_input(keyword):
    """Prepare the input for Lambda function"""
    return {
        "keyword": keyword,
        "timestamp": datetime.now().isoformat()
    }

# Read keywords from config
keywords = Variable.get("job_keywords", deserialize_json=True)

with DAG(
    'linkedin_jobs_search',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': True,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    description='Search LinkedIn jobs for different roles',
    schedule_interval=None,  # Set to None for manual triggering
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['linkedin', 'jobs'],
) as dag:

    start = EmptyOperator(task_id='start')
    prev_task = start
    
    # Create tasks for each keyword
    for i, keyword in enumerate(keywords):
        if i > 0:
            # Add wait task between searches
            wait_task = TimeDeltaSensor(
                task_id=f'wait_{i}',
                delta=timedelta(minutes=5)
            )
            prev_task >> wait_task
            prev_task = wait_task
        
        search_task = LambdaInvokeFunctionOperator(
            task_id=f'search_{keyword.replace(" ", "_").lower()}_jobs',
            function_name='linkedin_scraper',
            payload=json.dumps(get_lambda_input(keyword)),
            aws_conn_id='aws_test'
        )
        
        prev_task >> search_task
        prev_task = search_task