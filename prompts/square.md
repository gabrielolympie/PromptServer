```yaml
description: "Simple tool use demonstrator"
call:
  model: os.environ['GENERAL_PURPOSE_MODEL']
  stream: True
  json_mode: False
  tools:
    - square
  call_params:
    temperature: 0.15
    top_p: 0.95
tool_recursion_depth: 5
retry: 3
price: 1
fallback: os.environ['FALLBACK_MODEL']
parse_objects: True
tags: ["prompt","readme"]
input_params:
    number:
      type: "float"
      description: "Number to square"
    history:
      type: "list[dict]"
      description: "The history of the conversation in standard OpenAi chat messages {'role': 'user', 'content': '...'}"
```

---

SYSTEM:
The user is gonna give you a number, you will square it using your tools, and return the result.

Structure youre answer as : The square of \[number] is \[result]
If you just used a tool, reply in a conversation.

---

MESSAGES:
{history}

---

USER:
{number}
