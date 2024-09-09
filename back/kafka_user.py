from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import logging
import hashlib
import uuid

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka 설정
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'user'

class KafkaUserManager:
    def __init__(self):
        self.users = {}
        self.producer = None
        self.consumer = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        self.consumer = AIOKafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await self.producer.start()
        await self.consumer.start()
        await self.load_users()

    async def stop(self):
        await self.producer.stop()
        await self.consumer.stop()

    async def load_users(self):
        try:
            async for msg in self.consumer:
                user_data = json.loads(msg.value)
                self.users[user_data['username']] = user_data
        except Exception as e:
            logger.error(f"Error loading users: {e}")

    def hash_password(self, password: str):
        return hashlib.sha256(password.encode()).hexdigest()

    async def register_user(self, username: str, password: str):
        if username in self.users:
            return False, "Username already exists"
        
        user_data = {
            "username": username,
            "password": self.hash_password(password),
            "id": str(uuid.uuid4())
        }
        
        try:
            await self.producer.send_and_wait(KAFKA_TOPIC, json.dumps(user_data).encode())
            self.users[username] = user_data
            return True, "User registered successfully"
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, "Error registering user"

    def login_user(self, username: str, password: str):
        if username not in self.users or self.users[username]["password"] != self.hash_password(password):
            return False, "Invalid username or password"
        return True, self.users[username]["id"]

kafka_user_manager = KafkaUserManager()