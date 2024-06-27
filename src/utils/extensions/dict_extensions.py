

def deep_copy(obj: {}) -> {}:
    if isinstance(obj, dict):
        return {k: deep_copy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_copy(i) for i in obj]
    else:
        return obj