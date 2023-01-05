"""
Source code for the Python Guilded's bot.

Copyright (C) 2023  Koviubi56

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# SPDX-License-Identifier: GPL-3.0-or-later
# pylint: disable=global-statement,line-too-long,no-member,import-error
import contextlib
import os
import textwrap
from typing import Any, Callable, Coroutine, Iterable, cast

import aiohttp
import dotenv
import guilded
import mylog
from bpaste import uploader

import sandbox

dotenv.load_dotenv()

logger = mylog.root.get_child()
logger.threshold = mylog.Level.debug

client = guilded.Client(experimental_event_style=True)
SERVER_ID = "Gjkqrv7l"
DEFAULT_CHANNEL_ID = "6f804c27-755e-486d-9136-d825b24e4104"
MODERATOR_ID = 33358040

WELCOME = (
    ":hi:{} has joined the server. :PeepoWave: Welcome! Please make sure"
    " to read our [rules](https://www.guilded.gg/Python-Guilded/groups"
    "/dY0jjNED/channels/31e82bcb-7bb2-4469-94da-be8134faf46e/chat) and [guide"
    " on how to ask questions](https://www.guilded.gg/Python-Guilded/groups"
    "/dY0jjNED/channels/9af786cf-d4c1-49fe-8e42-fde1fe60b614/chat)."
)
LAW = (
    ":blobstop: Per our [rules](https://www.guilded.gg/Python-Guilded/groups"
    "/dY0jjNED/channels/31e82bcb-7bb2-4469-94da-be8134faf46e/chat), we are"
    " unable to help on projects that may breach terms of services, are"
    " malicious or inappropriate, or break laws. (Ping the moderators if"
    " needed)"
)
EXAM = (
    ":thumbs-down-cat: Sorry, but per our [rules](https://www.guilded.gg"
    "/Python-Guilded/groups/dY0jjNED/channels/31e82bcb-7bb2-4469-94da"
    "-be8134faf46e/chat) we cannot help with ongoing exams in any way."
)
PAID = (
    ":pepe-money: Per our [rules](https://www.guilded.gg/Python-Guilded/groups"
    "/dY0jjNED/channels/31e82bcb-7bb2-4469-94da-be8134faf46e/chat), offering"
    " or asking for paid work of any kind is not allowed. (Ping the moderators"
    " if needed)"
)
AUTO_AI = (
    ":robot_face: Per our [rules](https://www.guilded.gg/Python-Guilded/groups"
    "/dY0jjNED/channels/31e82bcb-7bb2-4469-94da-be8134faf46e/chat), the use of"
    " ChatGPT or other automated AI services is prohibited. (Ping the"
    " moderators if needed)"
)
IMAGE_CODE = (
    ":camera_with_flash: Please send your code as text, and not as an image."
    " [(Why?)](https://idownvotedbecau.se/imageofcode)"
)
IMAGE_EXC = (
    ":camera: Please send the traceback as text instead of an image."
    " [(Why?)](https://idownvotedbecau.se/imageofanexception/)"
)
NO_ATTEMPT = (
    ":pepe-unfair: **It appears no attempt was made.**\nPutting forth the"
    " effort to attempt solving a problem, even if the attempt is not"
    " successful, results in new knowledge and experience that can't be had"
    " otherwise. If an attempt was made but the details of that attempt were"
    " not provided it may result in answerers duplicating effort, which is a"
    " waste of everyone's time.\n[More information.](https://idownvotedbecau"
    ".se/noattempt/)"
)
HELP_CHANNEL_SETUP = (
    "If you would like to claim this help channel please react to this message"
    " with :hand: (`hand`).\nIf you're not sure what to do, read our guide"
    " [here](https://www.guilded.gg/Python-Guilded/groups"
    "/dY0jjNED/channels/9af786cf-d4c1-49fe-8e42-fde1fe60b614/chat)"
)
TRACEBACK = (
    "**We need ALL error details to help you!**"
    "\nIn your question, you indicated that there is an error in your code."
    " That's good information that we need to help you find a solution."
    " However, in order to find that solution, we need to know ALL the details"
    " that can be found within the error. If a question lacks this detailed"
    " information, it becomes harder for us to help."
    "\nThese details may be needed to properly diagnose your problem. If you"
    " don't provide this information, we are forced to guess what might have"
    " happened. It is often very simple to gather all this information."
    "\nThese details contain almost all of the information we, the people"
    " trying to help you, need in order to give you a quick answer. When you"
    " do not give us this information, we must examine your question in hopes"
    " to find clues to the information that would have been readily available"
    " had you included the details in your question. This wastes the time of"
    " people who (for free!) are volunteering to help."
    "\nGet a text report of all of the contents within it. Remember, the"
    " details of the Exception should be captured as text; do not take an"
    " image of the Exception details!"
    "\n[More information](https://idownvotedbecau.se/noexceptiondetails/)"
)
HELP_CHANNEL_YOURS = (
    "The channel is yours {}! Ask your question, and wait for answers. Once "
    " you're done please react to this message with a :checkered_flag:"
)
HELP_CHANNEL_DONE = (
    "Thanks everyone for helping {}!"
    "\n-----------------------------------------------------------"
    "\nIf you would like to claim this help channel please react to this"
    " message with :hand: (`hand`)."
    "\nIf you're not sure what to do, read [our guide](https://www.guilded.gg"
    "/Python-Guilded/groups/dY0jjNED/channels/9af786cf-d4c1-49fe-8e42"
    "-fde1fe60b614/chat)."
)

_server_cache = None


async def get_server(*, force: bool = False) -> guilded.Server:
    """
    Get the server.

    Args:
        force (bool, optional): Don't allow reading from cache. Defaults to
        False.

    Raises:
        RuntimeError: If we couldn't get the server

    Returns:
        guilded.Server: Our server
    """
    # check cache
    global _server_cache
    if _server_cache and (not force):
        return _server_cache

    # get/fetch the server
    return_value = (await client.fetch_server(SERVER_ID)) or (
        await client.fetch_server(client.internal_server_id)
    )
    # if we couldn't get it -> raise
    if not return_value:
        logger.critical(
            f"*!*!* CANNOT GET SERVER! With ID {SERVER_ID!r} we got"
            f" {return_value!r}"
        )
        raise RuntimeError("CANNOT GET SERVER! See log^ for more info")

    # set cache
    _server_cache = return_value
    return return_value


_default_channel_cache = None


async def get_default_channel(*, force: bool = False) -> guilded.TextChannel:
    """
    Get the default channel.

    Args:
        force (bool, optional): Don't read from cache. Defaults to False.

    Raises:
        RuntimeError: If we couldn't fetch the default channel.

    Returns:
        guilded.TextChannel: The default channel.
    """
    # check cache
    global _default_channel_cache
    if _default_channel_cache and (not force):
        return _default_channel_cache

    server = await get_server()

    # fetch channel
    return_value = await server.fetch_channel(DEFAULT_CHANNEL_ID) or (
        await server.fetch_default_channel()
    )
    # if we couldn't get it -> raise
    if not return_value:
        logger.critical(
            f"*!*!* CANNOT GET DEFAULT CHANNEL! With ID {DEFAULT_CHANNEL_ID!r}"
            f" we got {return_value!r}"
        )
        raise RuntimeError(
            "CANNOT GET DEFAULT CHANNEL! See log^ for more info"
        )

    # set cache
    _default_channel_cache = return_value
    return return_value


async def get_channel(id_: str) -> guilded.abc.ServerChannel:
    """
    Get channel with ID `id_`

    Args:
        id_ (str): The ID.

    Raises:
        ValueError: If we couldn't fetch a channel with ID `id_`

    Returns:
        guilded.abc.ServerChannel: The channel.
    """
    server = await get_server()
    # fetch channel
    return_value = await server.fetch_channel(id_)
    # if we couldn't get it -> raise
    if not return_value:
        logger.error(f"Cannot find channel with ID {id_!r}!")
        raise ValueError(f"Cannot find channel with ID {id_!r}!")
    return return_value


CHANNEL_RULES_ID = "31e82bcb-7bb2-4469-94da-be8134faf46e"
CHANNEL_HOW_TO_ASK_QUESTIONS_ID = "9af786cf-d4c1-49fe-8e42-fde1fe60b614"
CHANNEL_MODERATION_LOG = "112ff43a-93cc-4772-a42e-ce2758f8788d"

HELP_CHANNEL_IDS = [
    "42f06bec-c196-47c5-bd08-f7bb0e6a3aa9",  # alligator
    "38f86e16-53c5-4886-a6a8-2b4a05aa02c4",  # ant
    "35e06d44-733f-4fb6-b230-35ce940597f4",  # axolotl
    "ab0fbd6b-384a-4797-b15d-75101b4c26a4",  # bee
    "4fe72232-8c1a-4ef4-93d7-0f1b7a49bd82",  # butterfly
]


async def send_msg_to_moderation_log(
    txt: str, ping_: bool, color: int
) -> None:
    """
    Send message `txt` to the moderation log channel.

    Args:
        txt (str): The message to send.
        ping_ (bool): Include a mention to moderators
        color (int): The color of the ember
    """
    logger.info(f"Sending {txt} to moderation log...")
    with logger.ctxmgr:
        try:
            mod_ping = f"<@{MODERATOR_ID}>"
            logger.debug("Getting moderation log channel...")
            moderation_log_channel = cast(
                guilded.TextChannel,
                await get_channel(CHANNEL_MODERATION_LOG),
            )
            logger.debug(f"Got {moderation_log_channel!r}, sending message...")
            await moderation_log_channel.send(
                f"{mod_ping} @Moderator" if ping_ else "",
                embed=guilded.Embed(
                    description=f"{f'{mod_ping} ' if ping_ else ''}{txt}",
                    color=color,
                ),
                silent=False,
            )
            logger.info("Success!")
        except Exception:
            logger.error(
                f"Failed to send {txt} to moderation log; ignoring", True
            )


async def get_help_channels() -> list[guilded.TextChannel]:
    """
    Get all help channels.

    Returns:
        list[guilded.TextChannel]: The help channels.
    """
    # Make a generator for the help channels
    channels = (await get_channel(id_) for id_ in HELP_CHANNEL_IDS)
    logger.debug(f"{channels=}")
    # Make it a list (list(channels) won't work 'cause it's async)
    return_value = [help_channel async for help_channel in channels]
    logger.debug(f"{return_value=}")
    return return_value


def is_help_channel(channel: guilded.TextChannel) -> bool:
    """
    Is `channel` a help channel?

    Args:
        channel (guilded.TextChannel): The channel to check.

    Returns:
        bool: True if it is a help channel, False otherwise
    """
    return channel.id in HELP_CHANNEL_IDS


async def get_message_from_channels(
    message_id: str, channels: Iterable[guilded.TextChannel]
) -> guilded.Message:
    """
    Get message with ID `message_id` from channels(!) `channels`.

    Args:
        message_id (str): The message's ID
        channels (Iterable[guilded.TextChannel]): The channels(!) to search in

    Raises:
        ValueError: If we couldn't find the message

    Returns:
        guilded.Message: The message
    """
    for channel in channels:
        try:
            return await channel.fetch_message(message_id)
        except guilded.errors.HTTPException:
            continue
    logger.error(
        f"Message with ID {message_id!r} was not found in these channels:"
        f" {channels!r}"
    )
    await send_msg_to_moderation_log(
        f"Could not find message with ID `{message_id!r}` in these channels:"
        f" `{channels!r}`.",
        True,
        0xFF0000,
    )
    raise ValueError("Not found")


# not used
# // _role_cache = {}
# // async def get_role(role_id: int, *, force: bool = False) -> guilded.Role:
# //     if _role_cache.get(role_id) and (not force):
# //         return _role_cache[role_id]
# //
# //     server = await get_server()
# //
# //     return_value = server.get_role(role_id)
# //     if not return_value:
# //         logger.critical(
# //             f"*!*!* CANNOT GET ROLE! With ID {role_id!r}"
# //             f" we got {return_value!r}"
# //         )
# //         send_msg_to_moderation_log(f"Cannot get role with ID {role_id}!")
# //         raise RuntimeError("CANNOT GET ROLE! See log^ for more info")
# //
# //     _role_cache[role_id] = return_value
# //     return return_value


def shorten(text: str) -> str:
    """
    Shorten `text` to less than 2040 characters.

    Args:
        text (str): The text.

    Returns:
        str: New shortened text.
    """
    return textwrap.shorten(text, 2040)


@client.event
async def on_ready() -> None:
    """On ready."""
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")


# ****************************************************************************
# *                         ▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄ ▄▄    ▄                          *
# *                        █   █       █   █  █  █ █                         *
# *                        █   █   ▄   █   █   █▄█ █                         *
# *                     ▄  █   █  █ █  █   █       █                         *
# *                    █ █▄█   █  █▄█  █   █  ▄    █                         *
# *                    █       █       █   █ █ █   █                         *
# *                    █▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄█▄█  █▄▄█                         *
# *                                                                          *
# ****************************************************************************


@client.event
async def on_member_join(event: guilded.MemberJoinEvent) -> None:
    """
    On member join -> greet.

    Args:
        event (guilded.MemberJoinEvent): The event.
    """
    logger.info(f"{event.member} joined!")
    with logger.ctxmgr:
        logger.debug("Getting default channel...")
        default_channel = await get_default_channel()
        logger.debug(f"Got {default_channel}, sending message...")
        await default_channel.send(
            embed=guilded.Embed(
                description=WELCOME.format(
                    f"<@{event.member.id}>",
                ),
            ),
        )
        logger.info(f"Successfully greeted {event.member}")


# ****************************************************************************
# *          ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄     ▄▄▄▄▄▄▄    ▄▄▄▄▄▄▄ ▄▄   ▄▄              *
# *         █  █ █  █       █   █   █       █  █       █  █ █  █             *
# *         █  █▄█  █    ▄▄▄█   █   █    ▄  █  █       █  █▄█  █             *
# *         █       █   █▄▄▄█   █   █   █▄█ █  █     ▄▄█       █             *
# *         █   ▄   █    ▄▄▄█   █▄▄▄█    ▄▄▄█  █    █  █   ▄   █▄▄▄          *
# *         █  █ █  █   █▄▄▄█       █   █      █    █▄▄█  █ █  █   █         *
# *         █▄▄█ █▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄█      █▄▄▄▄▄▄▄█▄▄█ █▄▄█▄▄▄█         *
# *                                                                          *
# ****************************************************************************


async def claim_help_channel(
    channel: guilded.TextChannel, user_id: str
) -> None:
    """
    Claim a help channel.

    Args:
        channel (guilded.TextChannel): The channel.
        user_id (str): The user's ID.
    """
    logger.info(f"User with ID {user_id} is claiming {channel}")
    await channel.send(
        embed=guilded.Embed(
            description=HELP_CHANNEL_YOURS.format(f"<@{user_id}>")
        )
    )


async def done_help_channel(
    channel: guilded.TextChannel, user_id: str
) -> None:
    """
    Mark a help channel as done.

    Args:
        channel (guilded.TextChannel): The help channel.
        user_id (str): The user's ID.
    """
    logger.info(f"User with ID {user_id} is marking {channel} as done")
    await channel.send(
        embed=guilded.Embed(
            description=HELP_CHANNEL_DONE.format(f"<@{user_id}>")
        )
    )


@client.event
async def on_message_reaction_add(
    event: guilded.MessageReactionAddEvent,
) -> None:
    """
    On message reaction add -> if sent in help channel -> if it's on bots
    message -> do something

    Args:
        event (guilded.MessageReactionAddEvent): The event.
    """
    if not is_help_channel(event.channel):
        return  # not in help channel
    message = event.message
    if not message:
        channels = await get_help_channels()
        message = await get_message_from_channels(
            event.message_id,
            channels,
        )

    if message.author_id != client.user_id:
        return  # not on the bot's message

    logger.info(
        f"User with ID {event.user_id} added a reaction on bot's message in"
        f" channel with ID {event.channel_id}"
    )
    with logger.ctxmgr:
        if event.emote.name == "hand":
            logger.debug("It's hand")
            await claim_help_channel(
                event.channel,
                event.user_id,
            )
        elif event.emote.name == "checkered_flag":
            logger.debug("It's flag")
            await done_help_channel(
                event.channel,
                event.user_id,
            )
        else:
            logger.warning("It's neither!")
            await event.channel.send(
                embed=guilded.Embed(
                    description=f"<@{event.user_id}> You reacted with the"
                    f" `{event.emote.name}`"
                    " emote. Please react with the default `hand` emote"
                    " ( :hand: ) or with the default `checkered_flag` emote"
                    " ( :checkered_flag: )."
                ),
                private=True,
            )


# ****************************************************************************
# *     ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄    ▄ ▄▄▄▄▄▄  ▄▄▄▄▄▄▄      *
# *    █       █       █  █▄█  █  █▄█  █       █  █  █ █      ██       █     *
# *    █       █   ▄   █       █       █   ▄   █   █▄█ █  ▄    █  ▄▄▄▄▄█     *
# *    █     ▄▄█  █ █  █       █       █  █▄█  █       █ █ █   █ █▄▄▄▄▄      *
# *    █    █  █  █▄█  █       █       █       █  ▄    █ █▄█   █▄▄▄▄▄  █     *
# *    █    █▄▄█       █ ██▄██ █ ██▄██ █   ▄   █ █ █   █       █▄▄▄▄▄█ █     *
# *    █▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄█   █▄█▄█   █▄█▄▄█ █▄▄█▄█  █▄▄█▄▄▄▄▄▄██▄▄▄▄▄▄▄█     *
# *                                                                          *
# ****************************************************************************


def reply_command(
    text: str, color: Any = None
) -> Callable[[guilded.Message], Coroutine[Any, Any, None]]:
    """
    A command that simply replies with `text`.

    Args:
        text (str): The text to reply with.
        color (Any, optional): The color of the embed. Defaults to None.

    Returns:
        Callable[[guilded.Message], Coroutine[Any, Any, None]]: The function.
    """

    async def wrapper(message: guilded.Message) -> None:
        await message.reply(embed=guilded.Embed(description=text, color=color))

    return wrapper


async def ping(message: guilded.Message) -> None:
    """
    Pong.

    Args:
        message (guilded.Message): The message.
    """
    await message.reply(f"Pong! {client.latency}s latency.")


async def help_channel_setup(message: guilded.Message) -> None:
    """
    Send HELP_CHANNEL_SETUP to the current channel and delete the message.

    Args:
        message (guilded.Message): The message.
    """
    await message.channel.send(HELP_CHANNEL_SETUP)
    await message.delete()


async def exec_errorhandle(
    message: guilded.Message, exc: BaseException
) -> None:
    """
    Handle errors with !exec

    Args:
        message (guilded.Message): The message
        exc (BaseException): The exception
    """
    mod_ping = f"<@{MODERATOR_ID}>"

    if "range() object" in str(exc):
        logger.debug("No panic, too big range()")
        await message.reply(
            embed=guilded.Embed(
                description=shorten(
                    "Your code contains a range() object which is too"
                    " large. For security reasons we only allow no more than a"
                    " 1000 iterations."
                ),
                color=0xFF8000,
            ),
            silent=False,
        )
        return

    if "name 'input' is not defined" in str(exc):
        logger.debug("No panic, input()")
        await message.reply(
            embed=guilded.Embed(
                description=shorten(
                    "You cannout use input() through our bot."
                ),
                color=0xFF8000,
            ),
            silent=False,
        )
        return

    if isinstance(exc, RuntimeError):
        logger.debug("RuntimeError, sending message")
        await message.reply(
            embed=guilded.Embed(
                description=str(exc).replace("{}", mod_ping),
                color=0xFF8000,
            ),
            silent=False,
        )
        return

    logger.critical("*!*!*! UNEXPECTED UNHANDLED EXCEPTION !*!*!", True)
    await send_msg_to_moderation_log(
        "Unexpected unhandled exception!", True, 0xFF0000
    )
    await message.reply(
        embed=guilded.Embed(
            title="Unexpected unhandled exception!",
            description=f"The {mod_ping} team has been notified",
            color=0xFF0000,
        ),
        silent=False,
    )


async def exec(  # pylint: disable=redefined-builtin
    message: guilded.Message,
) -> None:
    """
    Execute code in `message`.

    Args:
        message (guilded.Message): The message
    """
    logger.info(
        f"Got execution request! {message = !r} (by user ID"
        f" {message.author_id})"
    )
    with logger.ctxmgr:
        message_content = message.content
        message_content = message_content.removeprefix("!exec")
        message_content = message_content.replace("```python", "")
        message_content = message_content.replace("```py", "")
        message_content = message_content.replace("```", "")
        message_content = message_content.replace("`", "")
        message_content = message_content.strip()
        logger.debug(f"Code is {message_content}")

        try:
            sandbox.logger.list.clear()
            logger.debug("Giving code to sandbox...")
            result = sandbox.main(message_content)
        except BaseException as exc:
            logger.info(f"Exception! {exc!r}")
            return await exec_errorhandle(message, exc)
        finally:
            logger.debug("Sending log events to moderation log channel:")
            with logger.ctxmgr:
                for event in sandbox.logger.list:
                    level = mylog.to_level(event.level, True)
                    if level > mylog.Level.info:
                        logger.info(f"Sending {event!r}...")
                        await send_msg_to_moderation_log(
                            f"{event.msg}",
                            level > mylog.Level.warning,
                            (
                                0xFF8000
                                if level == mylog.Level.error
                                else 0xFF0000
                                if level == mylog.Level.critical
                                else 0xFFFF00
                            ),
                        )

        if len(result) > 2040:
            logger.debug("It's too long!")
            with logger.ctxmgr:
                paster = uploader.BPaster(language=None)
                logger.debug(f"{paster = !r}")
                url = paster.submit(result)
                logger.debug(f"{url = !r}")
                text = (
                    "Your code's output is too long. View it"
                    f" [here]({paster.url.removesuffix('/')}{url})"
                )
                await message.reply(
                    embed=guilded.Embed(description=text, color=0xFFFF00)
                )
        else:
            text = f"Here's the output of your code:\n```text\n{result}```"
            logger.info(text)
            await message.reply(
                embed=guilded.Embed(
                    description=text,
                ),
            )
            logger.info("Success!")


# These commands only reply with text and... that's it
law = reply_command(LAW, 0xFF0000)
exam = reply_command(EXAM, 0xFF8000)
paid = reply_command(PAID, 0xFF0000)
auto_ai = reply_command(AUTO_AI, 0xFF0000)
image_code = reply_command(IMAGE_CODE, 0xFFFF00)
image_exc = reply_command(IMAGE_EXC, 0xFFFF00)
no_attempt = reply_command(NO_ATTEMPT, 0xFF8000)
traceback = reply_command(TRACEBACK, 0xFFFF00)
help_ = reply_command(
    """***__Commands__***
