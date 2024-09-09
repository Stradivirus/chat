import os
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import logging
import hashlib
import uuid

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka 설정
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka-service:9092')
KAFKA_TOPIC = 'user'

logger.info(f"Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")  # 디버깅을 위한 로그 추가

class KafkaUserManager:
    def __init__(self):
        self.users = {}
        self.producer = None
        self.consumer = None

    async def start(self):
        logger.info("Starting KafkaUserManager...")
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        self.consumer = AIOKafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await self.producer.start()
        await self.consumer.start()
        logger.info("Kafka producer and consumer started successfully.")
        await self.load_users()

    async def stop(self):
        logger.info("Stopping KafkaUserManager...")
        await self.producer.stop()
        await self.consumer.stop()
        logger.info("Kafka producer and consumer stopped successfully.")

    async def load_users(self):
        logger.info("Loading users from Kafka...")
        try:
            async for msg in self.consumer:
                user_data = json.loads(msg.value)
                self.users[user_data['username']] = user_data
            logger.info(f"Loaded {len(self.users)} users from Kafka.")
        except Exception as e:
            logger.error(f"Error loading users: {e}")

    def hash_password(self, password: str):
        return hashlib.sha256(password.encode()).hexdigest()

    async def register_user(self, username: str, password: str):
        if username in self.users:
            logger.warning(f"Attempted to register existing username: {username}")
            return False, "Username already exists"
        
        user_data = {
            "username": username,
            "password": self.hash_password(password),
            "id": str(uuid.uuid4())
        }
        
        try:
            await self.producer.send_and_wait(KAFKA_TOPIC, json.dumps(user_data).encode())
            self.users[username] = user_data
            logger.info(f"User registered successfully: {username}")
            return True, "User registered successfully"
        except Exception as e:
            logger.error(f"Error registering user {username}: {e}")
            return False, "Error registering user"

    def login_user(self, username: str, password: str):
        if username not in self.users or self.users[username]["password"] != self.hash_password(password):
            logger.warning(f"Failed login attempt for username: {username}")
            return False, "Invalid username or password"
        logger.info(f"Successful login for username: {username}")
        return True, self.users[username]["id"]

kafka_user_manager = KafkaUserManager()