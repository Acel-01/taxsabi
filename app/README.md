# TaxSabi — Offline Desktop App

A one-folder, fully offline app that lets anyone chat with the TaxSabi model.
No installation, no internet, no technical knowledge: double-click **Start TaxSabi**
and a simple tax-question page opens in your browser.

## Folder layout

```text
TaxSabi/
├── bin/
│   └── llama-server(.exe)      ← llama.cpp engine binary (place here)
├── model/
│   └── TaxSabi-1.5B-Q4_K_M.gguf← the TaxSabi model (~941 MB)
├── TaxSabi.html                ← the app page
├── Start-TaxSabi.bat           ← Windows launcher
├── Stop-TaxSabi.bat            ← Windows stop script
├── start-taxsabi.sh            ← Linux/macOS launcher
└── stop-taxsabi.sh             ← Linux/macOS stop script
```

## Setup

1. Copy the `llama-server` binary from a llama.cpp build into `bin/`
   (`llama-server.exe` on Windows).
2. Copy `TaxSabi-1.5B-Q4_K_M.gguf` into `model/`.
3. Double-click **Start TaxSabi** — the engine loads in the background and the
   app page opens in your browser at the local address shown.

Everything runs on your computer. Nothing is sent anywhere.

## Using the app

- Tap a green example chip, or type your own question in English or Nigerian Pidgin.
- Press **Ask TaxSabi** (or Enter). Answers include the band breakdown and statutory citations.
- Click **New question** between questions — the assistant is designed for
  one complete question at a time.

Estimates only — not tax advice. Deduction claims may require documentary
evidence under section 32 of the Nigeria Tax Act 2025.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Could not reach the TaxSabi engine" | Run Start/stop scripts again; check no firewall blocked `llama-server`; confirm nothing else uses port 8080 |
| Very first answer is slow | The model is loading into memory (one-time, ~10–20 s) |
| Port 8080 already in use | Edit the launcher and change `--port 8080` to another port, then reload the page |
