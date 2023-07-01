import motor.motor_asyncio
from vars import DB_NAME, DB_URI
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DB:
    """
    A class to manage user informations saved on MongoDb database using motor.motor_asyncio

    Args:
        uri: The uri of the MongoDb database
        db_name: The name of the database to connect

    Attributes:
        client: The motor client object to connect to MongoDb
        db: The mongodb database object
        usr: The collection of users

    © github.com/Joelkb or telegram.me/creatorbeatz
    """

    def __init__(self, uri, db_name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.usr = self.db.users
    
    async def new_user(self, id, name, username):
        user = dict(
            id = int(id),
            name = name,
            username = username,
            fetched = 0,
            last_msg_id = 0,
            source_chat = None,
            target_chat = None,
            on_process = False,
            is_complete = True,
            is_banned = False
        )
        await self.usr.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.usr.find_one({'id': int(id)})
        if user:
            return True
        else:
            return False
        
    async def ban_user(self, id):
        await self.usr.update_one({'id': int(id)}, {'$set': {'is_banned': True}})

    async def unban_user(self, id):
        await self.usr.update_one({'id': int(id)}, {'$set': {'is_banned': False}})

    async def pop_user(self, id):
        await self.usr.delete_many({'id': int(id)})

    def get_all_users(self):
        return self.usr.find({})
    
    async def get_user(self, id):
        return self.usr.find_one({'id': int(id)})
    
    async def count_users(self):
        total = await self.usr.count_documents({})
        return total
    
    async def update_any(self, id, key, value):
        await self.usr.update_one({'id': int(id)}, {'$set': {key: value}})

    async def get_forwarding(self):
        users = await self.usr.find({'on_process': True}).to_list(length=None)
        return users

db = DB(DB_URI, DB_NAME)