from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import base64
import os
import platform
import subprocess
import uuid
import sys
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def send_to_printer(temp_file, system):
    try:
        if system == "Windows":
            subprocess.Popen([
                "cmd", "/c", "start", "/min", "", "/print", temp_file
            ], shell=True)
        elif system == "Linux":
            subprocess.Popen(["xdg-open", temp_file])
        else:
            print("Unsupported OS for printing")
    except Exception as e:
        print("Printer error:", str(e))

@app.post("/print")
async def print_image(request: Request):
    try:
        data = await request.json()
        base64_image = data.get("image")

        if not base64_image:
            raise HTTPException(status_code=400, detail="Missing 'image' field")

        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        image_bytes = base64.b64decode(base64_image)
        temp_file = os.path.join(tempfile.gettempdir(), f"receipt_{uuid.uuid4()}.jpg")
        with open(temp_file, "wb") as f:
            f.write(image_bytes)

        print("Saved to:", temp_file)

        # Start print job in a background thread (non-blocking)
        threading.Thread(target=send_to_printer, args=(temp_file, platform.system()), daemon=True).start()

        return {"message": "Print job sent"}  # Respond immediately

    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=400, detail="Invalid image data")

if __name__ == "__main__":
    import uvicorn
    port = 5050
    for arg in sys.argv:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
