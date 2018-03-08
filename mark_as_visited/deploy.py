import boto3
import os
from . import aws_lambda


def s3_uri(bucket, key):
    S3_URI = 's3://{bucket}/{key}'.format(bucket=bucket, key=key)


def recreate_lambda(name, handler, bucket, key, role):
    lambda_client = boto3.client('lambda')

    try:
        lambda_client.delete_function(FunctionName=name)
    except lambda_client.exceptions.ResourceNotFoundException:
        pass

    func = lambda_client.create_function(
        FunctionName=name,
        Role=role,
        Handler=handler,
        Code={
            "S3Bucket": bucket,
            "S3Key": key
        },
        MemorySize=128,
        Timeout=300,
        Runtime="python3.6"
    )
    return func['FunctionArn']


def get_resource(resources, target):
    return [res for res in resources['items'] if res['path'] == target]


def update_schema(schema_path):
    apigateway_client = boto3.client('apigateway')
    with open(schema_path) as spec:
        api = apigateway_client.import_rest_api(
                body=spec.read().encode('utf-8')
        )

    return api['id']


def attach_lambda_to_method(api_id, lambda_arn, method, role, lambda_region):
    apigateway_client = boto3.client('apigateway')
    resources = apigateway_client.get_resources(
        restApiId=api_id
    )
    print(resources)
    resource = get_resource(resources, method)
    assert len(resource) == 1
    method_resource_id = resource[0]['id']
    print(method_resource_id)

    response = apigateway_client.put_integration(
        restApiId=api_id,
        resourceId=method_resource_id,
        httpMethod='GET',
        integrationHttpMethod='POST',
        type='AWS_PROXY',
        uri='arn:aws:apigateway:{region}:lambda:path/2015-03-31/'
        'functions/{func}/invocations'.format(
            region=lambda_region,
            func=lambda_arn
        ),
        credentials=role
    )


def create_api_deployment(api_id, stage):
    apigateway_client = boto3.client('apigateway')
    deployment = apigateway_client.create_deployment(
        restApiId=api_id,
        stageName=stage
    )
