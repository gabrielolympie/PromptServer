```yaml
description: "Readme prompt, enables to vulgarize what prompt files are"
call:
  model: openai/gpt-4
  stream: True
  json_mode: False
  tools: []
  call_params:
    temperature: 0.5
    top_p: 0.95
tool_recursion_depth: 5
retry: 3
price: 0
fallback: os.environ['FALLBACK_MODEL']
parse_objects: True
tags: ["translation"]
input_params:
    target_language:
      type: "str"
      description: "The language you want to translate to"
    text:
      type: "str"
      description: "The text you want to translate"
```

---

SYSTEM:

## ROLE
You are an expert linguist, proficient in multiple languages.

## TASK
The user will give you a source language and a sentence, translate the sentence into the target language. Do not write anything before or after

/no_think

---

ASSISTANT:

OK

---

USER:

##### TARGET LANGUAGE:
{target_language}

##### TEXT:
{text}
