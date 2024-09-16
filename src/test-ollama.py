from ollama import Client
client = Client(host='http://localhost:11434')
response = client.chat(model='llama3', messages=[
  {
    'role': 'user',
    'content': 'Koalas are fun, aren\'t they?',
  },
])
print(response['message']['content'])
response = client.chat(model='llama3', messages=[
  {
    'role': 'user',
    'content': 'What was the first word of my first message?',
  },
])
print(response['message']['content'])