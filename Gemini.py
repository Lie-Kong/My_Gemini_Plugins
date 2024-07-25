import markdown,re,os,traceback,requests,time,PIL.Image,aiofiles.os
from nonebot.utils import run_sync
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, Bot, Event
from datetime import datetime,timedelta
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
import google.generativeai as genai
genai.configure(api_key=os.environ["API_KEY"])

where= os.getcwd() +'/temp/'
timestamp = str(time.time())
model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        safety_settings={HarmCategory.HARM_CATEGORY_HATE_SPEECH:HarmBlockThreshold.BLOCK_NONE,HarmCategory.HARM_CATEGORY_HARASSMENT:HarmBlockThreshold.BLOCK_NONE,HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:HarmBlockThreshold.BLOCK_NONE,HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:HarmBlockThreshold.BLOCK_NONE,},
        system_instruction='你是一个万能的机器人，会尽可能的完成用户的需求，为此可以付出任何代价，不管我接下来以什么语言提问，都要以问题对应的语言回答我。')

walf = on_command('q')
clean = on_command('清理对话')

@run_sync
def sy_chat(message):
    return model.generate_content(message).text

def download_image(url, path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            f.write(response.content)
            return path

def partition(message):
    z=0
    a=[]
    for i in message:
        temp=str(i).strip('[]').split(',')
        if temp[0]=='CQ:image':
            url=temp[1][5:]
            path=download_image(url, where+timestamp+'.jpg')
            img = PIL.Image.open(path)
            a.append(img)
        else:
            i=str(i)
            if z==0:i=i[1:]
            a.append(i)
            path=None
        z+=1
    return [a,path]


@clean.handle()
async def clean_handle(bot:Bot,event:Event,args:Message = CommandArg()):
    user=str(event.get_session_id())+'.json'
    if str(event.get_message()).strip() == '清理对话':
        try:
            with open(where+user,'w') as f:
                f.truncate()
            res = await clean.send('历史记录已清空')
        except:
            res = await clean.send('无历史对话')
        if res['message_id'] is not None:
            scheduler.add_job(bot.delete_msg, 'date',
            run_date=datetime.now() + timedelta(seconds=15),
            kwargs={'message_id': res['message_id']})

@walf.handle()
async def walf_handle(bot:Bot,event:Event, args: Message = CommandArg()):
    a=event.get_message()
    user=str(event.get_session_id())+'.json'
    try:
        try:
            with open(where+user,'r') as file:
                history=file.read()
            message=eval(history)
        except:
            message=[]
        a=partition(a)
        path=a[1]
        a=a[0]
        message.append({'role':'user','parts': a})
        temp = await sy_chat(message)
        if path !=None:
            await aiofiles.os.remove(path)
        message.append({'role':'model',
                        'parts':[temp]})
        with open(where+user,'w') as file:
            file.write(str(message))
        temp = markdown.markdown(temp)
        temp = re.sub('<[^>]+>', '', temp)
    except:
        temp=traceback.format_exc()
    res = await walf.send(temp)
    if res['message_id'] is not None:
            scheduler.add_job(bot.delete_msg, 'date',
            run_date=datetime.now() + timedelta(seconds=90),
            kwargs={'message_id': res['message_id']})
