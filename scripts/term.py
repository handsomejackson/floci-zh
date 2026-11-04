import re,sys,html,asyncio
from playwright.async_api import async_playwright
C={30:'#555',31:'#e06c75',32:'#98c379',33:'#e5c07b',34:'#61afef',35:'#c678dd',36:'#56b6c2',37:'#dcdfe4',90:'#7f848e',91:'#ff7b86',92:'#b5e890',93:'#f0d58a',94:'#8cc4ff',95:'#d79bf0',96:'#7fd4df',97:'#fff'}
def conv(t):
    out=[];st={}
    for part in re.split(r'(\x1b\[[0-9;]*m)',t):
        m=re.match(r'\x1b\[([0-9;]*)m',part)
        if m:
            codes=[int(x) for x in m.group(1).split(';') if x] or [0]
            i=0
            while i<len(codes):
                c=codes[i]
                if c==0: st={}
                elif c==1: st['b']=1
                elif c==2: st['d']=1
                elif c==3: st['i']=1
                elif c==22: st.pop('b',0);st.pop('d',0)
                elif c==39: st.pop('fg',0)
                elif c in C: st['fg']=C[c]
                elif c==38 and i+2<len(codes) and codes[i+1]==5:
                    st['fg']=C.get(30+codes[i+2]%8,'#dcdfe4'); i+=2
                i+=1
            continue
        if not part: continue
        s=html.escape(part)
        s=re.sub(r'^(\$ .*)$',r'<span style="color:#f0d58a;font-weight:bold">\1</span>',s,flags=re.M)
        css=(f"color:{st['fg']};" if 'fg' in st else '')+('font-weight:bold;' if 'b' in st else '')+('opacity:.65;' if 'd' in st else '')+('font-style:italic;' if 'i' in st else '')
        out.append(f'<span style="{css}">{s}</span>' if css else s)
    return ''.join(out)
async def shot(items):
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"]);pg=await b.new_page(viewport={'width':1000,'height':300},device_scale_factor=2)
        for title,text,path in items:
            body=conv(text.strip('\n'))
            await pg.set_content(f"""<html><meta charset=utf-8><style>body{{margin:0;padding:18px;background:#e9e7e1}}#w{{display:inline-block;min-width:900px;background:#1e1f24;border-radius:10px;box-shadow:0 6px 20px #0003;overflow:hidden}}#t{{background:#2c2e35;color:#aab;font:13px 'Noto Sans CJK SC';padding:8px 14px}}#t i{{display:inline-block;width:11px;height:11px;border-radius:6px;margin-right:6px}}pre{{margin:0;padding:14px 18px;color:#dcdfe4;font:14px/1.5 'DejaVu Sans Mono','Noto Sans Mono CJK SC',monospace;white-space:pre}}</style><body><div id=w><div id=t><i style=background:#ff5f56></i><i style=background:#ffbd2e></i><i style=background:#27c93f></i>&nbsp;{html.escape(title)}</div><pre>{body}</pre></div></body></html>""")
            await (await pg.query_selector('#w')).screenshot(path=path)
        await b.close()
if __name__=='__main__':
    R=lambda f:open(f,encoding='utf-8').read()
    def secs(f):
        d={}
        for chunk in re.split(r'^=== ',R(f),flags=re.M)[1:]:
            k,_,v=chunk.partition('\n'); d[k.split()[0]]=v
        return d
    a=secs('logs/demo.log'); b=secs('logs/demo2.log'); v1=secs('logs/demo-cliv1.log')
    pit=v1['4'].split('$ T=')[0].rstrip()+'\n\n'+R('logs/cliv1-extra.log')
    items=[('实测：下载与启动 floci-aws（原生二进制）',R('logs/install.log'),'images/01-install.png'),
     ('配好 4 个环境变量，AWS 工具就指向本地',a['1'],'images/02-env.png'),
     ('S3：建桶、上传、下载、预签名 URL',a['2'],'images/03-s3.png'),
     ('DynamoDB：建表、写入、读取',a['3'],'images/04-dynamodb.png'),
     ('SNS → SQS：发布一条消息，队列里收到',a['4'],'images/05-sns-sqs.png'),
     ('Secrets Manager 和 SSM 参数',a['5'],'images/06-secrets.png'),
     ('boto3 写的业务测试：50 次下单全过',"$ python3 app_test.py\n"+R('logs/app_test.log'),'images/07-boto3.png'),
     ('踩坑：AWS CLI v1 的 SQS 无视 AWS_ENDPOINT_URL',pit,'images/08-cliv1-pitfall.png'),
     ('没有 Docker：Lambda 能建、不能跑',a['6'],'images/09-lambda.png'),
     ('持久化：默认重启清空，persistent 模式保留',b['7'],'images/10-persist.png'),
     ('启动钩子 ready.d：自动建好桶和队列',b['8'],'images/11-hooks.png')]
    asyncio.run(shot(items))
