```yaml
description: "Simple tool use demonstrator with structured output"
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

First call the square tool to get result,

Then structure your answer as yaml:
```yaml
input: the input
output: the output
rational: reasoning or tool used to find the result
```

Then, after that, write down a short description of what as been done, in full text.

Remember to begin by performing a tool call, answer only after

---

MESSAGES:
{history}

---

USER:
{number}
