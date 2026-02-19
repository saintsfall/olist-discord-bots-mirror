from typing import Final
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# DISCORD IMPORTS
from discord import Intents
from discord.ext import commands

# MODULES IMPORTS
from bot_events import handle_events
from bot_commands import handle_questions

# STEP 0: LOAD OUR DISCORD TOKEN FROM A SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

# Define o caminho do log na raiz do projeto
project_root = Path(__file__).parent
log_file_path = project_root / 'discord.log'

handler = logging.FileHandler(
    filename=str(log_file_path), encoding='utf-8', mode='a')

# STEP 1: BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
intents.members = True  # NOQA
bot: commands.Bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None  # Desabilita comando help padrão
)

# STEP 2: SETUP EVENTS AND COMMANDS
handle_events.set_events(bot, log_file_path=log_file_path)
handle_questions.set_commands(bot)

# STEP 3: MAIN ENTRY POINT


def main() -> None:
    bot.run(token=TOKEN, log_handler=handler, log_level=logging.DEBUG)


if __name__ == '__main__':
    main()
