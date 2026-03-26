# TMU-BioDesign-
# 🦿 KneeSense — Smart Rehabilitation Knee Sleeve

> *From uncertain recovery to data-driven rehabilitation.*

**Developed by TMU BioDesign** · Toronto Metropolitan University
**Competition:** True North Biomedical Competition 2025–2026
**Hosted by:** Western Biomedical Engineering Club (WE BMC) & Canadian Undergraduate Biomedical Engineering Council (CUBEC)
Our Notion: https://www.notion.so/TMU-BioDesign-Home-2924757061e880d2a529ca0d3173fb0f?pvs=18

## The Problem

Every year, thousands of athletes and patients undergo knee rehabilitation following injuries like ACL tears, meniscus damage, or post-surgical recovery. The rehabilitation process is long, demanding, and — crucially — **subjective**.

Physiotherapists have historically relied on patient self-reporting:

> *"How strong does your knee feel compared to your good leg?"*
> *"Give me a number - how confident are you in that movement?"*

Patients struggle to answer these questions meaningfully. They can't feel the difference between 60% and 70% muscle activation. They can't objectively measure whether their hamstring is firing before their quadricep. They don't know if their form is correct or compensatory.

This uncertainty makes recovery mentally exhausting and clinically imprecise. Without objective data:
- Patients feel discouraged and uncertain about their progress
- Clinicians make decisions based on subjective impressions
- Compensation patterns go undetected, increasing re-injury risk
- Return-to-play decisions lack quantitative support

**KneeSense exists to close this gap.**

---

## Our Solution

KneeSense is a **wearable smart rehabilitation knee sleeve** that combines surface EMG sensing, inertial motion tracking, and AI-powered movement analysis into a single integrated biomedical device.

The sleeve captures real-time data on:
- 🔴 **Muscle activation patterns** — quadriceps, hamstring, and calf firing sequences
- 📐 **Knee flexion angle** — integrated from gyroscope data
- ⚖️ **Activation balance** — across muscle groups throughout movement
- 🏃 **Movement quality** — whether form matches expected patterns for the exercise
- 📈 **Progress over time** — trends tracked across sessions

This data is processed, visualized, and presented through a **clinician-facing web dashboard** that turns every session into a data-driven conversation — empowering both the patient and their physiotherapist.


## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HARDWARE LAYER                           │
│   EMG Electrodes (×3)  +  IMU Sensors (×3)  →  ESP32 MCU       │
│   Quad / Hamstring / Calf        Acc + Gyro                     │
└────────────────────────┬────────────────────────────────────────┘
                         │ WebSocket (Wi-Fi)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND LAYER (Flask / Python)           │
│                                                                 │
│  app.py                                                         │
│  ├── /esp32/connect   — WebSocket to ESP32                      │
│  ├── /esp32/start     — Begin trial recording                   │
│  ├── /esp32/stop      — End trial, save CSV                     │
│  ├── /preprocess      — ECG → EMG signal processing             │
│  └── /run-nnunet      — Full ML inference pipeline              │
│                                                                 │
│  backend/ml/                                                    │
│  ├── preprocessing_script_v2.py   — Filter, RMS, knee flexion   │
│  ├── csv_to_npy_bridge.py         — CSV → (8,T) + (48,T) npy   │
│  ├── generate_pseudo_images.py    — npy → (21,T) PNG            │
│  ├── nnunet_predict.py            — nnUNet segmentation         │
│  ├── analyse_label_maps.py        — Label stats & form score    │
│  └── multiply_intensity.py        — Colorize prediction masks   │
└────────────────────────┬────────────────────────────────────────┘
                         │ JSON API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER (HTML/JS)                 │
│                                                                 │
│  login.html       — Firebase authentication                     │
│  index.html       — Patient management dashboard                │
│  exercise.html    — Exercise selection & ESP32 control          │
│  acquired.html    — Live signal visualization                   │
│  analysis.html    — Signal processing + ML inference + scoring  │
│  trial.html       — Trial history & progress tracking           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware

### Sensing

| Component | Purpose | Placement |
|---|---|---|
| Surface EMG Electrodes | Muscle activation (mV) | Quadriceps, Hamstring, Calf |
| IMU (Accelerometer + Gyroscope) | Orientation & angular velocity | Same 3 muscle groups |
| ESP32 Microcontroller | Data acquisition & Wi-Fi transmission | Sleeve housing |

### Sleeve Design

