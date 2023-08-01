import asyncio
import hashlib
import json
import random
import re
import time
import uuid
from typing import List, Union, AsyncGenerator, Optional

import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger

from .util import (
    HOME_URL,
    GQL_URL,
    GQL_RECV_URL,
    SETTING_URL,
    CONST_NAMESPACE,
    generate_data,
    QUERIES,
    generate_nonce,
    extract_formkey,
)


class Poe_Client:
    def __init__(
        self, p_b: str, formkey: Optional[str] = "", proxy: Optional[str] = ""
    ):
        self.channel_url: str = ""
        self.bots: dict = {}
        self.bot_list_url: str = ""
        self.formkey: str = formkey
        self.home_bot_list: List[str] = []
        self.next_data: dict = {}
        self.p_b: str = p_b
        self.sdid: str = ""
        self.subscription: dict = {}
        self.tchannel_data: dict = {}
        self.user_id: str = ""
        self.viewer: dict = {}
        self.ws_domain = f"tch{random.randint(1, int(1e6))}"[:8]
        self.proxy = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": f"p-b={self.p_b}",
            "poe-formkey": self.formkey,
            "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="112"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Upgrade-Insecure-Requests": "1",
        }

    @property
    def session_args(self):
        args = {
            "headers": self.headers,
            "cookies": {"p-b": self.p_b},
        }
        if self.proxy:
            connector = ProxyConnector.from_url(self.proxy)
            args["connector"] = connector
        return args

    async def get_basedata(self) -> None:
        """
        This function fetches the basic data from the HOME_URL and sets various attributes of the object.

        Raises:
            Raises an Exception if it fails to get the base data.
            Raises a ValueError if it fails to extract 'next_data', 'viewer', 'user_id', or 'formkey' from the response.
        """
        try:
            async with aiohttp.ClientSession(**self.session_args) as client:
                response = await client.get(HOME_URL, timeout=8)
                text = await response.text()
        except Exception as e:
            raise Exception("Failed to get basedata from home.") from e
        """extract next_data from html"""
        try:
            """get next_data"""
            json_regex = (
                r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
            )
            json_text = re.search(json_regex, text).group(1)
            self.next_data = json.loads(json_text)
        except Exception as e:
            raise ValueError("Failed to extract 'next_data' from the response.") from e

        """extract data from next_data"""
        try:
            self.bot_list_url = (
                f'https://poe.com/_next/data/{self.next_data["buildId"]}/index.json'
            )
            self.viewer = self.next_data["props"]["pageProps"]["data"]["viewer"]
            self.user_id = self.viewer["poeUser"]["id"]
            self.subscription = self.viewer["subscription"]
            bot_list = self.viewer["availableBotsConnection"]["edges"]
            for bot in bot_list:
                self.home_bot_list.append(bot["node"]["handle"])
            self.sdid = str(uuid.uuid5(CONST_NAMESPACE, self.viewer["poeUser"]["id"]))
        except KeyError as e:
            raise ValueError(
                "Failed to extract 'viewer' or 'user_id' from 'next_data'."
            ) from e

    async def get_channel_data(self) -> None:
        """
        This function fetches the channel data from the SETTING_URL and sets the 'tchanneldata' attribute of the object.

        Raises:
            Raises a ValueError if it fails to extract the channel data from the response.
        """
        try:
            async with aiohttp.ClientSession(**self.session_args) as client:
                response = await client.get(SETTING_URL)
                data = await response.text()
                json_data = json.loads(data)
                self.tchannel_data = json_data["tchannelData"]
                self.headers["Poe-Tchannel"] = self.tchannel_data["channel"]
                self.channel_url = f'https://{self.ws_domain}.tch.{self.tchannel_data["baseHost"]}/up/{self.tchannel_data["boxName"]}/updates?min_seq={self.tchannel_data["minSeq"]}&channel={self.tchannel_data["channel"]}&hash={self.tchannel_data["channelHash"]}'
        except Exception as e:
            raise ValueError("Failed to extract tchannel from response.") from e

    async def create(self):
        """
        This function initializes the Async_Poe_Client instance by fetching the base data, channel data, and bot data,
        and then subscribing to the channel.

        Returns:
            Returns the initialized instance of the Async_Poe_Client.

        Note:
            This function should be called after creating a new Async_Poe_Client instance to ensure that all necessary data is fetched and set up.
        """
        retry = 2
        while retry >= 0:
            try:
                await self.get_basedata()
                break
            except Exception as e:
                retry -= 1
                if retry == 0:
                    raise e
        await self.get_bots()
        logger.info("Succeed to create async_poe_client instance")
        return self

    async def get_botdata(self, url_botname: str) -> dict:
        """
        This function gets the chat data of the bot from the specified URL.

        Args:
            url_botname (str): The name of the bot used in the URL to fetch the bot's chat data.

        Returns:
            Returns the chat data of the bot.

        Raises:
            Raises a ValueError exception if it fails to get the chat data.
        """
        url = (
            f'https://poe.com/_next/data/{self.next_data["buildId"]}/{url_botname}.json'
        )
        retry = 2
        error = Exception("Unknown error")
        while retry > 0:
            try:
                async with aiohttp.ClientSession(**self.session_args) as client:
                    response = await client.get(url, timeout=8)
                    data = await response.text()  # noqa: E501
                    json_data = json.loads(data)
                    chat_data = json_data["pageProps"]["data"]["chatOfBotHandle"]
                    return chat_data
            except Exception as e:
                error = e
                retry -= 1
        raise ValueError(f"Failed to get bot chat_data from {url}") from error

    async def get_bot_info(self, url_botname: str) -> dict:
        """
        This function gets the bot's information from the specified URL.

        Args:
            url_botname (str): The name of the bot used in the URL to fetch the bot's information.

        Returns:
            Returns a dictionary containing the bot's information.

        Raises:
            Raises a ValueError exception if it fails to get the bot's info.
        """
        url = f'https://poe.com/_next/data/{self.next_data["buildId"]}/edit_bot.json?bot={url_botname}'
        try:
            async with aiohttp.ClientSession(**self.session_args) as client:
                response = await client.get(url, timeout=3)
                data = await response.text()
                bot_info = json.loads(data)
                return bot_info["pageProps"]
        except Exception as e:
            raise ValueError(
                f"Failed to get bot info from {url}. Make sure the bot is not deleted"
            ) from e

    async def save_botdata(self, url_botname: str) -> None:
        """
        This function saves the bot's chat data for later use.

        Args:
            url_botname (str): The name of the bot used in the URL to fetch the bot's chat data.

        Note:
            The function does not return anything.
        """
        chat_data = await self.get_botdata(url_botname)
        # here url_botname equals nickname
        self.bots[url_botname] = chat_data

    async def get_bots(self) -> None:
        """
        This function fetches and saves the chat data of all available bots on home page.

        Raises:
            Raises a RuntimeError exception if it fails to get any bots, or if the token is invalid.
        """

        if "availableBotsConnection" not in self.viewer:
            raise RuntimeError(
                "Failed to get_bots: Invalid token or no bots are available."
            )

        tasks = []
        for bot in self.home_bot_list:
            task = asyncio.create_task(self.save_botdata(bot))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def send_query(self, query_name: str, variables: dict) -> Union[dict, None]:
        """
        A general-purpose function used to send queries to a server. This function is primarily used by other functions in the program.

        Args:
            query_name (str): The name of the query that should be sent.
            variables (dict): A dictionary of the variables that should be included in the message.

        Returns:
            Returns the JSON response data from the server if the query is successful. If the query_name is "recv", it doesn't return anything.

        Raises:
            Raises an Exception if the query fails after 5 retries.
        """

        data = generate_data(query_name, variables)
        base_string = data + self.formkey + "Jb1hi3fg1MxZpzYfy"
        query_headers = {
            **self.headers,
            "content-type": "application/json",
            "poe-tag-id": hashlib.md5(base_string.encode()).hexdigest(),
        }
        retry = 2
        detail_error = Exception("unknown error")
        while retry:
            try:
                async with aiohttp.ClientSession(**self.session_args) as client:
                    if query_name == "recv":
                        await client.post(
                            GQL_RECV_URL, headers=query_headers, data=data
                        )
                        return None
                    else:
                        response = await client.post(
                            GQL_URL, data=data, headers=query_headers
                        )
                    data = await response.text()
                    json_data = json.loads(data)
                    if (
                        "success" in json_data.keys()
                        and not json_data["success"]
                        or json_data["data"] is None
                    ):
                        detail_error = Exception(json_data["errors"][0]["message"])
                        raise detail_error
                    return json_data
            except Exception as e:
                detail_error = e
                logger.error(
                    f"Failed to sending query:{query_name},error:{detail_error}. (retry: {retry}/5)"
                )
                retry -= 1
        raise Exception(
            f"Too much error when sending query:{query_name},error:{detail_error}"
        ) from detail_error

    async def subscribe(self):
        """
        This function is used to simulate a human user opening the website by subscribing to certain mutations.

        Raises:
            Raises an Exception if it encounters a failure while sending the SubscriptionsMutation.
        """
        try:
            await self.send_query(
                "SubscriptionsMutation",
                {
                    "subscriptions": [
                        {
                            "subscriptionName": "messageAdded",
                            "query": QUERIES["MessageAddedSubscription"],
                        },
                        {
                            "subscriptionName": "viewerStateUpdated",
                            "query": QUERIES["ViewerStateUpdatedSubscription"],
                        },
                    ]
                },
            )
            logger.info("Succeed to subscribe")
        except Exception as e:
            raise Exception(
                "Failed to subscribe by sending SubscriptionsMutation"
            ) from e

    async def create_bot(
        self,
        handle: str,
        prompt: str,
        display_name: Optional[str] = None,
        base_model: str = "chinchilla",
        description: Optional[str] = "",
        intro_message: Optional[str] = "",
        api_key: Optional[str] = None,
        api_bot: Optional[bool] = False,
        api_url: Optional[str] = None,
        prompt_public: Optional[bool] = True,
        profile_picture_url: Optional[str] = None,
        linkification: Optional[bool] = False,
        markdown_rendering: Optional[bool] = True,
        suggested_replies: Optional[bool] = True,
        private: Optional[bool] = False,
        temperature: Optional[int] = None,
    ) -> None:
        """
        This function is used to create a new bot with the specified configuration.

        Args:
            handle (str): The handle for the new bot which should be unique.
            prompt (str): The prompt for the new bot.
            display_name (str, optional): The display name for the new bot. If not provided, it will be set to None.
            base_model (str, optional): The base model for the new bot. Default is "chinchilla".
            description (str, optional): The description for the new bot. If not provided, it will be set to an empty string.
            intro_message (str, optional): The introduction message for the new bot. If not provided, it will be set to an empty string.
            api_key (str, optional): The API key for the new bot. If not provided, it will be set to None.
            api_bot (bool, optional): Whether the new bot is an API bot. Default is False.
            api_url (str, optional): The API URL for the new bot. If not provided, it will be set to None.
            prompt_public (bool, optional): Whether to set the bot's prompt to public. Default is True.
            profile_picture_url (str, optional): The profile picture URL for the new bot. If not provided, it will be set to None.
            linkification (bool, optional): Whether to enable linkification. Default is False.
            markdown_rendering (bool, optional): Whether to enable markdown rendering. Default is True.
            suggested_replies (bool, optional): Whether to enable suggested replies. Default is False.
            private (bool, optional): Whether to set the bot as private. Default is False.
            temperature (int, optional): The temperature setting for the new bot. If not provided, it will be set to None.

        Returns:
            Returns a dictionary containing information about the creation result.

        Raises:
            Raises a RuntimeError exception if the creation fails.

        Note:
            When creating a new bot, you only need to provide the `handle` and `prompt`. All other parameters are optional and will be set to their default values if not provided.
            Please ensure that the `handle` is unique and does not conflict with the handles of existing bots.
        """
        result = await self.send_query(
            "PoeBotCreateMutation",
            {
                "model": base_model,
                "displayName": display_name,
                "handle": handle,
                "prompt": prompt,
                "isPromptPublic": prompt_public,
                "introduction": intro_message,
                "description": description,
                "profilePictureUrl": profile_picture_url,
                "apiUrl": api_url,
                "apiKey": api_key,
                "isApiBot": api_bot,
                "hasLinkification": linkification,
                "hasMarkdownRendering": markdown_rendering,
                "hasSuggestedReplies": suggested_replies,
                "isPrivateBot": private,
                "temperature": temperature,
            },
        )

        data = result["data"]["poeBotCreate"]
        if data["status"] != "success":
            raise RuntimeError(f"Failed to create a bot with error: {data['status']}")
        # after creating, get the chatId (bot chat_data contains chatId) for using
        # when creating bot,the url_botname equals handle
        logger.info(f"Succeed to create a bot:{handle}")
        await self.save_botdata(url_botname=handle)
        return

    async def edit_bot(
        self,
        url_botname: str,
        handle: str = None,
        prompt: Optional[str] = None,
        display_name=None,
        base_model="chinchilla",
        description="",
        intro_message="",
        api_key=None,
        api_url=None,
        is_private_bot=None,
        prompt_public=None,
        profile_picture_url=None,
        linkification=None,
        markdown_rendering=None,
        suggested_replies=None,
        temperature=None,
    ) -> None:
        """
        This function is used to edit the configuration of an existing bot.

        Args:
            url_botname (str): The URL name of the bot to be edited.
            handle (str, optional): The new handle for the bot. If not provided, it will remain unchanged.
            prompt (str, optional): The new prompt for the bot. If not provided, it will remain unchanged.
            display_name (str, optional): The new display name for the bot. If not provided, it will remain unchanged.
            base_model (str, optional): The new base model for the bot. If not provided, it will remain unchanged.
            description (str, optional): The new description for the bot. If not provided, it will remain unchanged.
            intro_message (str, optional): The new introduction message for the bot. If not provided, it will remain unchanged.
            api_key (str, optional): The new API key for the bot. If not provided, it will remain unchanged.
            api_url (str, optional): The new API URL for the bot. If not provided, it will remain unchanged.
            is_private_bot (bool, optional): Whether to set the bot to private. If not provided, it will remain unchanged.
            prompt_public (bool, optional): Whether to set the bot's prompt to public. If not provided, it will remain unchanged.
            profile_picture_url (str, optional): The new profile picture URL for the bot. If not provided, it will remain unchanged.
            linkification (bool, optional): Whether to enable linkification. If not provided, it will remain unchanged.
            markdown_rendering (bool, optional): Whether to enable markdown rendering. If not provided, it will remain unchanged.
            suggested_replies (bool, optional): Whether to enable suggested replies. If not provided, it will remain unchanged.
            temperature (float, optional): The new temperature setting for the bot. If not provided, it will remain unchanged.

        Returns:
            Returns a dictionary containing information about the edit result.

        Raises:
            Raises a RuntimeError exception if the edit fails.

        Note:
            The `url_botname` parameter is the original URL name of the bot that you want to edit. This is required to identify which bot's configuration you are targeting to change.
            All other parameters represent the new values you want to set for the bot's configuration. If a parameter is not provided, the corresponding configuration of the bot will remain unchanged.
        """
        botinfo = await self.get_bot_info(url_botname)
        botinfo = botinfo["data"]["bot"]

        result = await self.send_query(
            "PoeBotEditMutation",
            {
                "baseBot": base_model or botinfo["model"],
                "botId": botinfo["botId"],
                "handle": handle or botinfo["handle"],
                "displayName": display_name or botinfo["displayName"],
                "prompt": prompt or botinfo["promptPlaintext"],
                "isPromptPublic": prompt_public or botinfo["isPromptPublic"],
                "introduction": intro_message or botinfo["introduction"],
                "description": description or botinfo["description"],
                "profilePictureUrl": profile_picture_url or botinfo["profilePicture"],
                "apiUrl": api_url or botinfo["apiUrl"],
                "apiKey": api_key or botinfo["apiKey"],
                "hasLinkification": linkification or botinfo["hasLinkification"],
                "hasMarkdownRendering": markdown_rendering
                or botinfo["hasMarkdownRendering"],
                "hasSuggestedReplies": suggested_replies
                or botinfo["hasSuggestedReplies"],
                "isPrivateBot": is_private_bot or botinfo["isPrivateBot"],
                "temperature": temperature or botinfo["temperature"],
            },
        )

        data = result["data"]["poeBotEdit"]
        if data["status"] != "success":
            raise RuntimeError(f"Failed to create a bot: {data['status']}")
        logger.info(f"Succeed to edit {url_botname}")
        return data

    async def delete_bot(self, url_botname: str) -> None:
        """
        This function is used to edit the configuration of an existing bot.

        Args:
            url_botname (str): The URL name of the bot to be edited.

        Returns:
            Returns None.

        Raises:
            Raises a ValueError exception if error occurs when sending query or the status is not 'success'.

        Note:
            This function will delete the bot permanently, so caution.
        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)
        bot_id = self.bots[url_botname]["defaultBotObject"]["botId"]
        try:
            response = await self.send_query(
                "BotDeletionButton_poeBotDelete_Mutation", {"botId": bot_id}
            )
        except Exception:
            raise ValueError(
                f"Failed to delete bot {url_botname}. Make sure the bot exists!"
            )
        if response["data"] is None and response["errors"]:
            raise ValueError(
                f"Failed to delete bot {url_botname} :{response['errors'][0]['message']}"  # noqa: E501
            )
        logger.info(f"Succeed to delete bot {url_botname}")

    async def explore_bots(
        self, count: int = 50, explore_all: bool = False
    ) -> List[dict]:
        """
        Asynchronously explore and fetch a specified number of third party bots.

        Args:
            count (int, optional): The number of bots to explore. Defaults to 50.
            explore_all (bool, optional): Whether to explore all third party bots. Defaults to False
        Returns:
            List[dict]: A list of dictionaries representing the explored bots.
                        Each dictionary represents a bot and includes details
                        about the bot. If fewer bots are found than requested,
                        the function will return a list of the found bots.

        Raises:
            Any exceptions raised by `self.send_query()` will be propagated.
        """
        bots = []
        result = await self.send_query(
            "ExploreBotsListPaginationQuery",
            {
                "count": count,
            },
        )
        new_cursor = result["data"]["exploreBotsConnection"]["edges"][-1]["cursor"]
        bots += [
            each["node"] for each in result["data"]["exploreBotsConnection"]["edges"]
        ]
        if len(bots) >= count and not explore_all:
            return bots[:count]
        while len(bots) < count or explore_all:
            result = await self.send_query(
                "ExploreBotsListPaginationQuery", {"count": count, "cursor": new_cursor}
            )
            if len(result["data"]["exploreBotsConnection"]["edges"]) == 0:
                if not explore_all:
                    logger.error(
                        f"No more bots could be explored,only {len(bots)} bots found."
                    )
                return bots
            new_cursor = result["data"]["exploreBotsConnection"]["edges"][-1]["cursor"]
            new_bots = [
                each["node"]
                for each in result["data"]["exploreBotsConnection"]["edges"]
            ]
            bots += new_bots
        logger.info("Succeed to explore bots")
        return bots[:count]

    async def send_message(
        self, url_botname: str, question: str, with_chat_break: bool = False
    ) -> int:
        """
        Sends a message to a specified bot and retrieves the message ID of the sent message.

        Parameters:
            url_botname (str): The unique identifier of the bot to which the message is to be sent.
            question (str): The message to be sent to the bot.
            with_chat_break (bool, optional): If set to True, a chat break will be sent before the message, clearing the bot's conversation history. Default is False.

        Returns:
            int: The message ID of the sent message.

        Raises:
            Exception: If the daily limit for messages to the bot has been reached.
            RuntimeError: If there is an error in extracting the message ID from the response.

        Note:
            This function sends a message to the bot but does not retrieve the bot's response. The 'ask' or 'ask_stream' function should be used to send and retrieve the bot's response.

        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)
        handle = self.bots[url_botname]["defaultBotObject"]["nickname"]
        message_data = await self.send_query(
            "SendMessageMutation",
            {
                "bot": handle,
                "query": question,
                "chatId": self.bots[url_botname]["chatId"],
                "source": None,
                "clientNonce": generate_nonce(),
                "sdid": self.sdid,
                "withChatBreak": with_chat_break,
            },
        )
        if not message_data["data"]["messageEdgeCreate"]["message"]:
            if message_data["data"]["messageEdgeCreate"]["status"] == "no_access":
                raise Exception("The bot doesn't exist or isn't accessible")
            else:
                raise Exception(f"Daily limit reached for {url_botname}.")
        try:
            human_message = message_data["data"]["messageEdgeCreate"]["message"]
            human_message_id = human_message["node"]["messageId"]
            logger.info(f"Succeed to send message to {url_botname}")
            return human_message_id
        except TypeError:
            raise RuntimeError(
                "Failed to extract human_message and human_message_id from response when asking: Unknown Error"
            )

    async def send_recv(
        self,
        url_botname: str,
        last_text: str,
        bot_message_id: str,
        human_message_id: int,
    ) -> None:
        """
        A function to mimic the behavior of a human user interacting with a webpage.

        Parameters:
            url_botname (str): The unique identifier of the bot involved in the interaction.
            last_text (str): The last message text received from the bot.
            bot_message_id (str): The message ID of the last bot's message.
            human_message_id (str): The message ID of the last human's message.

        This function sends a 'recv' query with various parameters related to the timing and content of the bot's response. These parameters are used to simulate the kind of metadata a real user would generate when interacting with a webpage.

        Returns:
            None

        Note:
            The exact purpose and effect of this function might vary depending on the specifics of the system it is integrated with.
        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)
        handle = self.bots[url_botname]["defaultBotObject"]["nickname"]
        await self.send_query(
            "recv",
            {
                "bot": handle,
                "time_to_first_typing_indicator": 300,  # randomly select
                "time_to_first_subscription_response": 600,
                "time_to_full_bot_response": 1100,
                "full_response_length": len(last_text) + 1,
                "full_response_word_count": len(last_text.split(" ")) + 1,
                "human_message_id": human_message_id,
                "bot_message_id": bot_message_id,
                "chat_id": self.bots[url_botname]["chatId"],
                "bot_response_status": "success",
            },
        )

    async def ask(
        self,
        url_botname: str,
        question: str,
        with_chat_break: bool = False,
    ) -> str:
        """
        Sends a question to a specified bot and retrieves the bot's response via HTTP.

        Parameters:
            url_botname (str): The unique identifier of the bot to which the question is to be sent.
            question (str): The question to be sent to the bot.
            with_chat_break (bool, optional): If set to True, a chat break will be sent before the question, clearing the bot's conversation memory. Default is False.

        Returns:
            Union[str, dict]: The bot's response. This will be a string if 'plain' is True, else it will be a dictionary.

        Raises:
            ValueError: If there's a timeout or failure in receiving the message from the bot.

        Note:
            This function uses AIOHTTP to send and receive messages. It doesn't support streaming and is not recommended if 'ask_stream' can be used.

        """
        await self.subscribe()
        human_message_id = await self.send_message(
            url_botname, question, with_chat_break
        )
        retry = 2
        start_time = time.time()
        while retry > 0:
            try:
                await asyncio.sleep(0.5)
                data = await self.get_botdata(url_botname)
                messages = data["messagesConnection"]["edges"]
                if messages[-1]["node"]["messageId"] <= human_message_id:
                    retry -= 1
                    continue
                else:
                    now_time = time.time()
                    differ = now_time - start_time
                    if messages[-1]["node"]["text"]:
                        await self.send_recv(
                            url_botname,
                            messages[-1]["node"]["text"],
                            messages[-1]["node"]["messageId"],
                            human_message_id,
                        )
                        return messages[-1]["node"]["text"]
                    else:
                        if differ > 180:
                            raise ValueError(
                                f"Timed out while getting message from {url_botname}"
                            )
                        continue
            except Exception as e:
                logger.error(
                    f"Failed to getting message from {url_botname}, error:{str(e)}"
                )
        raise ValueError(f"Failed to getting message from {url_botname} too many times")

    async def ask_stream(
        self,
        url_botname: str,
        question: str,
        with_chat_break: bool = False,
        suggest_able: bool = True,
    ) -> AsyncGenerator:
        """
        Asynchronously sends a question to a specified bot and yields the bot's responses as they arrive.

        Args:
            url_botname (str): The unique identifier of the bot to which the question is to be sent.
            question (str): The question to be sent to the bot.
            with_chat_break (bool, optional): If set to True, a chat break will be sent before the question, clearing the bot's conversation memory. Default is False.
            suggest_able (bool, optional): If set to True, suggested replies from the bot will be included in the responses. Default is False.

        Returns:
            AsyncGenerator[str]: An asynchronous generator that yields the bot's responses as they arrive.

        Raises:
            Exception: If there is a failure in receiving messages from the bots.

        """
        async with aiohttp.ClientSession(**self.session_args) as client:
            await self.get_channel_data()
            await self.subscribe()
            retry = 2
            error = "Unknown error"
            while retry >= 0:
                if retry == 0:
                    raise error
                try:
                    human_message_id = await self.send_message(
                        url_botname, question, with_chat_break
                    )
                    break
                except Exception as e:
                    retry -= 1
                    error = e
                    pass
            last_text = ""
            yield_header = False
            suggestion_list = []
            self.bots[url_botname]["Suggestion"] = []
            retry = 2
            suggestion_lost = 10
            while retry >= 0:
                if retry == 0:
                    raise Exception(
                        "Failed to get answer form poe too many times:No Reply!"
                    )
                try:
                    response = await client.get(self.channel_url)
                    raw_data = await response.json()
                    if "messages" not in raw_data:
                        retry -= 1
                        await asyncio.sleep(1)
                        if retry == 0:
                            raise Exception(
                                "Failed to get answer form poe too many times:No Reply!"
                            )
                        continue
                    message = json.loads(raw_data["messages"][-1])["payload"]["data"][
                        "messageAdded"
                    ]
                    if message["messageId"] > human_message_id:
                        plain_text = message["text"][len(last_text) :]
                        last_text = message["text"]
                        if (
                            self.bots[url_botname]["defaultBotObject"][
                                "hasSuggestedReplies"
                            ]
                            and suggest_able
                        ):
                            if plain_text:
                                retry = 2
                                yield plain_text
                            elif message["state"] == "complete":
                                if len(message["suggestedReplies"]) == 0:
                                    suggestion_lost -= 1
                                    await asyncio.sleep(0.5)
                                    if suggestion_lost <= 0:
                                        logger.error(
                                            "Failed to get suggestions:Poe didn't send suggestions"
                                        )
                                        break
                                else:
                                    if len(message["suggestedReplies"]) == len(
                                        suggestion_list
                                    ):
                                        suggestion_lost -= 1
                                        await asyncio.sleep(0.5)
                                        if suggestion_lost <= 0:
                                            logger.error(
                                                "Failed to get enough suggestions:Poe didn't send suggestions"
                                            )
                                            break
                                    else:
                                        suggestion_lost = 10
                                    if not yield_header:
                                        yield_header = True
                                        yield "\n\nSuggested Reply:"
                                    for suggest in message["suggestedReplies"]:
                                        if suggest not in suggestion_list:
                                            yield f"\n{str(len(suggestion_list)+1)}:{suggest}"
                                            suggestion_list.append(suggest)
                                        self.bots[url_botname][
                                            "Suggestion"
                                        ] = suggestion_list
                                    if len(suggestion_list) >= 3:
                                        self.bots[url_botname][
                                            "Suggestion"
                                        ] = suggestion_list
                                        break
                            else:
                                retry -= 1
                                await asyncio.sleep(1)
                                continue
                        else:
                            if plain_text:
                                yield plain_text
                            if message["state"] == "complete":
                                break
                    else:
                        retry -= 1
                        await asyncio.sleep(1)
                        if retry == 0:
                            if retry == 0:
                                raise Exception(
                                    "Failed to get answer form poe too many times: No reply!"
                                )
                            continue
                except asyncio.exceptions.TimeoutError as e:
                    raise Exception(
                        f"Failed to get message from {url_botname}:{str(e)}"
                    ) from e
                except Exception as e:
                    raise Exception(
                        f"Failed to get message from {url_botname}:{str(e)}"
                    ) from e
            await self.send_recv(
                url_botname, last_text, message["messageId"], human_message_id
            )
            return

    async def send_chat_break(self, url_botname: str) -> None:
        """
        Asynchronously sends a chat break to a specified bot, effectively clearing the bot's conversation memory.

        Parameters:
            url_botname (str): The unique identifier of the bot to which the chat break is to be sent.

        Returns:
            None

        Note:
            This function clears the language model's conversation memory for the specified bot, so it should be used with caution.

        """
        if url_botname not in self.bots.keys():
            self.bots[url_botname] = await self.get_botdata(url_botname)
        await self.send_query(
            "AddMessageBreakMutation", {"chatId": self.bots[url_botname]["chatId"]}
        )
        logger.info(f"Succeed to chat break to {url_botname}")
        return

    async def delete_messages(self, message_ids: Union[list, int]):
        """
        Asynchronously deletes messages based on provided message IDs.

        Parameters:
            message_ids (Union[list, int]): A list of message IDs or a single message ID to be deleted.

        Returns:
            None

        Raises:
            TypeError: If 'message_ids' is neither a list nor an integer.

        Note:
            Be aware that this function will permanently delete messages based on provided IDs.

        """
        if isinstance(message_ids, int):
            message_ids = [int(message_ids)]

        await self.send_query("DeleteMessageMutation", {"messageIds": message_ids})
        logger.info(f"Succeed to deleting messages: {message_ids}")

    async def get_message_history(
        self, url_botname, count: Optional[int] = None, get_all: Optional[bool] = False
    ):
        """
        Asynchronously fetches the message history for a specified bot.

        Parameters:
            url_botname (str): The url name of the bot whose message history is to be fetched.
            count (int, optional): The number of most recent messages to fetch. If not provided, either 'get_all' must be set to True or else a TypeError will be raised.
            get_all (bool, optional): If set to True, all messages will be fetched. If not provided, either 'count' must be set or else a TypeError will be raised.

        Returns:
            list: A list of messages. If 'count' is provided, the list will contain the 'count' number of most recent messages. If 'get_all' is True, the list will contain all messages.

        Raises:
            TypeError: If neither 'count' nor 'get_all' are provided.
            ValueError: If the bot has no message history.

        """
        if url_botname not in self.bots.keys():
            await self.save_botdata(url_botname)
        if not (count or get_all):
            raise TypeError(
                "Please provide at least one of the following parameters: del_all=<bool>, count=<int>"
            )
        messages = self.bots[url_botname]["messagesConnection"]["edges"]
        if len(messages) == 0:
            logger.error(
                f"Failed to get message history of {url_botname}: No messages found with {url_botname}"
            )
            return []
        cursor = messages[0]["cursor"]
        if not get_all and count <= len(messages):
            return messages[-count:]
        while get_all or (count > len(messages)):
            result = await self.send_query(
                "ChatListPaginationQuery",
                {"count": 20, "cursor": cursor, "id": self.bots[url_botname]["id"]},
            )
            previous_messages = result["data"]["node"]["messagesConnection"]["edges"]
            messages = previous_messages + messages
            cursor = messages[0]["cursor"]
            if len(previous_messages) == 0:
                if not get_all:
                    logger.warning(
                        f"Only {str(len(messages))} history messages found with {url_botname}"
                    )
                break
        logger.info(f"Succeed to get messages from {url_botname}")
        if count:
            return messages[-count:]
        else:
            return messages

    async def delete_bot_conversation(
        self,
        url_botname: str,
        count: Optional[int] = None,
        del_all: Optional[bool] = False,
    ):
        """
        Deletes the conversation history with the specified bot.

        Args:
            url_botname (str): The url name of the bot to delete the conversation history for.
            count (int, optional): The number of messages to delete. If not provided, all messages will be deleted.
            del_all (bool, optional): Whether to delete all messages. If set to True, 'count' parameter will be ignored.

        Raises:
            TypeError: If neither 'del_all' nor 'count' parameter is provided.

        Returns:
            None
        """
        if del_all:
            arg = "all"
            messages = await self.get_message_history(url_botname, get_all=True)
        elif count:
            arg = str(count)
            messages = await self.get_message_history(url_botname, count=count)
        else:
            raise TypeError(
                "Please provide at least one of the following parameters: del_all=<bool>, count=<int>"
            )
        message_ids = [message["node"]["messageId"] for message in messages]
        await self.delete_messages(message_ids)
        logger.info(f"Succeed to delete {arg} messages with {url_botname}")

    async def get_available_bots(
        self, count: Optional[int] = 25, get_all: Optional[bool] = False
    ) -> List[dict]:  # noqa: E501
        """
        Get own available bots .

        Args:
            count (int, optional): The number of bots to get.
            get_all (bool, optional): Whether to get all bots.

        Raises:
            TypeError: If neither 'get_all' nor 'count' parameter is provided.

        Returns:
            None
        """
        if not (get_all or count):
            raise TypeError(
                "Please provide at least one of the following parameters: get_all=<bool>, count=<int>"
            )
        response = await self.send_query("availableBotsListModalPaginationQuery", {})
        bots = [
            each["node"]
            for each in response["data"]["viewer"]["availableBotsConnection"]["edges"]
            if each["node"]["deletionState"] == "not_deleted"
        ]
        cursor = response["data"]["viewer"]["availableBotsConnection"]["pageInfo"][
            "endCursor"
        ]
        if len(bots) >= count and not get_all:
            return bots[:count]
        while len(bots) < count or get_all:
            response = await self.send_query(
                "availableBotsListModalPaginationQuery", {"cursor": cursor}
            )
            new_bots = [
                each["node"]
                for each in response["data"]["viewer"]["availableBotsConnection"][
                    "edges"
                ]
                if each["node"]["deletionState"] == "not_deleted"
            ]
            cursor = response["data"]["viewer"]["availableBotsConnection"]["pageInfo"][
                "endCursor"
            ]
            bots += new_bots
            if len(new_bots) == 0:
                if not get_all:
                    logger.error(f"Only {len(bots)} bots found on this account")
                else:
                    logger.info("Succeed to get all available bots")
                return bots
        logger.info("Succeed to get available bots")
        return bots[:count]

    async def delete_available_bots(
        self, count: Optional[int] = 2, del_all: Optional[bool] = False
    ):
        """
        Asynchronously deletes some or all user available bots.

        Args:
            count (int, optional): The number of bots to delete.
            del_all (bool, optional): Whether to delete all bots.
        Raises:
            TypeError: If neither 'del_all' nor 'count' parameter is provided

        Returns:
            None

        Note:
            Be careful while using this function as it will permanently remove the bots.
            Delete all bots may take a long time depends on the num of your bots.
        """
        if not (del_all or count):
            raise TypeError(
                "Please provide at least one of the following parameters: del_all=<bool>, count=<int>"
            )
        bots = await self.get_available_bots(count, del_all)
        for bot in bots:
            if not bot["isSystemBot"]:
                try:
                    await self.delete_bot(bot["handle"])
                except Exception as e:
                    logger.error(
                        f"Failed to delete {bot['handle']} : {str(e)}. Make sure the bot belong to you."
                    )
            else:
                logger.info("Can't delete SystemBot, skipped")
        logger.info("Succeed to delete bots")

    async def delete_all_conversations(self):
        """
        Asynchronously deletes all user messages in the conversations.

        Returns:
            None

        Note:
            Be careful while using this function as it will permanently remove all conversations.

        """
        await self.send_query("DeleteUserMessagesMutation", {})
        logger.info("Succeed to delete all conversations")
