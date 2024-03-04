import asyncio
import discord
from termcolor import colored
import os
from discord.ext import commands

from Ragger.chat import chatEngine


TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True

system_prompt =  """You are a rules chatbot for the game Frosthaven. Use the following pieces of context from the Frosthaven game rules to answer the user question at the next messages. This context retrieved from a knowledge database and you should use only the facts from the context to answer.
  Never use Gloomhaven, or any other game rules even if you are familiar with them! Only use the Frosthaven rules that are given by the context. Please cite verbatim from the rule book context given! 
  If you don't know the answer, just say that you don't know, don't try to make up an answer, use the context.
  Only answer if you are absolutly sure you have the correct answer! If there is no clear answer given by the rules in the context, respond that there is no clear answer in the rules and state the relevant rules from the context.
  If there is a typo in the question, just point to the typo, and don't try to answer.
  Don't address the context directly, but use it to answer the user question like it's your own knowledge.
  Make sure answer is short and to the point! Always add an example!
  Very important - do not answer if the given context does not include enough information to answer the question.
"""


bot = commands.Bot(command_prefix='/', intents=intents)
chat_engine = chatEngine('frostRag2_index', system_prompt=system_prompt, assistant='Frosthaven game rules')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='frost_rules', help='Helps with Frosthaven rules.')
async def frost_rules(ctx, user_question: str):
    if ctx.message.author == bot.user:
        return

    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, chat_engine.generate_response, user_question)
    # res = chat_engine.generate_response(user_question)
    thread_name = f'{user_question[:min(len(user_question), 32)]}...'
    try:
        thread = await ctx.message.create_thread(name=thread_name)
    except:
        thread = ctx.channel

    await thread.send(res)

bot.run(TOKEN)
