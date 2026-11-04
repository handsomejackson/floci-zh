# 用 boto3 写的“业务代码”+测试：上传订单到 S3，写 DynamoDB，发 SQS 消息
import boto3, json, time, uuid
s3, ddb, sqs = boto3.client("s3"), boto3.client("dynamodb"), boto3.client("sqs")

def place_order(item, price):
    oid = str(uuid.uuid4())[:8]
    s3.put_object(Bucket="orders-archive", Key=f"{oid}.json", Body=json.dumps({"item": item, "price": price}, ensure_ascii=False))
    ddb.put_item(TableName="orders", Item={"id": {"S": oid}, "item": {"S": item}, "price": {"N": str(price)}})
    sqs.send_message(QueueUrl=sqs.get_queue_url(QueueName="order-queue")["QueueUrl"], MessageBody=oid)
    return oid

def setup():
    s3.create_bucket(Bucket="orders-archive")
    ddb.create_table(TableName="orders", AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                     KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}], BillingMode="PAY_PER_REQUEST")
    sqs.create_queue(QueueName="order-queue")

def test_place_order():
    oid = place_order("拿铁", 28)
    assert json.loads(s3.get_object(Bucket="orders-archive", Key=f"{oid}.json")["Body"].read())["item"] == "拿铁"
    assert ddb.get_item(TableName="orders", Key={"id": {"S": oid}})["Item"]["price"]["N"] == "28"
    q = sqs.get_queue_url(QueueName="order-queue")["QueueUrl"]
    assert sqs.receive_message(QueueUrl=q, WaitTimeSeconds=1)["Messages"][0]["Body"] == oid
    return oid

if __name__ == "__main__":
    t = time.time(); setup(); print("setup OK")
    n = 50
    for i in range(n): test_place_order()
    print(f"✓ {n} 次下单测试全部通过，用时 {time.time()-t:.2f}s（含建表建桶）")
