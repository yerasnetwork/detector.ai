import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from ultralytics import YOLO
import fitz  # PyMuPDF
import io
from pathlib import Path
from typing import List # <-- 1. ДОБАВИЛИ List

# --- 1. ЗАГРУЖАЕМ "МОЗГ" ---
MODEL_PATH = Path("best.pt")
if not MODEL_PATH.exists():
    print("[!] ОШИБКА: Файл 'best.pt' не найден.")
    exit()
    
print("[*] Загружаем обученную модель best.pt...")
model = YOLO("best.pt")
print("[+] Модель успешно загружена!")
# ----------------------------------------

# --- 2. ЦВЕТА ДЛЯ РАМОК (B, G, R) ---
# Мы берем их из data.yaml: 0:Signature, 1:text, 2:qr-code, 3:stamp
# Убедись, что твои `model.names` совпадают!
CLASSES_COLORS = {
    "Signature": (255, 0, 0),    # Синий
    "stamp": (0, 0, 255),        # Красный
    "qr-code": (0, 255, 0),      # Зеленый
    "text": (255, 255, 0),     # Бирюзовый (если мы захотим его)
}
# ----------------------------------------

app = FastAPI(
    title="Цифровой Инспектор (ФИНАЛ v3.1)",
    description="API для детекции с ФИЛЬТРАМИ!",
    version="3.1"
)

# --- CORS ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- КОНЕЦ CORS ---

@app.get("/")
def read_root():
    return {"message": "Цифровой Инспектор (ФИНАЛ v3.1) готов к работе!"}


def draw_boxes(img, results, classes_to_find: List[str]):
    """
    ЗАМЕНА ДЛЯ .plot()
    Вручную рисует рамки ТОЛЬКО для тех классов, которые мы ищем.
    """
    # Начинаем с оригинальной картинки
    img_with_boxes = results[0].orig_img.copy() 
    
    # model.names это {0: 'Signature', 1: 'text', 2: 'qr-code', 3: 'stamp'}
    names = results[0].names 
    
    for box in results[0].boxes:
        # Получаем класс (0, 1, 2...) и его имя ('Signature', 'text'...)
        class_id = int(box.cls[0])
        class_name = names.get(class_id, "Unknown")
        
        # --- 3. НАШ ФИЛЬТР! ---
        # Если имя класса НЕ в списке, который прислал юзер, пропускаем эту рамку
        if class_name not in classes_to_find:
            continue
        # --- КОНЕЦ ФИЛЬТРА ---

        # Получаем координаты [x1, y1, x2, y2]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        # Получаем уверенность (0.0 - 1.0)
        conf = float(box.conf[0])
        
        # Выбираем цвет
        color = CLASSES_COLORS.get(class_name, (255, 255, 255)) # Белый по умолчанию
        
        # Рисуем рамку
        cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), color, 3) # Толще рамка
        
        # Рисуем текст (Имя класса + Уверенность)
        label = f"{class_name} {conf:.2f}"
        cv2.putText(img_with_boxes, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        
    return img_with_boxes


def process_pdf(pdf_bytes, classes_to_find: List[str]):
    processed_pages = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if len(doc) == 0:
        raise HTTPException(status_code=400, detail="PDF is empty")
    
    print(f"[*] PDF получен. Ищем: {classes_to_find}. Обрабатываем {len(doc)} страниц...")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=200)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        if img_np.shape[2] == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # --- 4. МАГИЯ v3.1 ---
        # Мы понижаем порог до 0.1 (10%), чтобы найти СЛАБЫЕ подписи
        results = model(img_bgr, conf=0.1, verbose=False) 
        
        # Рисуем рамки вручную, используя наш фильтр
        img_with_boxes = draw_boxes(img_bgr, results, classes_to_find)
        # --- КОНЕЦ МАГИИ ---
        
        processed_pages.append(img_with_boxes)
    
    doc.close()
    if not processed_pages: return None
    
    print(f"[*] Обработка завершена. Склеиваем {len(processed_pages)} страниц...")
    final_image = cv2.vconcat(processed_pages)
    return final_image

def process_image(img_bytes, classes_to_find: List[str]):
    print(f"[*] Изображение получено. Ищем: {classes_to_find}...")
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None: return None
    
    # --- МАГИЯ v3.1 ---
    results = model(img, conf=0.1, verbose=False) # Понижаем порог
    img_with_boxes = draw_boxes(img, results, classes_to_find)
    # --- КОНЕЦ МАГИИ ---
    
    return img_with_boxes


@app.post("/inspect/")
async def inspect_document(
    # --- 5. НОВЫЙ ПАРАМЕТР! ---
    # Мы принимаем список "find" из URL (query parameter)
    find: List[str] = Query(default=["Signature", "stamp", "qr-code", "text"]),
    file: UploadFile = File(...)
):
    img_bytes = await file.read()
    file_type = file.content_type
    
    final_image = None 

    if file_type == "application/pdf":
        final_image = process_pdf(img_bytes, find)
    elif file_type in ["image/png", "image/jpeg"]:
        final_image = process_image(img_bytes, find)
    else:
        return JSONResponse(status_code=400, content={"error": f"Тип файла {file_type} не поддерживается."})

    if final_image is None:
        return JSONResponse(status_code=500, content={"error": "Не удалось прочитать или сконвертировать файл."})

    is_success, buffer = cv2.imencode(".png", final_image)
    if not is_success:
        return JSONResponse(status_code=500, content={"error": "Could not encode final image"})
    
    output_image_bytes = io.BytesIO(buffer)
    
    return StreamingResponse(
        output_image_bytes, 
        media_type="image/png"
    )

if __name__ == "__main__":
    print(f"[*] Запускаем 'Цифровой Инспектор' (v3.1 - LIVE MODEL + FILTERS) на http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)