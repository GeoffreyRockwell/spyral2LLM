# Spyral JS Assistant

A single-page JS coding assistant (`index.html`) that can talk to either a
local **Ollama** model or the **Claude** API. It's meant to be opened
directly in a browser, with an optional local proxy server
(`server.py`) for when the browser blocks direct requests.

## Running Ollama locally

The app talks to Ollama at `http://localhost:11434`, so Ollama needs to be
installed, running, and have at least one model pulled.

1. **Install Ollama**
   - Download the desktop app from [ollama.com/download](https://ollama.com/download), or
   - `brew install ollama`

2. **Start Ollama**
   - If you installed the desktop app, just launch it — it runs the server
     in the background.
   - If you installed via Homebrew (or want to run it manually in a
     terminal), start it with:
     ```
     ollama serve
     ```

3. **Pull at least one model**
   ```
   ollama pull llama3.2
   ```
   Any model you pull will show up in the app's model dropdown when the
   "Ollama" provider tab is selected.

4. **Verify it's reachable**
   ```
   curl http://localhost:11434/api/tags
   ```
   This should return JSON listing your installed models. If this fails,
   the app won't be able to reach Ollama either.

## Running the app

Once Ollama is running, open `index.html` directly in your browser — no
server required. Ollama and Claude requests go straight from the browser
to their APIs.

### If the browser blocks the request (CORS)

Ollama rejects requests from pages opened as a plain `file://` URL, so this
is common. The app automatically falls back to the local proxy in
`server.py`, but that fallback only works if the server is running. Start
it in a terminal and open `http://localhost:8080` instead of the file
directly:

```
cd "spyral2LLM"
python3 server.py
```

`server.py` proxies:
- `GET /api/ollama/tags` → `http://localhost:11434/api/tags`
- `POST /api/ollama/chat` → `http://localhost:11434/api/chat`
- `POST /api/claude` → `https://api.anthropic.com/v1/messages`

## Using Claude instead

Switch to the "Claude" provider tab and enter an Anthropic API key in
Settings (⚙). The key is held in memory only and is cleared when you close
the page.

## Files

- `index.html` — the app (UI, provider/model selection, chat logic)
- `server.py` — optional local proxy used as a CORS fallback for both
  Ollama and Claude
