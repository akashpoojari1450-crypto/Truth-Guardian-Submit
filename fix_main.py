with open('app.py', 'r') as f:
    content = f.read()

# Remove the broken duplicate main block
bad = '''\ndef main():
    uvicorn.run(app, host="0.0.0.0", port=7860)
if __name__ == "__main__":
    main()'''

content = content.replace(bad, '')
content = content.replace(
    'if __name__ == "__main__":\n    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860)',
    'def main():\n    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860)\n\nif __name__ == "__main__":\n    main()'
)

with open('app.py', 'w') as f:
    f.write(content)
print("✅ Fixed!")
