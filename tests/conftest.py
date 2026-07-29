import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ["GITHUB_TOKEN"] = ""
os.environ["GITHUB_REPO"] = ""
os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = ""
os.environ["LINE_CHANNEL_SECRET"] = ""
os.environ["ACTIVE_TEXT_MODEL_PROVIDER"] = "mock"
os.environ["ACTIVE_EMBEDDING_PROVIDER"] = "mock"
os.environ["STORAGE_PROVIDER"] = "local"
