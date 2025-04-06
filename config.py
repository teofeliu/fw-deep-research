# Configuration settings
DEFAULT_CONFIG = {
    "models": {
        "scout": {
            "model_id": "accounts/fireworks/models/llama4-scout-instruct-basic",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "maverick": {
            "model_id": "accounts/fireworks/models/llama4-maverick-instruct-basic",
            "temperature": 0.7,
            "max_tokens": 2048
        }
    },
    "max_search_results": 10,
    "max_content_length": 15000,  # Characters per page to process
    "default_depth": 3,
    "default_breadth": 3
}