- **Material:** Breathable, compression-grade fabric
- **Fit:** Adjustable circumference — accommodates ±3 inches around a 24-inch quad circumference, per competition specification
- **Biocompatibility:** All skin-contact materials are hypoallergenic
- **Form factor:** Compact enough for a physio bag; wiring integrated into the sleeve structure to survive folding

### Signal Characteristics

| Parameter | Value |
|---|---|
| EMG Sampling Rate | ~1259 Hz |
| IMU Sampling Rate | ~148 Hz |
| EMG:IMU Ratio | 17:2 (aligned in preprocessing) |
| Transmission | WebSocket over Wi-Fi (ESP32 AP mode) |
| Output Format | CSV — `timestamp_ms, EMG_Quad_mV, EMG_Ham_mV, EMG_Calf_mV, ACC_*_g, GYR_*_dps` |

---

## Software Stack

### Backend

| Library | Purpose |
|---|---|
| Flask | Web server & REST API |
| numpy / scipy | Signal filtering, RMS, resampling |
| pandas | CSV ingestion and processing |
| Pillow | Pseudo-image generation and normalization |
| nnUNetv2 | Deep learning inference |
| websocket-client | Real-time ESP32 communication |
| python-dotenv | Environment configuration |

### Frontend

| Technology | Purpose |
|---|---|
| HTML / CSS / JavaScript | Dashboard pages |
| Chart.js | Real-time signal visualization |
| Firebase SDK | Authentication & patient data persistence |
| LocalStorage | Session state between pages |

---

## Machine Learning Pipeline

KneeSense uses a trained **nnUNet 2D segmentation model** to classify movement quality from each recorded trial. The model was trained on the **KneE-PAD dataset** — a public research dataset of lower-limb EMG and IMU recordings across multiple exercises.

### Pipeline Overview

```
Raw CSV (ESP32)
      │
      ▼
1. PREPROCESSING  ──  preprocessing_script_v2.py
   • High-pass filter (20 Hz Butterworth, order 4)
   • Detrend → rectify → RMS envelope (50 ms window)
   • Knee flexion angle via trapezoidal gyroscope integration
   • Output: processed CSV with RMS_QUAD, RMS_HAM, RMS_CALF, KneeFlexion_deg
      │
      ▼
2. CSV → NPY BRIDGE  ──  csv_to_npy_bridge.py
   • Maps 3-muscle KneeSense CSV → KneE-PAD 8-sensor array format
   • EMG output: (8, T_emg) — Quad→RF(0,4), Ham→HAM(1,5), Calf→GAS(3,7)
   • IMU output: (48, T_imu) — 8 sensors × 6 channels (acc xyz, gyro xyz)
   • Resamples from ESP32 rate → training dataset rates (EMG: 1259 Hz, IMU: 148 Hz)
      │
      ▼
3. PSEUDO-IMAGE GENERATION  ──  generate_pseudo_images.py
   • Builds (21, T) signal image per side (right + left)
   • 3 muscles × 7 rows each: 1 EMG channel + 6 IMU channels
   • IMU upsampled to match EMG time base (17:2 ratio)
   • Z-score normalized per row → scaled to [0, 1] → saved as 8-bit grayscale PNG
      │
      ▼
4. NNUNET INFERENCE  ──  nnunet_predict.py
   • Model: Dataset601_KneePadSquat / nnUNetTrainer / nnUNetPlans / 2d
   • Input: PNG pseudo-images (case_XXXX_0000.png)
   • Output: Segmentation mask PNGs (grayscale, values 0 / 1 / 2)
      │
      ▼
5. LABEL MAP ANALYSIS  ──  analyse_label_maps.py
   • Label 0 → correct execution
   • Label 1 → wrong type 1  (e.g. valgus collapse)
   • Label 2 → wrong type 2  (e.g. insufficient squat depth)
   • Computes pixel-wise label distribution → form_score (% correct, 0–100)
      │
      ▼
6. MULTIPLY INTENSITY  ──  multiply_intensity.py
   • Colorizes prediction masks for clinical visualization
   • 0 → black (correct), 1 → red (wrong type 1), 2 → orange (wrong type 2)
   • Saved to dashboard/nnunet_results/ for display in analysis.html
```

### Model Details

| Parameter | Value |
|---|---|
| Framework | nnUNetv2 |
| Configuration | 2D |
| Dataset ID | Dataset601_KneePadSquat |
| Training data | KneE-PAD public dataset (squat classes 0 / 1 / 2) |
| Input format | Grayscale PNG, shape (21, T) |
| Output | Segmentation mask PNG (labels 0, 1, 2) |
| Cross-validation folds | fold_0 → fold_3 |

