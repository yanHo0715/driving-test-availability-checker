## Driving Test Availability Checker

A small desktop tool that automatically monitors DVSA driving test cancellations, alerts you when availability changes, and runs quietly in the background.

**Personal use only.**

DVSA actively blocks excessive automation. Use responsibly and at your own risk.

## Purpose
Built to solve a real personal problem and explore how AI tools can support development and automation.

## Tech Stack
- Language: Python
- Tools: PyCharm, ChatGPT
- Environment: Local / Linux terminal

## How It Works

1. You manually log in to the DVSA website

2. You select:
- the button area to click
- the message area to monitor

3. The program:
- clicks the button at random intervals
- takes screenshots
- triggers an alarm if dates matched

4. You stop the alarm or exit via the tray icon

## AI Usage
ChatGPT was used to:
- Help design the initial logic
- Explain unfamiliar APIs and errors
- Refactor and simplify code
All AI-generated code was reviewed, tested, and adapted.

## Requirment
- Python 3.10+
- Google Chrome (or any browser you manually open)
- Tesseract OCR
