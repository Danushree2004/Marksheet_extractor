# 📄 My Technical Approach - Marksheet AI

Building a system that can read any marksheet from any school is actually a pretty tricky problem. Below is an explanation of how I approached it and the decisions I made along the way.

---

## 1. Understanding the Problem

The goal was to build an API that takes a PDF or image of an academic marksheet and gives back organized JSON data. 

**What I wanted to achieve:**
*   **It should work everywhere**: Not just for one specific board, but for any university marksheet.
*   **Extract everything**: Candidate name, roll numbers, and a list of subjects with marks.
*   **Confidence Scores**: I wanted the system to tell me if it thinks it made a mistake.
*   **Avoid AI Hallucinations**: Since this is academic data, we can't have the AI making up numbers.

---

## 2. My Architecture Design

### Why I chose OCR + LLM instead of just sending an image to AI
I spent some time thinking about this and did some tests. I decided on a two-step process: **OCR (EasyOCR) → Text → LLM (Gemini)**.

**Why?**
1.  **Safety**: LLMs are great at understanding context, but they sometimes "fill in the blanks" if an image is blurry. By doing OCR first, I ensure the AI only sees text that actually exists on the page.
2.  **Debugging**: If something goes wrong, I can check the OCR output. If the OCR is bad, I know it's a vision problem. If the OCR is good but the JSON is bad, I know it's a prompt problem.
3.  **Cost**: Using Gemini's text model is cheaper and faster than always using the vision model (though I ended up using Vision for better layout understanding).

### Why EasyOCR?
I tried Tesseract initially, but I found EasyOCR was much easier to set up on my laptop and handled different fonts/watermarks better without needing a lot of "image cleaning" code.

### Why Google Gemini?
I chose **Gemini 1.5 Flash**. 
*   It's free for developers (mostly).
*   It handles JSON output really well.
*   The "Vision" feature helps it see the layout of the table, which is huge for marksheets.

---

## 3. How the Data Flows

1.  **Upload**: The user sends a file. I check if it's too big or the wrong type.
2.  **OCR Stage**: I use EasyOCR to get the raw text. If it's a PDF, I convert the first page to an image first.
3.  **Cleaning**: I remove extra spaces and weird vertical bars that OCR sometimes adds.
4.  **AI Stage**: I send the text (and the image) to Gemini. I gave it a specific "template" so it knows exactly what fields I want.
5.  **Scoring**: I calculate a final 0-1 score based on how well the OCR worked and what the AI thinks.
6.  **Response**: The user gets the final JSON.

---

## 4. The Confidence Score Logic

Setting up the scoring wasn't an exact science, so I came up with a weighted formula that felt "right" after testing a few samples.

**The Formula:**
`0.3 * OCR + 0.5 * AI_Score + 0.2 * Completeness`

*   **50% for AI**: Since Gemini sees the context (like headings and tables), its "felt" confidence is most important.
*   **30% for OCR**: If the OCR read characters with high confidence, the data is likely solid.
*   **20% for Completeness**: If we found 18 out of 20 expected fields, that's better than finding only 5.

---

## 5. How I handled different layouts

Instead of telling the code "look for the name at the top left," I used **Prompt Engineering**. 

I told the AI: *"I have some text from a marksheet. Please find the student's name, their father's name, and their marks for each subject."*

This makes the system **layout-agnostic**. It doesn't matter if the name is at the top, bottom, or in a table—the LLM is smart enough to find the label and the value next to it.

---

## 6. What I actually built (and what I left out)

### Included:
*   Full extraction pipeline (OCR to JSON).
*   Handling both images and PDFs.
*   A "Health" endpoint to check if the server is running.
*   Interactive Swagger UI (thanks to FastAPI).

### Left out (Trade-offs):
*   **Database**: I kept it stateless. It doesn't save your files, which is better for privacy but means you can't look at history.
*   **Multi-page PDFs**: Usually, marksheets are one page, so I focused on making that page perfect first.
*   **Handwriting**: This is much harder to do accurately, so I focused on printed documents.

---

## 7. Personal Reflections & Learnings

**What I learned:**
*   Getting text out of images is easy, but making *sense* of that text is hard. 
*   OCR line-grouping is tricky. I had to write a custom loop to group words that are on the same line horizontally.
*   Pydantic is awesome for making sure your JSON doesn't break.

**What I'd change if I had more time:**
*   I'd add a "Table detection" model to handle complex tables even better.
*   I'd implement a cache so if you upload the same image twice, it doesn't call the AI again.
*   I'd add a beautiful React frontend (I started one but the backend was the main focus).

---

## 8. Conclusion

I think this project shows a solid way to solve document extraction without over-engineering it. It's simple, explainable, and it actually works on real-world samples I tested. 

**Author:** AI Engineer Intern Candidate
**Date:** January 2026
