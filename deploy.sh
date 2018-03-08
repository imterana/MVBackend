#! /bin/sh
if [ -z $CI ]; then
  export GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  export AWS_DEPLOY_BUCKET="markasvisited-source"
  export AWS_DEPLOY_KEY_PREFIX="source-"
  export AWS_DEPLOY_LAMBDA_REGION="eu-west-1"
  export AWS_DEPLOY_GATEWAY_ROLE="arn:aws:iam::505402960041:role/MAVApiGatewayRole"
  export AWS_DEPLOY_LAMBDA_ROLE="arn:aws:iam::505402960041:role/MAVLambdaRole"
  export AWS_DEFAULT_REGION="eu-west-1"
else
  if [ -z $TRAVIS_PULL_REQUEST_BRANCH ]; then
    export GIT_BRANCH="$TRAVIS_BRANCH" 
  else
    export GIT_BRANCH="$TRAVIS_PULL_REQUEST_BRANCH"
  fi
fi

zip -r archive mark_as_visited
aws s3 cp archive.zip "s3://markasvisited-source/${AWS_DEPLOY_KEY_PREFIX}${GIT_BRANCH}.zip"
python3 ./deploy.py
