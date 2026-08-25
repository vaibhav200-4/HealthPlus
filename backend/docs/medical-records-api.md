# Authoritative API Reference: Medical Record Upload for Telegram / n8n Workflow

This document is the **single source of truth** for configuring the **n8n HTTP Request node** to upload patient medical documents and photos from Telegram to the HealthPulse backend.

---

## Endpoint Details

- **Method**: `POST`
- **Production URL**: `https://healthplus-backend-nwpw.onrender.com/api/medical-records/upload`
- **Local Dev URL**: `http://localhost:8000/api/medical-records/upload`
- **Content-Type**: `multipart/form-data`

---

## Authentication Header

Only server-to-server requests providing a valid `X-Telegram-Secret` header matching the backend's `TELEGRAM_WEBHOOK_SECRET` environment variable are permitted for n8n/Telegram uploads. The `n8n_token` / `Authorization: Bearer` path has been disabled to prevent false `401` errors during upstream context resolution.

| Header Name | Required | Value / Expression | Value Source |
| :--- | :--- | :--- | :--- |
| `X-Telegram-Secret` | **Yes** | `telegram-secret-key-0192837465` *(or `{{ $env.TELEGRAM_WEBHOOK_SECRET }}`)* | Render Environment Variable: `TELEGRAM_WEBHOOK_SECRET` |

---

## Multipart Form Data Fields

| Field Name | Type | Required | Default if Omitted | Example n8n Expression | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `file` | File / Binary | **Yes** | N/A | `data` | Binary payload from `message.document` or `message.photo` |
| `patient_identifier` | Form Data (text) | **Yes** | N/A | `{{ $json.user_id }}` | Accepts `profiles.id` or `patients.id` (internally resolved) |
| `title` | Form Data (text) | **Yes** | N/A | `{{ $json.title || "Telegram Document Upload" }}` | Human-readable title for the report or scan |
| `uploaded_by` | Form Data (text) | No | `"patient"` | `patient` | Source tag (`"patient"`, `"doctor"`, `"admin"`) |
| `record_type` | Form Data (text) | No | `"other"` | `{{ $json.record_type || "other" }}` | Category: `"diagnosis"`, `"lab_report"`, `"xray"`, `"mri"`, `"blood_test"`, `"discharge_summary"`, `"other"` |
| `description` | Form Data (text) | No | `""` | `{{ $json.description || "Uploaded via Telegram bot" }}` | Clinical or user notes |
| `doctor_id` | Form Data (text) | No | `null` | `{{ $json.doctor_id }}` | Optional doctor UUID |
| `session_id` | Form Data (text) | No | `null` | `{{ $json.session_id }}` | Optional clinical session UUID |

---

## File Field & Extension Contract

- **Binary Field Name**: Must be named **`file`**.
- **Extension & MIME Handling**: The backend inspects `file.filename` extension (`.pdf`, `.jpg`, `.png`, `.webp`). If missing or generic (e.g. Telegram photo `file_0`), extension is inferred automatically from `content_type` (`image/jpeg` $\rightarrow$ `jpg`).

---

## Literal n8n HTTP Request Node Configuration Example

```json
{
  "parameters": {
    "method": "POST",
    "url": "https://healthplus-backend-nwpw.onrender.com/api/medical-records/upload",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "X-Telegram-Secret",
          "value": "telegram-secret-key-0192837465"
        }
      ]
    },
    "sendBody": true,
    "contentType": "multipart-form-data",
    "bodyParameters": {
      "parameters": [
        {
          "name": "patient_identifier",
          "value": "={{ $json.user_id }}"
        },
        {
          "name": "title",
          "value": "={{ $json.title || 'Telegram Upload' }}"
        },
        {
          "name": "uploaded_by",
          "value": "patient"
        },
        {
          "name": "record_type",
          "value": "={{ $json.record_type || 'other' }}"
        },
        {
          "name": "description",
          "value": "={{ $json.description || 'Uploaded via Telegram bot' }}"
        }
      ]
    },
    "sendBinaryData": true,
    "binaryPropertyName": "data"
  }
}
```

---

## Expected API Responses

### 1. Success Response (`HTTP 200 OK`)
```json
{
  "id": "c1f7b0a1-8d23-4e89-a1b2-c3d4e5f6a7b8",
  "patient_id": "2ea9fa57-f207-4421-bcb8-473d260b9625",
  "patient_code": "PT-000001",
  "doctor_id": null,
  "doctor_name": null,
  "session_id": null,
  "record_type": "other",
  "title": "Telegram Photo Scan",
  "description": "Uploaded via Telegram bot",
  "file_url": "2ea9fa57-f207-4421-bcb8-473d260b9625/c1f7b0a1-8d23-4e89-a1b2-c3d4e5f6a7b8.jpg",
  "signed_file_url": "https://eazotbgtvykowccfjlbk.supabase.co/storage/v1/object/sign/medical-records/...",
  "uploaded_by": "patient",
  "file_type": "jpg",
  "file_size_bytes": 1048576,
  "created_at": "2026-08-25T16:35:00.000Z",
  "updated_at": null
}
```

### 2. Error Responses

#### `HTTP 401 Unauthorized` (Missing or Invalid X-Telegram-Secret Header)
```json
{
  "detail": "Invalid X-Telegram-Secret header"
}
```

#### `HTTP 400 Bad Request` (Invalid File Type)
```json
{
  "detail": "Invalid file extension '.exe'. Allowed extensions: jpeg, jpg, pdf, png, webp"
}
```

#### `HTTP 400 Bad Request` (File Exceeds 15MB Limit)
```json
{
  "detail": "File size exceeds maximum limit of 15MB"
}
```

#### `HTTP 404 Not Found` (Patient Profile Not Found)
```json
{
  "detail": "No patient or profile record found for identifier: invalid_user_id"
}
```
