import discord
from discord.ext import commands
import config
import database
from utils import webserver
import asyncio
import os

class UltimateBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Requires "Server Members Intent" in Dev Portal
        intents.message_content = True # Requires "Message Content Intent" in Dev Portal
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Initialize Database
        await database.init_db()
        
        # Load Cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # Sync Slash Commands
        await self.tree.sync()
        print("Slash commands synced")

        # Persistent Views
        from cogs.drops import DropView
        from cogs.generator import GeneratorView
        self.add_view(DropView(self))
        self.add_view(GeneratorView(self))
        
        # Start Web Server
        self.loop.create_task(webserver.start_server())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

async def main():
    bot = UltimateBot()
    async with bot:
        await bot.start(config.TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle graceful shutdown
        pass
