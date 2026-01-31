# Deployment Guide: JEE Buddy

This guide explains how to put your app online so anyone can use it.

## 1. Push to GitHub (Save your Code)
You need to put your code on GitHub first.

1.  Go to **[GitHub.com](https://github.com/)** and create a **New Repository**.
    *   **Repository Name:** `jee-buddy`
    *   **Public/Private:** Private is better for now (keeps your ideas safe).
    *   Click **Create repository**.

2.  Open your **Command Prompt** (Terminal) in the project folder and run these 5 commands one by one:

    ```bash
    git init
    git add .
    git commit -m "Initial launch version"
    git branch -M main
    # REPLACE THE URL BELOW WITH YOUR NEW GITHUB REPO URL
    git remote add origin https://github.com/<YOUR-USERNAME>/jee-buddy.git
    git push -u origin main
    ```

## 2. Deploy to Vercel (Put it Online)
Vercel will host your app for free.

1.  Go to **[Vercel.com](https://vercel.com/)** and Sign Up (using GitHub is easiest).
2.  Click **"Add New..."** -> **"Project"**.
3.  You will see your `jee-buddy` repo. Click **Import**.
4.  **Configure Project:**
    *   **Framework Preset:** Leave as "Other" (It detects Python automatically).
    *   **Root Directory:** Leave as `./` (default).

5.  **Environment Variables (Important!)**
    Click on "Environment Variables" and add these two:
    
    | Name | Value |
    | :--- | :--- |
    | `OPENAI_API_KEY` | (Copy from your `.env` file) |
    | `MONGO_URI` | (Copy from your `.env` file) |

6.  Click **Deploy**.

## 3. Done! 🚀
Vercel will build your site (takes ~1 minute).
Once done, it will give you a link (e.g., `jee-buddy.vercel.app`).
Share that link with your friends!
