from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from urllib.parse import quote_plus

# # Your MongoDB credentials
# username = "abel12"  # Replace with your actual username
# password = "Appillil@2024"  # Replace with your actual password

# # URL encode the username and password
# encoded_username = quote_plus(username)
# encoded_password = quote_plus(password)

MONGO_URI = f"mongodb+srv://saviosunny48:2TJsNwpNwqJX2aG3@cluster0.0zmwv1l.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URI)  # Replace with MongoDB URI
db = client["HireSmart"]
users_collection = db["Signup"]
result_collection=db["Results"]
