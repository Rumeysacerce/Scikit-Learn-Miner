# Software Engineering with GenAI: scikit-learn Data Collection

This repository contains the Python scripts used to collect data from the `scikit-learn` repository for the 'Software Engineering with GenAI' course project.

The main goal of the project is to fine-tune Code Large Language Models (CodeLLMs) like **CodeT5+** and **StarCoder2** using data collected from the `scikit-learn` GitHub repository.

## 🎯 Project Tasks

The data collection process for this project is designed to support two mandatory and two optional tasks:

* **Mandatory:**
    1.  **Code Search:** Matching natural language queries (e.g., 'issue' titles) with their corresponding Python code blocks (e.g., 'issue' bodies).
    2.  **Code Repair:** Identifying and fixing buggy code (e.g., 'diff' data from 'fix' commits).

* **Optional:**
    1.  **Bug Classification:** Classifying code changes from Pull Requests based on their labels (e.g., 'Bug').
    2.  **Commit Message Generation:** Automatically generating a commit message based on a code change (diff).

## 🛠️ Setup

Before running the scripts, you need to set up your project.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Rumeysacerce/Scikit-Learn-Miner
    cd Scikit-Learn-Miner
    ```

2.  **Install Requirements:**
    Install the required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```
    (This will install `requests` and `python-dotenv`).

## 🚀 Usage (Step 1: Fetching Metadata)

The `main.py` script collects the list (i.e., "metadata") of issues, pull requests, and commits required for the four tasks listed above.

### 1. Set Up GitHub Token (Mandatory)

To avoid GitHub API rate limits, using a **Personal Access Token (PAT)** is mandatory.

This script is configured to securely read the token from a `.env` file at the project root.

1.  Create a file named **`.env`** in the same folder as `main.py`.
2.  Open the `.env` file and add your token (Do **NOT** use quotes):
    ```
    GITHUB_TOKEN=ghp_YourTokenGoesHere12345
    ```
3.  The included `.gitignore` file will automatically prevent this file from being uploaded to GitHub.

### 2. Run the Script

Once your `.env` file is ready, run the main Python script from your terminal:

```bash
python main.py