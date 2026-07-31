# Live Sharing & Demo Guide — Power BI Dashboard & GitHub Showcase

This guide explains how to present and share your live Power BI dashboard and complete project with recruiters, hiring managers, and interviewers **without requiring them to download any files or install software**.

---

## Option A: Live Interactive Power BI Web Link (Best for Resumes & LinkedIn)

Publishing your dashboard to **Power BI Service** generates an interactive public web link that allows anyone to click city slicers, filter date ranges, and view live metrics directly in their mobile or desktop web browser.

### Step-by-Step Instructions:

1. **Publish from Power BI Desktop:**
   - Open your dashboard file in Power BI Desktop: `powerbi/Weather_Analytics_Dashboard.pbix`.
   - In the top ribbon (Home tab), click **Publish** ➔ select **My Workspace** ➔ click **Select**.
   - Wait for the success message: *"Publishing to Power BI completed successfully"*.

2. **Generate Public Embed Link in Power BI Service:**
   - Log into **[app.powerbi.com](https://app.powerbi.com)** using your Power BI credentials.
   - Go to **Workspaces** ➔ **My Workspace** ➔ click on **Weather_Analytics_Dashboard**.
   - In the top menu bar, click **File** ➔ **Embed report** ➔ **Publish to web (public)**.
   - Click **Create embed code** ➔ click **Publish**.
   - Copy the generated **Link you can send in email / paste in your resume**:
     ```
     https://app.powerbi.com/view?r=eyJr...
     ```

3. **Where to Add This Link:**
   - **Resume Header:** Add next to your LinkedIn and GitHub: `Live Dashboard: https://app.powerbi.com/...`
   - **LinkedIn Featured Section:** Add as a featured link on your profile.
   - **Cover Letters:** Include as an interactive project proof link.

---

## Option B: Professional GitHub Web Repository (Code & Engineering Proof)

Recruiters and technical interviewers can inspect your complete pipeline architecture, SQL DDL scripts, DAX measure library, and test coverage directly on GitHub:

🔗 **`https://github.com/Jaaveed786/Automated-ETL-Pipeline-Live-Power-BI-Dashboard`**

### What Recruiters See Instantly:
- **`README.md`**: Executive summary, system architecture diagram, tech stack, and quick-start guide.
- **`dax/dax_measures.md`**: 15 production DAX measures (moving averages, YTD, anomaly detection).
- **`sql/`**: Star Schema DDL and analytical SQL views.
- **`src/`**: Modular Python ETL pipeline (extractors, transformers, loaders, quality checks).
- **`tests/`**: 42 automated pytest unit tests.
- **`docs/`**: 30 technical interview Q&As, STAR story guide, resume bullet points, and setup instructions.

---

## Option C: 15-Second Screen Recording GIF in GitHub README

Embedding a animated `.gif` of your dashboard in your GitHub README immediately catches recruiters' attention as soon as they open your repository.

### Step-by-Step Instructions:

1. **Record Dashboard Interaction:**
   - Open your dashboard in Power BI Desktop or web browser.
   - Use a free screen recorder like **Loom**, **ScreenToGif**, or **Windows Game Bar** (`Win + Alt + R`).
   - Record a 15-second clip showing yourself:
     - Clicking the **Dubai** tile on the city slicer (showing visuals filter dynamically).
     - Moving the **Date Range** slider.
     - Hovering over the **7-Day Moving Average** line chart tooltip.

2. **Convert to GIF & Save:**
   - Save the clip as `dashboard_demo.gif` (keep file size < 5 MB for fast loading).
   - Place the GIF file in your project folder at: `docs/dashboard_demo.gif`.

3. **Embed in README:**
   - Add this Markdown line near the top of your `README.md`:
     ```markdown
     ![Live Dashboard Demo](docs/dashboard_demo.gif)
     ```

---

## Summary of Sharing Channels

| Channel | Format | Best Used For |
|---|---|---|
| **Resume & Cover Letter** | Interactive Power BI Web URL | Instant recruiter proof (0 downloads required) |
| **LinkedIn Profile** | GitHub Repo Link + Power BI Link | Profile visibility & hiring manager outreach |
| **Technical Interviews** | GitHub Repo + Architecture Docs | Deep-dive code reviews & system design discussions |
| **Portfolio Website** | Embedded iFrame / GIF + Repo Link | Personal branding showcase |
