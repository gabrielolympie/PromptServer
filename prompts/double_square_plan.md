```yaml
description: "Simple tool use demonstrator with planning"
call:
  model: os.environ['GENERAL_PURPOSE_MODEL']
  stream: True
  json_mode: False
  tools:
    - llm_planner
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

Your task is to compute the power four of a number provided by the user, using all the tools at your disposal

First call the tool planner.

Hint: you can call the square function twice.

---

MESSAGES:
{history}

---

USER:
{number}
