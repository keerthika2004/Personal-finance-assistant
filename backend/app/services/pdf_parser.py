import io
import re
import os
import json
import base64
import pandas as pd
import pdfplumber
from datetime import datetime
from typing import List, Dict, Any
from groq import Groq


class StatementParser:
    """Parses bank statements from CSV, PDF, and Image files into structured transaction records."""

    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            return StatementParser._parse_csv(file_content)
        elif filename_lower.endswith(".pdf"):
            return StatementParser._parse_pdf(file_content)
        elif filename_lower.endswith((".png", ".jpg", ".jpeg")):
            return StatementParser._parse_image(file_content, filename_lower)
        else:
            raise ValueError(f"Unsupported file extension: {filename}")

    @staticmethod
    def _parse_csv(file_content: bytes) -> List[Dict[str, Any]]:
        df = pd.read_csv(io.BytesIO(file_content))
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Map common column names
        date_col = next((c for c in df.columns if "date" in c), None)
        desc_col = next((c for c in df.columns if any(k in c for k in ["desc", "merchant", "name", "payee", "details"])), None)
        amount_col = next((c for c in df.columns if "amount" in c or "val" in c), None)
        
        # Support separate Credit / Debit columns if present
        credit_col = next((c for c in df.columns if "credit" in c or "deposit" in c or "in" in c), None)
        debit_col = next((c for c in df.columns if "debit" in c or "withdrawal" in c or "out" in c), None)

        transactions = []
        for idx, row in df.iterrows():
            try:
                date_str = str(row[date_col]).strip() if date_col and pd.notna(row[date_col]) else str(datetime.utcnow().date())
                parsed_date = StatementParser._parse_date(date_str)
                
                desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else "Unknown Transaction"
                
                amount = 0.0
                if amount_col and pd.notna(row[amount_col]):
                    amount = float(str(row[amount_col]).replace("$", "").replace(",", "").strip())
                elif credit_col or debit_col:
                    credit_val = float(str(row[credit_col]).replace("$", "").replace(",", "").strip()) if credit_col and pd.notna(row[credit_col]) else 0.0
                    debit_val = float(str(row[debit_col]).replace("$", "").replace(",", "").strip()) if debit_col and pd.notna(row[debit_col]) else 0.0
                    amount = credit_val - abs(debit_val)

                transactions.append({
                    "date": parsed_date,
                    "raw_description": desc,
                    "amount": amount
                })
            except Exception as e:
                continue

        return transactions

    @staticmethod
    def _parse_pdf(file_content: bytes) -> List[Dict[str, Any]]:
        transactions = []
        
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        date_col = desc_col = amount_col = debit_col = credit_col = -1
                        header_row = None
                        
                        # Search top 5 rows for headers
                        for row in table[:5]:
                            row_text = " ".join([str(c).lower() for c in row if c])
                            if "date" in row_text or "details" in row_text or "description" in row_text or "particulars" in row_text:
                                header_row = row
                                for j, cell in enumerate(row):
                                    if not cell: continue
                                    cell_lower = str(cell).lower().replace("\n", " ")
                                    if "date" in cell_lower and date_col == -1: date_col = j
                                    elif any(k in cell_lower for k in ["desc", "details", "particulars", "narration", "merchant"]) and desc_col == -1: desc_col = j
                                    elif any(k in cell_lower for k in ["debit", "withdrawal", "out"]) and debit_col == -1: debit_col = j
                                    elif any(k in cell_lower for k in ["credit", "deposit", "in"]) and credit_col == -1: credit_col = j
                                    elif ("amount" in cell_lower or "val" in cell_lower) and amount_col == -1 and debit_col == -1 and credit_col == -1: amount_col = j
                                break
                        
                        if date_col == -1 or desc_col == -1:
                            continue  # Cannot parse this table safely
                        
                        start_idx = table.index(header_row) + 1 if header_row in table else 0
                        for row in table[start_idx:]:
                            if len(row) <= max(date_col, desc_col): continue
                            
                            date_str = str(row[date_col]).strip() if row[date_col] else ""
                            if not date_str:
                                continue # Skip empty rows
                                
                            parsed_date = StatementParser._parse_date(date_str)
                            desc = str(row[desc_col]).replace("\n", " ").strip() if row[desc_col] else "Unknown Transaction"
                            
                            amount = 0.0
                            try:
                                if debit_col != -1 and len(row) > debit_col and row[debit_col]:
                                    val_str = str(row[debit_col]).replace("$", "").replace(",", "").replace(" ", "").strip()
                                    if val_str: amount = -abs(float(val_str))
                                elif credit_col != -1 and len(row) > credit_col and row[credit_col]:
                                    val_str = str(row[credit_col]).replace("$", "").replace(",", "").replace(" ", "").strip()
                                    if val_str: amount = abs(float(val_str))
                                elif amount_col != -1 and len(row) > amount_col and row[amount_col]:
                                    val_str = str(row[amount_col]).replace("$", "").replace(",", "").replace(" ", "").strip()
                                    if val_str: amount = float(val_str)
                            except ValueError:
                                pass
                                
                            if amount != 0.0 or desc != "Unknown Transaction":
                                transactions.append({
                                    "date": parsed_date,
                                    "raw_description": desc,
                                    "amount": amount
                                })
                else:
                    # Fallback for PDFs without grid lines
                    text = page.extract_text(layout=True)
                    if not text:
                        continue
                    
                    date_regex = re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})", re.IGNORECASE)
                    amount_regex = re.compile(r"[-+]?\s*\$?\s*[\d,]+\.\d{2}")
                    
                    lines = text.split("\n")
                    current_tx = None
                    
                    for line in lines:
                        date_match = date_regex.search(line)
                        amount_matches = list(amount_regex.finditer(line))
                        
                        if date_match and amount_matches:
                            if current_tx:
                                transactions.append(current_tx)
                                
                            date_str = date_match.group(1)
                            parsed_date = StatementParser._parse_date(date_str)
                            
                            # Avoid picking the Balance column if possible by ignoring the last match if there are multiple matches
                            if len(amount_matches) >= 2:
                                amt_match = amount_matches[-2]
                            else:
                                amt_match = amount_matches[-1]
                                
                            amt_str = amt_match.group(0).replace("$", "").replace("$", "").replace(",", "").replace(" ", "")
                            try:
                                amount = float(amt_str)
                            except ValueError:
                                amount = 0.0
                                
                            desc_start = date_match.end()
                            desc_end = amt_match.start()
                            raw_desc = line[desc_start:desc_end].strip()
                            
                            current_tx = {
                                "date": parsed_date,
                                "raw_description": raw_desc,
                                "amount": amount
                            }
                        elif current_tx and line.strip() and not date_match:
                            # Continuation of description (multiline)
                            current_tx["raw_description"] += " " + line.strip()
                    
                    if current_tx:
                        transactions.append(current_tx)

        return transactions

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
            "%b %d, %Y", "%b %d %Y", "%b %d", "%d/%m/%y", "%m/%d/%y"
        ]
        date_clean = date_str.strip()
        for fmt in formats:
            try:
                dt = datetime.strptime(date_clean, fmt)
                if dt.year == 1900:  # If year omitted
                    dt = dt.replace(year=datetime.utcnow().year)
                return dt
            except ValueError:
                continue
        return datetime.utcnow()

    @staticmethod
    def _parse_image(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Parses an image (JPEG/PNG) of a bank statement using local OCR and Groq LLM."""
        try:
            import pytesseract
            from PIL import Image
            
            # Explicitly set tesseract path for Homebrew on Apple Silicon
            if os.path.exists('/opt/homebrew/bin/tesseract'):
                pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
            elif os.path.exists('/usr/local/bin/tesseract'):
                pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        except ImportError:
            raise ValueError("pytesseract or Pillow is not installed. Required for image parsing.")
            
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        if not groq_api_key or groq_api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY is not set or valid in backend/.env.")

        # OCR the image
        img = Image.open(io.BytesIO(file_content))
        ocr_text = pytesseract.image_to_string(img)
        
        if not ocr_text.strip():
            raise ValueError("Could not extract any text from the image using OCR.")

        client = Groq(api_key=groq_api_key)
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        prompt = (
            "You are a strict data extraction tool. I have OCR'd a bank statement image. "
            "Extract the tabular transaction data from this raw OCR text. "
            "Return ONLY a raw JSON array of objects without any markdown blocks or backticks. "
            "Each object must have the following keys:\n"
            "- date: The date of the transaction\n"
            "- raw_description: The full, complete multiline transaction description.\n"
            "- amount: The transaction amount as a float. IMPORTANT: If it's a Debit/Withdrawal, the amount MUST be negative. If it's a Credit/Deposit, the amount MUST be positive.\n"
            "Do NOT include the running balance as the amount. Only output valid JSON.\n"
            "CRITICAL: ONLY extract transactions that are explicitly present in the OCR text. Do NOT generate example or placeholder transactions. If no transactions are found, return an empty array [].\n\n"
            f"OCR TEXT:\n{ocr_text}"
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2048,
        )

        content = response.choices[0].message.content.strip()
        
        # Clean potential markdown JSON wrapping
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()

        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse LLM output into JSON. Output was: {content[:200]}...")

        transactions = []
        for item in parsed_data:
            date_str = str(item.get("date", ""))
            parsed_date = StatementParser._parse_date(date_str)
            transactions.append({
                "date": parsed_date,
                "raw_description": item.get("raw_description", "Unknown"),
                "amount": float(item.get("amount", 0.0))
            })

        return transactions
