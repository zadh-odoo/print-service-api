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
import struct
import win32print
from PIL import Image, ImageEnhance, ImageFilter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRINTER_WIDTH = 576  # adjust to your thermal printer's pixel width


def send_to_printer(temp_file, system):
    try:
        if system == "Windows":
            printer_name = win32print.GetDefaultPrinter()
            print(f"Printing {temp_file} to {printer_name}")

            # Load and process the image with enhanced quality
            im = Image.open(temp_file)
            print(f"Original image size: {im.size}")
            
            # Calculate new dimensions maintaining aspect ratio
            w = PRINTER_WIDTH
            h = int(im.height * (w / im.width))
            print(f"Resizing to: {w}x{h}")
            
            # Use high-quality resampling
            im = im.resize((w, h), Image.LANCZOS)
            
            # Apply sharpening filter to improve text clarity
            print("Applying sharpening filter...")
            im = im.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3))
            
            # Enhance sharpness for crisp text
            enhancer_sharpness = ImageEnhance.Sharpness(im)
            im = enhancer_sharpness.enhance(1.5)  # Increase sharpness
            
            # Increase brightness for better visibility on thermal paper
            print("Enhancing brightness...")
            enhancer_brightness = ImageEnhance.Brightness(im)
            im = enhancer_brightness.enhance(1.4)  # Increased from 1.3 to 1.4
            
            # Increase contrast for better text definition
            print("Enhancing contrast...")
            enhancer_contrast = ImageEnhance.Contrast(im)
            im = enhancer_contrast.enhance(1.8)  # Increased from 1.5 to 1.8
            
            # Convert to grayscale first for better dithering
            print("Converting to grayscale...")
            im = im.convert('L')
            
            # Apply Floyd-Steinberg dithering for better quality monochrome conversion
            print("Converting to monochrome with dithering...")
            im = im.convert('1', dither=Image.FLOYDSTEINBERG)

            # Pack pixels into bytes for ESC/POS
            width_bytes = (im.width + 7) // 8
            bitmap = bytearray()
            pixels = im.load()

            for y in range(im.height):
                for x in range(0, im.width, 8):
                    byte = 0
                    for bit in range(8):
                        if x + bit < im.width:
                            if pixels[x + bit, y] == 0:  # Black pixel
                                byte |= 1 << (7 - bit)
                    bitmap.append(byte)

            # ESC/POS commands
            data = bytearray()
            data += b'\x1B\x40'  # Initialize
            data += b'\x1D\x76\x30\x00'  # GS v 0 m
            data += struct.pack('<2H', width_bytes, im.height)  # Width in bytes, height in dots
            data += bitmap
            data += b'\n\n\x1D\x56\x00'  # Feed & cut

            # Send to printer in RAW mode
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("ESC/POS Print", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

        elif system == "Linux":
            subprocess.run(["lp", temp_file], check=True)
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

        # Remove data URI prefix if present
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        image_bytes = base64.b64decode(base64_image)

        # Save image to temp file
        temp_file = os.path.join(tempfile.gettempdir(), f"receipt_{uuid.uuid4()}.png")
        with open(temp_file, "wb") as f:
            f.write(image_bytes)

        print("Saved to:", temp_file)

        # Print in a background thread
        threading.Thread(target=send_to_printer, args=(temp_file, platform.system()), daemon=True).start()

        return {"message": "Print job sent"}

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
