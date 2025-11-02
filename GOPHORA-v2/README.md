# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

---

## GOPHORA - Development Setup

This section explains how to run the GOPHORA project for local development.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/en/download/) (v18 or later)
- [OpenSSL](https://www.openssl.org/) (usually pre-installed on Linux and macOS)

### 1. Configure Environment

This project uses a `.env` file to manage secrets like the API secret key and database credentials. To get started, copy the example file:

```bash
cp .env.example .env
```

Next, you need to generate a secret key. Open the new `.env` file and add a value for `SECRET_KEY`. You can generate a secure key with this command:

```bash
openssl rand -hex 32
```

Copy the output of that command into your `.env` file for the `SECRET_KEY` variable.

### 2. API Keys

This project uses two external services that require API keys:

-   **Google Gemini:** Used for all AI-powered features, including chat and verification.
-   **Geoapify:** Used for geocoding locations to display on the map.

After creating your `.env` file, you need to add the following keys:

1.  **`GEMINI_API_KEY`**:
    *   Go to [Google AI Studio](https://aistudio.google.com/).
    *   Click on "**Get API key**" and create a new key.
    *   Copy the key and paste it into your `.env` file:
        ```
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```

2.  **`GEOAPIFY_API_KEY`**:
    *   Create a free account on [Geoapify](https://www.geoapify.com/).
    *   Create a new project to automatically generate an API key.
    *   Copy the key and paste it into your `.env` file for both the backend and frontend variables:
        ```
        GEOAPIFY_API_KEY="YOUR_GEOAPIFY_API_KEY"
        VITE_GEOAPIFY_API_KEY="YOUR_GEOAPIFY_API_KEY"
        ```

Your final `.env` file should look something like this:

```
SECRET_KEY=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GEMINI_EMBED_MODEL="text-embedding-004"
GEMINI_CHAT_MODEL="gemini-1.5-flash-latest"
GEOAPIFY_API_KEY="YOUR_GEOAPIFY_API_KEY"
VITE_GEOAPIFY_API_KEY="YOUR_GEOAPIFY_API_KEY"
```

### 2. Start the Backend & Database (with Docker)

The backend server and PostgreSQL database run in Docker containers managed by Docker Compose. This command reads the variables from your `.env` file.

From the project root directory, run the following command:

```bash
docker-compose up --build -d
```

- `--build`: Builds the Docker images. Use this the first time or after changing dependencies.
- `-d`: Runs the containers in the background.

This command starts the backend, which will be accessible on `http://localhost:8000`.

### 3. Run the Frontend (Local)

The frontend is a React application that runs locally and connects to the backend in Docker.

From the project root directory, run these commands:

```bash
# Install all frontend dependencies
npm install

# Start the frontend development server
npm run dev
```

Your application will be running and accessible at **http://localhost:5173**.

### Usage

- **Web Application:** [http://localhost:5173](http://localhost:5173)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Common Commands

- **View backend logs:** `docker-compose logs -f backend`
- **Stop all services:** `docker-compose down`

### Restarting Docker & clearing the database volume

If you need to fully restart the backend and reset the Postgres data volume (for example when the DB schema changed or you want a clean DB), run the following from the project root:

```bash
docker compose down
docker volume rm gophora_postgres_data
docker compose up --build
```

What this does:
- `docker compose down` stops and removes the containers and networks.
- `docker volume rm gophora_postgres_data` removes the named Docker volume that stores Postgres data so the database will start fresh.
- `docker compose up --build` rebuilds images and starts the services again.

Run the three commands above before starting the frontend (`npm run dev`) if you want the backend to be restarted with a fresh database.