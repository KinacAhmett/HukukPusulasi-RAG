# HukukPusulası — Privacy-Preserving RAG for Turkish Consumer Law

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6B6B)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

> **HukukPusulası** is a retrieval-augmented legal assistant for
> Turkish consumer law, paired with a systematic evaluation of **locally deployable**
> language models. It explores how reliable legal information can be delivered
> **without sending sensitive data to a third-party cloud**.

<!-- TODO: add a screenshot or short GIF of the chat interface here -->
<!-- ![HukukPusulası interface](docs/screenshot.png) -->

---

## 📖 Overview

Accessing reliable, well-grounded answers in consumer law is hard: the information
exists in legislation, but reading and interpreting it correctly is the real
bottleneck. HukukPusulası addresses this with a **Retrieval-Augmented Generation
(RAG)** pipeline that retrieves the relevant articles of Turkish consumer law and
generates answers grounded in those sources.

The project has two halves:

1. **The application** — a working chatbot (Flask + React) that answers
   consumer-law questions with source-grounded responses.
2. **The research** — a systematic evaluation of **7 language models** on a
   purpose-built Turkish consumer-law benchmark, measuring whether locally
   deployable open-source models can match proprietary cloud APIs on the metrics
   that matter for deployment: **faithfulness** and **factual correctness**.

---

## 🎓 Academic Context

This project was developed as a **graduation project** in the Department of
Computer Engineering, **TED University**.

| | |
|---|---|
| **Author** | Ahmet Kınaç |
| **Supervisor** | Dr. Eren Ulu |
| **Graduation Project** | *Privacy-Preserving Retrieval-Augmented Generation for Turkish Consumer Law: Evaluation of Locally Deployable Language Models* |
| **Institution** | TED University — Department of Computer Engineering |

