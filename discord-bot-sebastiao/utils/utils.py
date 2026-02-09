from discord import Message
from random import choice, randint

def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()

    if lowered == '':
        return 'Not the talkative type, I imagine...'
    elif 'hello' in lowered:
        return 'Hello there!'
    elif 'roll dice' in lowered:
        return f'You\'ve rolled: {randint(1, 6)}'
    else:
        return choice([
            'I do not understand...',
            'What are you talking about?',
            'Do you mind rephrasing that?'
        ])

async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('(Message empty, probably due to intents problems)')
        return

    # Checks if the user is trying to get a private message using '?' at the start of the message
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)