### Sensor Mapping: KneeSense → KneE-PAD

The KneE-PAD dataset uses an 8-sensor layout (right + left, 4 muscles each). KneeSense measures 3 muscles. The bridge script fills the 8-channel format accordingly, with the tibialis anterior — excluded from the pseudo-image builder by design — zeroed out.

```
KneeSense        →    KneE-PAD sensor index
────────────────────────────────────────────────────
EMG_Quad_mV      →    RF   (right = 0,  left = 4)
EMG_Ham_mV       →    HAM  (right = 1,  left = 5)
EMG_Calf_mV      →    GAS  (right = 3,  left = 7)
[not measured]   →    TIB  (right = 2,  left = 6)  ← zeroed, excluded
```

---

## Clinical Dashboard

The KneeSense web dashboard is designed for physiotherapists to use during or after a session. It requires no technical training to navigate.

### Key UI Features

- 📊 Real-time Chart.js signal plots with labeled axes
- 🔄 5-step pipeline progress indicator with live status
- 🎨 Colorized nnUNet prediction masks displayed inline
- 🎚️ Therapist score slider with one-click apply to patient record
- 📱 Responsive layout — usable on tablet for bedside sessions
- 🔔 Toast notifications for all pipeline events

---
## Setup & Installation

### Prerequisites

- Python 3.9+
- An ESP32 flashed with the KneeSense firmware
- Trained nnUNet model folds at the path shown in the repo structure above

### 1. Clone the repository

```bash
git clone https://github.com/your-org/KneeSense.git
cd KneeSense
```

### 2. Install Python dependencies

```bash
cd backend
pip install flask python-dotenv numpy scipy pandas matplotlib Pillow websocket-client nnunetv2
```

### 3. Configure environment

Create a `.env` file in the `backend/` directory with your Firebase credentials, ESP32 WebSocket URL, and output folder path.

> ⚠️ Never commit your `.env` file — add it to `.gitignore`.

### 4. Verify model folds exist

```
machineLearning/KneEPAD_nnUNet/nnUnet_results/
  Dataset601_KneePadSquat/
    nnUNetTrainer_nnUNetPlans_2d/
      fold_0/   ← required
      fold_1/
      fold_2/
      fold_3/
      plans.json
      dataset.json
```

The `nnunet_predict.py` script sets the `nnUNet_results` environment variable automatically at runtime using the model base path passed to it by `app.py`.

---

## Running the System

### Start the Flask server

```bash
cd backend
python app.py
# Server runs at http://localhost:5000
```

### Connect the sleeve

1. Power on the sleeve — ESP32 broadcasts a Wi-Fi access point
2. Connect your laptop to the ESP32 network
3. Open `http://localhost:5000` → log in → select patient → **Exercise** → **Connect to ESP32**

### Record a trial

1. **Connect** — wait for "Connected to ESP32 — ready to calibrate"
2. **Calibrate** — keep sleeve still for 12 seconds, then zero angles
3. **Start** — patient performs the exercise
4. **Stop** — trial saved as CSV in `backend/trial/`
5. **View Acquired Data** — inspect raw signals before analysis

### Analyse a trial

1. From **Acquired Data** → navigate to **Analysis**
2. **Run Processing** — ECG → EMG filtering, RMS envelope, knee flexion angle
3. **Run nnUNet** — full ML segmentation pipeline (~30–60 s)
4. **Run ML Model** — movement quality classification
5. **Apply Score** — set and save therapist score to patient record

---

## Engineering Standards

KneeSense was designed with reference to the following standards:

| Standard | Application |
|---|---|
| Health Canada Class I (Non-Invasive) | Device classification and safety |
| FDA Class I Medical Device Guidelines | Design input / output framework |
| ISO 14971 | Risk management — DFMEA submitted with design report |
| ISO 10993 | Biocompatibility of skin-contact materials |
| IEC 60601-1 | Electrical safety for medical electrical equipment |

All failure modes were documented in a Design Failure Mode and Effect Analysis (DFMEA) submitted as part of the competition design report on February 23rd, 2026.

---

## Acknowledgements

- **KneE-PAD Dataset** — public lower-limb EMG/IMU research dataset used for nnUNet model training
- **nnU-Net** (Isensee et al.) — self-configuring medical image segmentation framework
- **True North Biomedical Competition** — WE BMC & CUBEC for organizing the challenge
- **Ansys** — simulation tools and student licensing support

---

*KneeSense — turning rehabilitation from an uncertain journey into a guided, measurable path.*
