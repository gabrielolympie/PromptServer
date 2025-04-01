```yaml
call:
  model: gemini-1.5-flash-8b
  stream: True
  json_mode: False
  tools: []
  call_params:
    temperature: 0.3
    top_p: 0.95
retry: 3
fallback: os.environ['FALLBACK_MODEL']
parse_objects: True
```

## PROMPTFILE

SYSTEM:
You are a helpful assistant

---

MESSAGES:

{history}

---

ASSISTANT:

OK

---

USER:

##### TASK

Describe the following image:
{image:image}

Pay attention to the following points:
{attention_points}

##### OUTPUT

First write a free form description of the image, then write a yaml in the following format:

###### DESCRIPTION

[The description of the image]

###### YAML DESCRIIPTION

```yaml
'subject': '[main subject of the image]'
'context': '[context of the image]'
```