> This was a team project. The **React frontend, the SQLite data layer, and the
> full evaluation** were my individual contribution — see [My Contribution](#-my-contribution).

---

## ✨ Features

- 🤖 **Source-grounded legal Q&A** — answers backed by retrieved articles of Turkish consumer law
- 📚 **RAG pipeline** with ChromaDB as the vector store
- 🧩 **Document-aware chunking** — respects the *madde* (article) / *fıkra* (sub-clause) structure of legislation
- 🔐 **Configurable model backend** — runs with a cloud API **or** a locally deployable model
- 💬 **Multi-session chat** with persistent history
- 📄 **PDF upload and analysis**
- 🔍 **Chat history search**
- ♿ **Accessibility-focused** interface

---

## 🔬 Research & Evaluation

The core research question: **can locally deployable open-source models match a
proprietary cloud baseline closely enough to be a privacy-preserving alternative?**

### Retrieval pipeline

- Legal texts are embedded with an encoder and stored in a vector store.
- A **document-aware chunking mechanism** preserves the natural *madde* / *fıkra*
  organisation of legislation, tuned for Turkish — an agglutinative language whose
  morphology makes naïve chunking unreliable.
- A **quality-aware retrieval** step filters chunks by semantic distance before
  they reach the generation stage.

### Benchmark

- **13,676** question–answer pairs covering Turkish consumer law.
- A **200-question stratified subset** for evaluation:
  50% hypothetical · 30% analytical · 20% factual.

### Evaluation protocol

- **7 language models** evaluated (open-source and proprietary, ~2–8B parameter range).
- **6 RAGAS metrics**, including Faithfulness, Answer Relevancy, Semantic
  Similarity, and Factual Correctness.
- **~8,400 observations** in total; ~80 hours of evaluation on consumer-grade hardware.

### Key findings

- **Retrieval was strong and consistent** — across all models, Context Precision
  stayed around **0.93** and Context Recall around **0.83**. Retrieval is shared
  by the whole pipeline, so these barely move between models.
- **The best open-source model matched or beat the proprietary baseline on every
  metric.** Qwen-3-7B vs. Gemini-3.1-Flash-Lite: **+0.059** Faithfulness
  (0.605 vs. 0.546) and **+0.024** Factual Correctness (0.564 vs. 0.540), with a
  small edge on Answer Relevancy and a tie elsewhere.
- **Qwen-3-7B was the strongest generator overall**, leading on both Faithfulness
  (0.605) and Factual Correctness (0.564).
- **Model choice mattered enormously for faithfulness** — scores ranged from
  0.605 (Qwen-3-7B) down to 0.247 (DeepSeek-R1-7B), roughly a 2.4× gap, even
  though every model received identical retrieved context.

### Results

Per-model scores on the 200-question evaluation subset:

| Model | Context Precision | Context Recall | Faithfulness | Answer Relevancy | Semantic Similarity | Factual Correctness (F1) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Qwen-3-7B | 0.934 | 0.829 | **0.605** | 0.462 | 0.791 | **0.564** |
| Gemini-3.1-Flash-Lite ¹ | 0.934 | 0.829 | 0.546 | 0.455 | 0.791 | 0.540 |
| Gemma-3-4B | 0.936 | 0.825 | 0.535 | 0.454 | **0.803** | 0.521 |
| Gemma-2-2B | 0.930 | **0.837** | 0.326 | 0.404 | 0.787 | 0.390 |
| Llama-3.1-8B | **0.939** | 0.825 | 0.294 | **0.478** | 0.743 | 0.319 |
| Mistral-7B | 0.934 | 0.821 | 0.273 | 0.436 | 0.771 | 0.278 |
| DeepSeek-R1-7B | 0.934 | 0.828 | 0.247 | 0.428 | 0.595 | 0.278 |

¹ Proprietary cloud baseline. All other models are open-source and locally deployable.
Bold marks the best score in each column.

---

## 🏗️ Architecture

```
                ┌──────────────┐        ┌──────────────────┐
   User  ─────► │ React frontend│ ─────► │  Flask backend   │
                └──────────────┘        │                  │
                                        │  ┌────────────┐  │
                                        │  │ RAG service │  │──► ChromaDB (vector store)
                                        │  └────────────┘  │
                                        │  ┌────────────┐  │
                                        │  │   model     │  │──► Cloud API  ─┐
                                        │  │   backend   │  │                ├─ configurable
                                        │  └────────────┘  │──► Local model ─┘
                                        │       │          │
                                        │       ▼          │
                                        │   SQLite (chat)  │
                                        └──────────────────┘
```

- **`backend/`** — Flask API, SQLite for chat persistence, RAG + model integration
- **`frontend/`** — React single-page application
- **`fineTuning/`** — Jupyter notebooks for dataset creation and the RAG / evaluation experiments

---

## 🧰 Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python, Flask, SQLite |
| **Vector store** | ChromaDB |
| **Retrieval / Generation** | RAG pipeline, configurable model backend |
| **Frontend** | React |
| **Research** | Jupyter, RAGAS evaluation metrics |
| **Infrastructure** | Docker, Docker Compose |

---

## 🔐 Models & Privacy

HukukPusulası supports **two interchangeable model backends**:

| Backend | Use case | Privacy |
|---|---|---|
| **Cloud API (Gemini)** | Fast setup, strong baseline performance | Sends queries to a third-party service |
| **Locally deployable model** | Privacy-preserving deployment | Data never leaves the host |

Because consumer-law questions can contain sensitive personal information, the
**locally deployable path is the privacy-preserving option** — and the project's
evaluation shows that open-source models in the 2–8B range are accurate enough to
make that path viable.

---

## 🚀 Installation

### Running with Docker (recommended)

1. **Create the backend `.env` file:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your model/API configuration
   ```

2. **Start with Docker Compose:**
   ```bash
   cd frontend
   docker-compose up --build
   ```
   - Backend: http://localhost:5000
   - Frontend: http://localhost:3000

   For detailed Docker setup, see [`frontend/DOCKER_README.md`](./frontend/DOCKER_README.md).

### Manual installation

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env
python app.py
```

**Frontend**
```bash
cd frontend
npm install
npm start
```

---

## 📁 Project Structure

```
HukukPusulasi/
├── backend/                  # Flask backend API
│   ├── app.py                # Main Flask application
│   ├── database.py           # SQLite database management
│   ├── model_service.py      # Model backend + RAG integration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React frontend application
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── fineTuning/               # Dataset creation + RAG / evaluation notebooks
│   ├── dataset_create.ipynb
│   ├── HukukPusulasi_RAG.ipynb
│   ├── .env.example
│   └── README.md
└── docker-compose.yml        # Docker Compose configuration
```

---

## 👤 My Contribution

This was a team project. My individual work spanned three areas:

**🖥️ React frontend**
- Built the React single-page application — the chat interface, multi-session
  navigation, and the overall user experience.

**🗄️ SQLite data layer**
- Implemented the SQLite database layer for chat persistence and multi-session
  management on the backend.

**🔬 Evaluation & research**
- Designed and implemented the evaluation framework used to compare models.
- Constructed the Turkish consumer-law benchmark (13,676 Q&A pairs and the
  200-question stratified subset).
- Ran the systematic comparison of 7 language models across 6 RAGAS metrics
  (~8,400 observations) and analysed the results.
- Contributed to the document-aware chunking mechanism that preserves the
  *madde* / *fıkra* structure of legislation.
- Investigated the privacy-preserving angle: whether locally deployable
  open-source models can replace a proprietary cloud baseline.

> ✏️ *Adjust the wording so it matches your exact role precisely — only claim
> what you personally did.*

---

## 🙏 Acknowledgments

- **Dr. Eren Ulu** — project supervisor, TED University
- The project teammates who contributed to the application development
- TED University, Department of Computer Engineering

---

## 📄 License

Released under the MIT License. See [`LICENSE`](./LICENSE) for details.

---

## 🔒 Privacy & Security Notes

- Never commit real API keys — `.env` files are protected by `.gitignore`.
- The ChromaDB store (`backend/legal_chroma_db/`) and SQLite database
  (`backend/chat.db`) are persisted via Docker volumes.
- For privacy-sensitive deployments, use the **local model backend** so that
  user queries never leave the host.