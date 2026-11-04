#!/bin/bash
# 实测：持久化（FLOCI_STORAGE_MODE=persistent）+ 启动钩子（ready.d）
export AWS_ENDPOINT_URL=http://localhost:4566 AWS_DEFAULT_REGION=us-east-1 AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_PAGER=
B=/workspace/floci-tutorial/bin/floci-aws
r(){ echo "\$ $*"; eval "$@" 2>&1; echo; }
start(){ (cd /tmp/flocirun && eval "$1 nohup $B > /tmp/flocirun/server.log 2>&1 &"); sleep 2; }
stop(){ pkill -f bin/floci-aws; sleep 1; }
stop; rm -rf /tmp/flocirun; mkdir -p /tmp/flocirun/init/ready.d
echo "=== 7 persist"
echo '# 默认 memory 模式：重启后数据清空'
start ""; r 'aws s3 mb s3://keep-me'; stop; start ""; r 'aws s3 ls'
echo '# 打开持久化再试'
stop; start "FLOCI_STORAGE_MODE=persistent FLOCI_STORAGE_PERSISTENT_PATH=/tmp/flocirun/data"
r 'aws s3 mb s3://keep-me && echo hi | aws s3 cp - s3://keep-me/a.txt'
stop; echo '$ # 重启 floci-aws …'; echo
start "FLOCI_STORAGE_MODE=persistent FLOCI_STORAGE_PERSISTENT_PATH=/tmp/flocirun/data"
r 'aws s3 ls s3://keep-me'
r 'ls /tmp/flocirun/data | head -5'
echo "=== 8 hooks"
cat > /tmp/flocirun/init/ready.d/01-seed.sh <<'H'
#!/bin/sh
aws s3 mb s3://seeded-bucket
aws sqs create-queue --queue-name seeded-queue
H
stop
r 'cat /tmp/flocirun/init/ready.d/01-seed.sh' 
start "FLOCI_INIT_HOOKS_DIR=/tmp/flocirun/init"
r 'curl -s localhost:4566/_floci/init; echo'
r 'aws s3 ls; aws sqs list-queues --query QueueUrls'
r 'grep -i "hook\|init" /tmp/flocirun/server.log | cut -c25-150 | head -6'
