def find_by_key(data, target):
    for key, value in data.items():
        if key == target:
            return value
        elif isinstance(value, dict):
            find_by_key(value, target)
    return {}
