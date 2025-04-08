# GitHub Setup Guide for AI Study Assistant

This guide will help you deploy the AI Study Assistant project on GitHub and set it up for others to use.

## Step 1: Create a GitHub Repository

1. Log in to your GitHub account
2. Click on the "+" icon in the top right corner and select "New repository"
3. Name your repository (e.g., "ai-study-assistant")
4. Add a description (optional)
5. Choose "Public" or "Private" visibility
6. Initialize the repository with a README (optional)
7. Click "Create repository"

## Step 2: Prepare Your Local Files for GitHub

1. Clone the repository to your local machine:
   ```
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Copy all the project files into this directory:
   - app.py
   - utils/ (folder with all utility files)
   - .streamlit/ (configuration folder)
   - other necessary files

3. Create a requirements.txt file with the following content:
   ```
   streamlit>=1.30.0
   aiohttp>=3.9.1
   anthropic>=0.8.0
   faster-whisper>=0.9.0
   moviepy>=1.0.3
   nbformat>=5.9.2
   nltk>=3.8.1
   openai>=1.3.0
   pypdf2>=3.0.1
   python-docx>=1.0.1
   python-pptx>=0.6.21
   requests>=2.31.0
   speechrecognition>=3.10.0
   trafilatura>=1.6.0
   youtube-transcript-api>=0.6.1
   zipfile36>=0.1.3
   ```

## Step 3: Add Environment Setup Instructions

Create a .env.example file to show users which environment variables they can set:

```
# API Keys (Optional - app has fallback mechanisms)
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Add instructions in the README.md explaining how to set up these environment variables.

## Step 4: Push to GitHub

1. Add your files to the Git repository:
   ```
   git add .
   ```

2. Commit your changes:
   ```
   git commit -m "Initial commit of AI Study Assistant"
   ```

3. Push to GitHub:
   ```
   git push origin main
   ```

## Step 5: Deploy to a Hosting Service (Optional)

You can deploy your Streamlit app to services like:

1. **Streamlit Cloud**:
   - Create an account at https://streamlit.io/cloud
   - Connect your GitHub repository
   - Select the repository and choose the main Python file (app.py)
   - Add any required secrets (API keys)

2. **Heroku**:
   - Create a Procfile with the content: `web: streamlit run app.py --server.port=$PORT`
   - Create a runtime.txt with: `python-3.9.0` (or your preferred version)
   - Deploy from your GitHub repository

3. **Railway, Render, or similar PaaS services**:
   - Connect your GitHub repository
   - Configure the build and start commands according to the service documentation

## Step 6: Document API Key Requirements

Explain to users how to obtain free API keys if they want enhanced functionality:

1. **OpenAI API Key**: https://platform.openai.com/account/api-keys
2. **HuggingFace API Key**: https://huggingface.co/settings/tokens
3. **Anthropic API Key**: https://console.anthropic.com/

Note that these are optional, as the app has fallback mechanisms.

## Step 7: Update README with Usage Instructions

Include clear instructions in your README on:
- How to install requirements
- How to set up API keys (optional)
- How to run the application
- What features are available
- Examples of usage