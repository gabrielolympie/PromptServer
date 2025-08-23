```yaml
description: "Just triggers a long generation"
call:
  model: openai/gpt-4
  stream: True
  json_mode: False
  tools: []
  call_params:
    temperature: 0.15
    max_tokens: 2048
tool_recursion_depth: 5
retry: 3
price: 10
fallback: os.environ['FALLBACK_MODEL']
parse_objects: True
tags: ["speed_bench"]
input_params:
    topic:
      type: "str"
      description: "Topic of the poem"
```

---

USER:

Write a very very long poem about {topic}.
Use at least 4096 words.
Never stop, dont discuss
