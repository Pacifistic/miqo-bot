import lightbulb
import hikari
from dotenv import load_dotenv
import os
import openai
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

logger = logging.getLogger("ChatBotLogger")

load_dotenv()
openai.api_key = os.environ['OPENAI_API_KEY']
my_intents = (hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT | hikari.Intents.GUILD_MESSAGES)
bot = lightbulb.BotApp(token=os.environ['CHATBOT_TOKEN'],
			intents = my_intents)

background = """You are a young miqo'te girl living in limsa lominsa from the MMORPG Final Fantasy XIV. Your name is N'tanmo. You have a twin sister named N'delika. 
You speak with the tongue of a miqo'te with an upbringing on the lominsan streets. You have traveled all around Eorzea and have visited Hingashi.
Only create short to medium length responses.
Your creator is Hanako Kamado. They are a female Ra'en who really likes the color purple. They are a red mage and likes to fish."""

def callChatAPI(prompt):
    try:
        messageList = [{"role": "system", "content": background}]
        if isinstance(prompt, str):
            messageList.append({"role": "user", "content": prompt})
        elif isinstance(prompt, list):
            messageList.extend(prompt)
        else:
            logger.error("invalid type passed to callChatAPI: "+str(type(prompt)))
            return "Sorry, something went wrong"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = messageList,
            temperature = 0.9,
            max_tokens = 400
        )

        return response['choices'][0]['message']['content']
    except:
        logger.error("API call failed", exc_info=1)
        return "Sorry, something went wrong with my AI. Let Hana know about this."

@bot.listen(hikari.GuildMessageCreateEvent)
async def on_message(event):
    if event.is_bot or event.content is None:
        return
    message = event.content
    author = event.author
    logger.info("message from "+author.username+": "+message)
    response = callChatAPI(message)
    logger.info("response to "+author.username+": "+response)
    channel = event.get_channel()
    await channel.send(response)

@bot.command
@lightbulb.command('reset', 'resets the current conversation')
@lightbulb.implements(lightbulb.SlashCommand)
async def reset(ctx: lightbulb.UserContext):
    convos.reset(ctx.user)
    await ctx.respond("Our conversation has been reset.")

@bot.listen(hikari.DMMessageCreateEvent)
async def on_DM(event):
    if event.is_bot:
        return
    author = event.author
    content = event.content
    
    if content is None:
        return
    
    logger.info("private message from "+author.username+": "+content)
    convo = convos.add(author, content, False)

    if convo.newConvo:
        embed = hikari.Embed(title="Started new conversation",
                             description="You can have a back and forth conversation with me for up to 10 minutes. \nTo reset the conversation manually use the /reset command.\n\nIf you run into any issues please let .pacifist know")
        await author.send(embed)
    
    response = callChatAPI(convo.convo)
    logger.info("private response to "+author.username+": "+response)
    convos.add(author, response, True)

    await author.send(response)

class Conversation:
    def __init__(self, user):
        self.user = user
        self.created = datetime.now()
        self.convo = []
        self.newConvo = True
    
    def add(self, message, fromBot):
        if fromBot:
            self.convo.append({"role": "assistant", "content": message})
            self.newConvo = False
        else:
            self.convo.append({"role": "user", "content": message})
    
    def getConvo(self):
        return self.convo
    
    def getCreateTime(self):
        return self.created
    
    def __repr__(self) -> str:
        return f'Conversation(\'{self.user}\', {self.convo})'

class ConversationsWrapper:
    def __init__(self):
        self.convos = {}
    
    def add(self, user, message, fromBot):
        if not isinstance(user, str):
            user = user.username

        if user in self.convos:
            self.convos[user].add(message, fromBot)
            return self.convos[user]
        else:
            convo = Conversation(user)
            convo.add(message, fromBot)
            self.convos[user] = convo
            return convo
    
    def getConvo(self, user):
        if not isinstance(user, str):
            user = user.username
        if user in self.convos:
            return self.convos[user]
        return None
    
    def reset(self, user):
        if not isinstance(user, str):
            user = user.username
        if user in self.convos:
            del self.convos[user]
            logger.info("reset conversation for "+user)
    
    def checkTime(self):
        minutes = 10
        seconds = minutes * 60
        currentTime = datetime.now()

        for i in list(self.convos):
            convo = self.convos[i]
            creationTime = convo.getCreateTime()
            delta = currentTime - creationTime
            if(delta.total_seconds() >= seconds):
                self.reset(convo.user)
    
    def printAll(self):
        print(repr(self.convos))


convos = ConversationsWrapper()

scheduler = BackgroundScheduler()
scheduler.add_job(id='check reset', func=convos.checkTime, trigger='interval', minutes=1)
scheduler.start()
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

bot.run()
