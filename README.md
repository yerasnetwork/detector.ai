# 🔎 Digital Inspector

**An AI service (YOLOv8 + FastAPI) for the automatic detection of signatures, stamps, and QR codes on documents.**

This project was developed during a 24-hour hackathon. The solution can accept `.pdf`, `.png`, or `.jpg` files as input and return a processed image with all detected objects.

---

##  demo Demo

*Our FastAPI backend processes all pages of an uploaded PDF, runs the YOLOv8 model on each page, and stitches them into a single "filmstrip" image for easy review.*



---

## 🏆 Key Features

* **Multi-Class Detection:** The fine-tuned YOLOv8s model confidently recognizes **3** key classes: `Signature`, `stamp`, and `qr-code`.
* **Flexible Input:** The API accepts not only images (`.png`, `.jpg`) but also **multi-page `.pdf` files**.
* **Interactive Frontend:** A clean HTML/CSS/JS interface allows users to upload files and **filter** the displayed objects (e.g., "show only signatures").
* **High-Performance Backend:** A **FastAPI** (Python) backend ensures asynchronous processing, ready for high-load scenarios.

---

## 🛠️ Tech Stack (Architecture)

* **Model:** **YOLOv8s** (fine-tuned).
* **Training:** **Google Colab** (on a T4 GPU) using a "golden" public dataset from Roboflow (9,000+ images) after discovering the organizer's data was corrupt.
* **Backend:** **FastAPI** (Python) — for a high-speed REST API.
* **Frontend:** Plain **HTML, CSS, JavaScript** (using the `fetch` API).
* **PDF Processing:** `PyMuPDF (fitz)` — for rapid in-memory conversion of PDF to images.
* **Image Processing:** `OpenCV (cv2)` — for drawing bounding boxes and stitching pages.

---

## 🚀 How to Run Locally

### 1. Preparation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yerasnetwork/detector.ai.git](https://github.com/yerasnetwork/detector.ai.git)
    cd detector.ai
    ```

2.  **Create and activate a virtual environment** (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 2. Download the Model (Critical!)

The trained model **`best.pt`** (22 MB) is not stored in Git due to its size (it's in the `.gitignore`).

* **[https://drive.google.com/file/d/1D9H4XzBpYN-5uMPSQhEAhpmAzGLRZk1t/view?usp=drive_link (best.pt)]()** *(<-- **IMPORTANT:** Upload your `best.pt` 

**Place the downloaded `best.pt` file in the project root** (next to `main.py`).

### 3. Launch

1.  **Run the Backend (FastAPI):**
    * In your terminal, run:
    ```bash
    python main.py
    ```
    * The server will start on `http://127.0.0.1:8000`

2.  **Open the Frontend:**
    * In your file explorer, **double-click the `index.html` file**.
    * It will open in your browser.

You can now upload PDF files (e.g., from the `test` folder) and see the live results!

---

## 🗺️ Vision & Scalability (Answering Judging Criterion #2)

**The Question:** "Can it handle processing 1,000 documents?"

**The Answer:** Yes. But not by using the "Upload" button.

The current web UI is a **demo**. The real product is the **`main.py` (API)**.

We chose **FastAPI** specifically because it is a **perfectly scalable ("stateless")** solution. To process 1,000 documents, we would **not** run them one-by-one on a local machine. We would deploy this API to **Google Cloud Run**, which **automatically scales up to 1,000 parallel instances** of our server. This allows us to process 1,000 documents in the same amount of time it takes to process one.

**This project's architecture is already designed for production-level loads.**