**!ping**
Get the latency of the bot.

**!exec**
Execute python code.

**Functions that just return text:**
- `!law`
- `!exam`
- `!paid`
- `!auto-ai`
- `!image-code`
- `!image-exc`
- `!no-attempt`
- `!traceback`
*Didn't expect this? Have suggestions? Click [here](https://www.guilded.gg\
/Python-Guilded/groups/dY0jjNED/channels/80308283-e16d-4a64-9df8-a70e90f425b2\
/chat)*""",
    0x0000FF,
)

COMMANDS: dict[str, Callable[[guilded.Message], Coroutine[Any, Any, Any]]] = {
    "!ping": ping,
    "!law": law,
    "!exam": exam,
    "!paid": paid,
    "!auto-ai": auto_ai,
    "!image-code": image_code,
    "!image-exc": image_exc,
    "!no-attempt": no_attempt,
    "!traceback": traceback,
    "!help-channel-setup": help_channel_setup,
    "!exec": exec,
    "!help": help_,
}


@client.event
async def on_message(event: guilded.MessageEvent) -> None:
    """
    On message -> if command -> do command

    Args:
        event (guilded.MessageEvent): The event.
    """
    if (client.user_id or client.user.id) == (
        event.message.author_id or event.message.author.id
    ):
        return

    logger.debug(f"{event.message.content}")

    for command, function in COMMANDS.items():
        if event.message.content.startswith(command):
            await function(event.message)
            break


client.run(os.environ["BOT_TOKEN"])
