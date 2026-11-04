#!/bin/bash
# Floci 实测脚本：S3 / DynamoDB / SQS / SNS / Secrets / SSM
export AWS_ENDPOINT_URL=http://localhost:4566 AWS_DEFAULT_REGION=us-east-1 AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_PAGER=
r(){ echo "\$ $*"; eval "$@" 2>&1; echo; }
sec(){ echo "=== $1"; }
cd /tmp && echo "hello floci 你好" > hello.txt
sec 1 env
r 'env | grep ^AWS_ | sort'
r 'aws sts get-caller-identity'
sec 2 s3
r 'aws s3 mb s3://demo-bucket'
r 'aws s3 cp hello.txt s3://demo-bucket/docs/hello.txt'
r 'aws s3 ls s3://demo-bucket --recursive'
r 'aws s3 cp s3://demo-bucket/docs/hello.txt -'
r 'URL=$(aws s3 presign s3://demo-bucket/docs/hello.txt --expires-in 600); echo "$URL" | cut -c1-90; curl -s "$URL"'
sec 3 dynamodb
r 'aws dynamodb create-table --table-name users --attribute-definitions AttributeName=pk,AttributeType=S --key-schema AttributeName=pk,KeyType=HASH --billing-mode PAY_PER_REQUEST --query TableDescription.TableStatus'
r "aws dynamodb put-item --table-name users --item '{\"pk\":{\"S\":\"u1\"},\"name\":{\"S\":\"小明\"},\"age\":{\"N\":\"18\"}}'"
r "aws dynamodb get-item --table-name users --key '{\"pk\":{\"S\":\"u1\"}}' --output json"
r 'aws dynamodb list-tables'
sec 4 sqs-sns
r 'Q=$(aws sqs create-queue --queue-name orders --query QueueUrl --output text); echo $Q'
r 'T=$(aws sns create-topic --name order-events --query TopicArn --output text); echo $T'
r 'aws sns subscribe --topic-arn $T --protocol sqs --notification-endpoint arn:aws:sqs:us-east-1:000000000000:orders --attributes RawMessageDelivery=true'
r "aws sns publish --topic-arn \$T --message '{\"order\":42,\"item\":\"咖啡\"}'"
r 'aws sqs receive-message --queue-url $Q --wait-time-seconds 2 --query "Messages[0].Body" --output text'
sec 5 secrets-ssm
r 'aws secretsmanager create-secret --name prod/db-password --secret-string "s3cr3t!" --query Name'
r 'aws secretsmanager get-secret-value --secret-id prod/db-password --query SecretString --output text'
r 'aws ssm put-parameter --name /app/feature-flag --type String --value on --query Version'
r 'aws ssm get-parameter --name /app/feature-flag --query Parameter.Value --output text'
sec 6 lambda
r 'aws lambda list-functions'
printf 'def handler(e,c):\n    return {"ok":True}\n' > fn.py && python3 -c "import zipfile;zipfile.ZipFile('fn.zip','w').write('fn.py')"
r 'aws lambda create-function --function-name hello --runtime python3.12 --role arn:aws:iam::000000000000:role/x --handler fn.handler --zip-file fileb://fn.zip --query State'
r 'aws lambda invoke --function-name hello out.json; cat out.json'
