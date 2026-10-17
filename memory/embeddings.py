from sentence_transformers import SentenceTransformer
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------
# Hugging Face token
# ---------------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN not found. Please add it to the .env file."
    )

# ---------------------------------------------------------
# Embedding model
# ---------------------------------------------------------

MODEL_NAME = "BAAI/bge-small-en-v1.5"

print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME,
    device="cpu",
    token=HF_TOKEN
)

print("Embedding model loaded.")


# ---------------------------------------------------------
# Create embedding
# ---------------------------------------------------------

def create_embedding(text):
    """
    Convert text into a numerical vector.
    """

    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    text = "I prefer Python for backend development."

    vector = create_embedding(text)

    print("\nText:")
    print(text)

    print("\nVector:")
    print(vector)

    print("\nVector dimensions:")
    print(len(vector))