import os
import uvicorn

from app.config import settings

def main():
    # Only enable reload for local development, never in Docker
    reload = os.environ.get('DOCKER_ENV') != 'true'

    print(f"🚀 Starting FinBot backend...")
    print(f"   API Key present: {'✅' if settings.groq_api_key else '❌'}")
    print(f"   Reload enabled: {reload}")

    uvicorn.run(
        "app.main:app",
        port=8000,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()

