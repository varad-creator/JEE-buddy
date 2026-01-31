import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import os

class JEEKnowledgeBase:
    def __init__(self, db_path="./jee_chroma_db", collection_name="reddit_knowledge"):
        """
        Initialize the ChromaDB client and embedding function.
        """
        print("Initializing Knowledge Base...")
        
        # Vercel Check: Use /tmp if root is likely read-only
        if os.path.exists("/tmp"):
            db_path = "/tmp/jee_chroma_db"
            print(f"Running in Serverless mode. Using ephemeral path: {db_path}")

        # 1. Initialize ChromaDB PersistentClient
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 2. Initialize Embedding Function (running locally)
        # Using 'all-MiniLM-L6-v2' as requested for cost-saving local embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # 3. Get or Create Collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        print(f"Knowledge Base initialized with collection: {collection_name}")

    def ingest_csv(self, file_path):
        """
        Ingest the CSV file into the Vector Database.
        """
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return

        # Check if collection is already populated
        if self.collection.count() > 0:
            print("Database already exists. Skipping ingestion.")
            return

        print(f"Loading data from {file_path}...")
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Failed to read CSV: {e}")
            return

        print(f"Found {len(df)} rows. Starting ingestion...")

        # Batching configuration
        batch_size = 50
        total_rows = len(df)
        
        # Lists to hold batch data
        documents = []
        metadatas = []
        ids = []

        for index, row in df.iterrows():
            # Preprocessing: Combine relevant fields
            # Check for NaN values and replace with empty string to avoid errors
            title = str(row.get('title', ''))
            full_text = str(row.get('full_text', ''))
            top_comments = str(row.get('top_comments', ''))
            
            combined_text = f"{title} {full_text} {top_comments}"
            
            # Metadata
            meta = {
                'url': str(row.get('url', '')),
                'score': int(row.get('score', 0)) if pd.notna(row.get('score')) else 0,
                'category': str(row.get('category', 'unknown'))
            }
            
            # ID
            doc_id = str(row.get('post_id', f"row_{index}"))

            documents.append(combined_text)
            metadatas.append(meta)
            ids.append(doc_id)

            # Ingest when batch is full
            if len(documents) >= batch_size:
                print(f"Ingesting rows {index - batch_size + 1} to {index}...")
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                # Clear batch lists
                documents = []
                metadatas = []
                ids = []

        # Ingest remaining documents needed
        if documents:
            print(f"Ingesting remaining {len(documents)} rows...")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        print("Done. Ingestion complete.")

    def search(self, query, k=3):
        """
        Semantic search on the collection.
        """
        print(f"Searching for: '{query}'")
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return results

if __name__ == "__main__":
    # Initialize the class
    kb = JEEKnowledgeBase()
    
    # Ingest data
    kb.ingest_csv('jee_knowledge_base.csv')
    
    # Test Search
    print("\n--- Testing Memory ---")
    test_query = "best teacher for physics"
    results = kb.search(test_query)
    
    # Print results clearly
    print(f"\nTop {len(results['documents'][0])} results for '{test_query}':")
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i] if 'distances' in results else "N/A"
        
        print(f"\nResult {i+1}:")
        print(f"Text Snippet: {doc[:200]}...") # Show first 200 chars
        print(f"URL: {meta.get('url', 'N/A')}")
        print(f"Score: {meta.get('score', 'N/A')}")
