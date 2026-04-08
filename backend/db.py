from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId
import uuid
from datetime import datetime

load_dotenv()

class InMemoryCollection:
    """In-memory collection fallback for development"""
    def __init__(self):
        self.data = {}
        self.counter = 1
    
    def find_one(self, query):
        if '_id' in query and isinstance(query['_id'], ObjectId):
            # Convert ObjectId to string for comparison
            query = query.copy()
            query['_id'] = str(query['_id'])
        
        for doc_id, doc in self.data.items():
            match = True
            for key, value in query.items():
                if key not in doc:
                    match = False
                    break
                # Handle ObjectId comparison
                if key == '_id':
                    if isinstance(value, ObjectId):
                        if str(doc[key]) != str(value):
                            match = False
                            break
                    elif doc[key] != value:
                        match = False
                        break
                elif doc[key] != value:
                    match = False
                    break
            if match:
                return doc
        return None
    
    def insert_one(self, document):
        doc_id = str(self.counter)
        document['_id'] = doc_id
        self.data[doc_id] = document.copy()
        self.counter += 1
        
        class MockResult:
            def __init__(self, doc_id):
                self.inserted_id = doc_id
        
        return MockResult(doc_id)
    
    def find(self, query=None, projection=None):
        """Find multiple documents with optional query and projection"""
        if query is None:
            query = {}
        
        results = []
        for doc_id, doc in self.data.items():
            match = True
            for key, value in query.items():
                if key not in doc:
                    match = False
                    break
                # Handle ObjectId comparison
                if key == '_id':
                    if isinstance(value, ObjectId):
                        if str(doc[key]) != str(value):
                            match = False
                            break
                    elif doc[key] != value:
                        match = False
                        break
                elif doc[key] != value:
                    match = False
                    break
            
            if match:
                result_doc = doc.copy()
                # Apply projection
                if projection:
                    if '_id' in projection and projection['_id'] == 0:
                        if '_id' in result_doc:
                            del result_doc['_id']
                    elif 'user_id' in projection and projection['user_id'] == 0:
                        if 'user_id' in result_doc:
                            del result_doc['user_id']
                
                results.append(result_doc)
        
        class MockCursor:
            def __init__(self, documents):
                self.documents = documents
            
            def sort(self, key, direction=1):
                if isinstance(key, str):
                    self.documents.sort(key=lambda x: x.get(key, ''), reverse=(direction == -1))
                return self
            
            def limit(self, count):
                self.documents = self.documents[:count]
                return self
            
            def __iter__(self):
                return iter(self.documents)
        
        return MockCursor(results)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        try:
            # Enhanced MongoDB Atlas connection with better SSL handling
            self.client = MongoClient(
                os.getenv('MONGODB_URI'),
                ssl=True,
                tlsAllowInvalidCertificates=False,
                retryWrites=True,
                w='majority',
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=15000,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                retryReads=True
            )
            
            # Test the connection
            self.db = self.client.plant_disease_db
            self.db.command('ping')
            print("✅ Connected to MongoDB Atlas successfully")
            
        except Exception as e:
            print(f"❌ MongoDB Atlas connection failed: {e}")
            
            # Try alternative connection method
            try:
                self.client = MongoClient(
                    os.getenv('MONGODB_URI'),
                    ssl=True,
                    tlsAllowInvalidCertificates=True,
                    serverSelectionTimeoutMS=5000
                )
                self.db = self.client.plant_disease_db
                print("⚠️ Connected to MongoDB Atlas with invalid certificates")
                
            except Exception as e2:
                print(f"❌ Alternative Atlas connection failed: {e2}")
                
                # Final fallback to local MongoDB
                try:
                    self.client = MongoClient('mongodb://localhost:27017/')
                    self.db = self.client.plant_disease_db
                    print("🔄 Fallback: Connected to local MongoDB")
                except Exception as local_e:
                    print(f"❌ Local MongoDB failed: {local_e}")
                    print("💾 Using in-memory storage")
                    self.db = None
    
    def get_collection(self, collection_name):
        if self.db is None:
            # In-memory fallback for development
            return InMemoryCollection()
        return self.db[collection_name]
    
    def close(self):
        if self.client:
            self.client.close()

db = Database()