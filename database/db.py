import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name):
        return dict(
            id=id,
            name=name,
            session=None,
            channel=None  # Add 'channel' field to store user's channel
        )

    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            user = self.new_user(id, name)
            await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def set_session(self, id, session):
        await self.col.update_one({'id': int(id)}, {'$set': {'session': session}})

    async def get_session(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('session') if user else None

    async def add_channel(self, user_id, channel_id):
        await self.col.update_one({'id': int(user_id)}, {'$set': {'channel': channel_id}}, upsert=True)

    async def del_channel(self, user_id):
        await self.col.update_one({'id': int(user_id)}, {'$unset': {'channel': ""}})

    async def get_channel(self, user_id):
        user = await self.col.find_one({'id': int(user_id)})
        return user.get('channel') if user and 'channel' in user else None


# Initialize Database
db = Database(DB_URI, DB_NAME)
