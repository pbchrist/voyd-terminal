import json, re, sys

schema = json.load(open('story_room/schemas/cold_walk.schema.json'))
required = schema['required']

def extract_json(text):
    # Find the first { that starts the JSON object
    start = text.find('{"path"')
    if start == -1:
        start = text.find('{\n  "path"')
    if start == -1:
        start = text.find('{"path":')
    if start == -1:
        return None
    # Find the matching closing brace
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == '\\' and in_str:
            escape = True
            continue
        if c == '"' and not escape:
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

files = {
    'walk1-antiquarian': '/home/patrick/.hermes/cache/delegation/subagent-summary-0-20260909_030507_042435.txt',
    'walk2-temple': '/home/patrick/.hermes/cache/delegation/subagent-summary-0-20260909_030656_173433.txt',
    'walk3-stray': '/home/patrick/.hermes/cache/delegation/subagent-summary-0-20260909_030812_051519.txt',
}

for name, path in files.items():
    text = open(path).read()
    raw = extract_json(text)
    if raw is None:
        print(f"{name}: FAILED to extract JSON")
        continue
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"{name}: JSON parse error: {e}")
        continue
    # Validate against schema
    errors = []
    for key in required:
        if key not in data:
            errors.append(f"missing required key: {key}")
        elif not isinstance(data[key], list):
            errors.append(f"key {key} is not a list")
        elif len(data[key]) == 0:
            errors.append(f"key {key} is empty")
        else:
            for item in data[key]:
                if not isinstance(item, str):
                    errors.append(f"key {key} has non-string item: {repr(item)[:50]}")
    extra = set(data.keys()) - set(required)
    if extra:
        errors.append(f"unexpected keys: {extra}")
    if errors:
        print(f"{name}: SCHEMA VIOLATIONS: {errors}")
    else:
        print(f"{name}: VALID (path has {len(data['path'])} scenes)")
        # Save to reports
        out = f'story_room/reports/20260909T100000Z/cold/{name}.json'
        with open(out, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  saved to {out}")
