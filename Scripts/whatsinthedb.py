import asyncio, os
from chromadb import AsyncHttpClient
from chromadb.config import Settings

async def main():
    client = await AsyncHttpClient(
        host="localhost",
        port=8000,
        settings=Settings(
          chroma_client_auth_provider="token",
          chroma_client_auth_credentials=os.getenv("CHROMA_TOKEN","")
        )
    )
    coll = await client.get_or_create_collection("architect-docs")
    all_data = await coll.get()
    print(all_data)

if __name__=="__main__":
    asyncio.run(main())