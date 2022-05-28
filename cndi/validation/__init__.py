from cndi.env import walkDictKey, normalize

schema = {
    "type": "object",
    "properties": {
        "rcn": {
            "type": "object",
            "properties": {
                "profile": {"type": "string" },
                "binders": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "object"
                        }
                    }
                }
            }
        }
    }
}