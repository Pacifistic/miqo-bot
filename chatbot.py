import lightbulb
import hikari
from dotenv import load_dotenv
import os
import openai
import logging

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

def callChatAPI(prompt:str):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = [
                {"role": "system", "content": background},
                {"role":"user", "content": prompt}
            ],
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
    

bot.run()
