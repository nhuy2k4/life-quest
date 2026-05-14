# Vision AI Handoff (Google Cloud Vision)

## Muc tieu

- Huong dan cach chay Google Cloud Vision API trong project backend de test nhanh va sau do co the tich hop vao service.

## Trang thai hien tai

- File test dang dung: d:/DATN/be/test_vision.py
- Da chuyen tu Gemini (google genai) sang Google Cloud Vision (google.cloud.vision).
- Chay test thanh cong va nhan label tu Vision API.
- VisionService va AIApprovalService da duoc noi vao pipeline async.

## Cac buoc cau hinh dung (Windows)

1. Tao project dung tren Google Cloud Console.
2. Enable Cloud Vision API trong project do.
3. Tao Service Account, cap quyen Cloud Vision API User, tai file JSON key.
4. Dat file JSON vao vi tri de tham chieu, vi du: d:/DATN/be/google-vision.json
5. Dat bien moi truong:
   - Cach nhanh (session hien tai):
     $env:GOOGLE_APPLICATION_CREDENTIALS="D:\DATN\be\google-vision.json"
   - Cach ben (User env):
     [Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS","D:\DATN\be\google-vision.json","User")
     Sau do dong va mo lai terminal.
6. Neu dung .env, can load dotenv (da co) va su dung service account path tu .env.

## Cach check env neu bi loi ADC

- Kiem tra bien env trong session:
  $env:GOOGLE_APPLICATION_CREDENTIALS
- Kiem tra duong dan co ton tai:
  Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS
- Neu trống, session chua nhan bien env => set lai theo muc 5.
- He thong hien tai KHONG dung ADC fallback, bat buoc co GOOGLE_APPLICATION_CREDENTIALS.

## Luu y quan trong

- Loi 403 SERVICE_DISABLED => Cloud Vision API chua duoc bat dung project.
- Loi DefaultCredentialsError => bien GOOGLE_APPLICATION_CREDENTIALS chua duoc set hoac sai path.
- Neu set trong User/System env, can mo terminal moi de nhan.

## File test_vision.py hien tai (da load dotenv)

- Dung ImageAnnotatorClient voi credentials tu service account (khong ADC fallback).
- Doc test.jpg va goi label_detection.

## Ket qua mong doi

- Chay: python test_vision.py
- In ra cac label va score.

## Cac tinh nang co the dung trong Vision API

- Label Detection
- Object Localization
- Face Detection
- Landmark Detection
- Logo Detection
- Text / Document Text Detection
- Image Properties
- Safe Search Detection
- Web Detection
- Crop Hints
- Product Search (can setup them)
- Batch / Async annotate

## De tiep tuc

## Tich hop runtime (moi)

Luồng async hien tai:

1. User submit quest -> tao Submission (pending)
2. Enqueue Celery task
3. Worker goi VisionService (label detection)
4. AIApprovalService tinh diem va ra quyet dinh
5. Cap nhat Submission status + ai_score + cheat_flags

Ghi chu:

- Neu Vision API loi/timeout: danh dau manual_review va log error trong cheat_flags.
- Nen them retry co backoff (3 lan) trong worker.

## Cac file lien quan

- d:/DATN/be/app/services/vision/vision_service.py
- d:/DATN/be/app/services/ai/ai_approval_service.py
- d:/DATN/be/app/services/pipeline/approval_pipeline.py
- d:/DATN/be/app/workers/approval_tasks.py

## De xuat tiep theo

- Them ai_detection_logs de luu labels/ocr/raw_response.
- Dua threshold ra env (AI_AUTO_APPROVE_THRESHOLD, AI_MANUAL_REVIEW_THRESHOLD).
