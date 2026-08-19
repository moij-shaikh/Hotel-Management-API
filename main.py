from fastapi import FastAPI

app=FastAPI(debug=True,version="1")

@app.get("/")
def show():
    return "ok requirement"