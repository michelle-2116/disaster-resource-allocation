from root dir of repo (...\4-el)

for be:
```
cd backend
pip install .
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

for fe:
```
cd frontend
npm install
npm run dev
```