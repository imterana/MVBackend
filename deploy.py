import mark_as_visited.deploy as deploy
import mark_as_visited.aws_lambda as aws_lambda

import os
import sys

branch = os.environ['GIT_BRANCH']
bucket = os.environ['AWS_DEPLOY_BUCKET']
region = os.environ['AWS_DEFAULT_REGION']
prefix = os.environ['AWS_DEPLOY_KEY_PREFIX']
gateway_role = os.environ['AWS_DEPLOY_GATEWAY_ROLE']
lambda_role = os.environ['AWS_DEPLOY_LAMBDA_ROLE']
stage = branch.replace('-', '_')

key = prefix + branch + '.zip'
print(key)
api_id = deploy.update_schema('mark_as_visited/deploy/api.json')

for method, function in aws_lambda.lambda_functions.items():
    lambda_name = "mav_{branch}_{function}".format(
        branch=branch, 
        function = function.__name__
    )
    handler = "{module}.{function}".format(module=function.__module__, function=function.__name__)
    print(handler)
    lambda_arn = deploy.recreate_lambda(lambda_name, handler, bucket, key, lambda_role)
    deploy.attach_lambda_to_method(api_id, lambda_arn, method, gateway_role, region)

deploy.create_api_deployment(api_id, stage)

print("https://{API_ID}.execute-api.{REGION}.amazonaws.com/{STAGE}".format(
    API_ID=api_id,
    REGION=region,
    STAGE=stage
))
