import pandas as pd
import re
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from app.core.config import settings


class CSVProcessor:
    def __init__(self):
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # DD.MM.YYYY
        ]
        
        self.amount_patterns = [
            r'^-?\$?\d{1,3}(,\d{3})*(\.\d{2})?$',  # $1,234.56
            r'^-?\d{1,3}(,\d{3})*(\.\d{2})?$',    # 1,234.56
            r'^-?\$?\d+\.\d{2}$',                  # $123.45
            r'^-?\d+$',                            # 123
            r'^\(\$?\d{1,3}(,\d{3})*(\.\d{2})?\)$',  # (123.45)
        ]

    def detect_columns(self, df: pd.DataFrame, sample_size: int = 20) -> Dict[str, Any]:
        """Detect column mappings using heuristics"""
        sample_df = df.head(sample_size)
        detected = {}
        unmapped = []
        
        # Detect date column
        date_column = self._detect_date_column(sample_df)
        if date_column:
            detected["date"] = {
                "source_column": date_column,
                "confidence": self._calculate_date_confidence(sample_df[date_column]),
                "format": self._detect_date_format(sample_df[date_column])
            }
        
        # Detect amount columns
        amount_result = self._detect_amount_columns(sample_df)
        if amount_result:
            detected.update(amount_result)
        
        # Detect description column
        description_column = self._detect_description_column(sample_df)
        if description_column:
            detected["description"] = {
                "source_column": description_column,
                "confidence": self._calculate_description_confidence(sample_df[description_column])
            }
        
        # Detect balance column
        balance_column = self._detect_balance_column(sample_df)
        if balance_column:
            detected["balance"] = {
                "source_column": balance_column,
                "confidence": self._calculate_balance_confidence(sample_df[balance_column])
            }
        
        # Find unmapped columns
        mapped_columns = {info["source_column"] for info in detected.values()}
        unmapped = [col for col in df.columns if col not in mapped_columns]
        
        # Calculate overall confidence
        confidence_scores = [info.get("confidence", 0) for info in detected.values()]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            "detection_confidence": overall_confidence,
            "columns": detected,
            "unmapped_columns": unmapped,
            "requires_manual_input": overall_confidence < 0.85
        }

    def _detect_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect date column"""
        for col in df.columns:
            if self._is_date_column(df[col]):
                return col
        return None

    def _is_date_column(self, series: pd.Series) -> bool:
        """Check if series contains dates"""
        non_null = series.dropna()
        if len(non_null) < 3:
            return False
        
        date_count = 0
        for value in non_null.head(10):
            if self._looks_like_date(str(value)):
                date_count += 1
        
        return date_count / len(non_null.head(10)) > 0.7

    def _looks_like_date(self, value: str) -> bool:
        """Check if string looks like a date"""
        for pattern in self.date_patterns:
            if re.match(pattern, value.strip()):
                return True
        return False

    def _detect_date_format(self, series: pd.Series) -> str:
        """Detect date format"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return "unknown"
        
        sample = str(non_null.iloc[0])
        if '/' in sample:
            return "MM/DD/YYYY"
        elif '-' in sample and sample.startswith(str(datetime.now().year)[:2]):
            return "YYYY-MM-DD"
        elif '-' in sample:
            return "MM-DD-YYYY"
        elif '.' in sample:
            return "DD.MM.YYYY"
        return "unknown"

    def _detect_amount_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect amount columns (single amount or debit/credit)"""
        amount_columns = []
        debit_columns = []
        credit_columns = []
        
        for col in df.columns:
            col_type = self._analyze_amount_column(df[col])
            if col_type == "amount":
                amount_columns.append(col)
            elif col_type == "debit":
                debit_columns.append(col)
            elif col_type == "credit":
                credit_columns.append(col)
        
        if amount_columns:
            return {
                "amount": {
                    "source_column": amount_columns[0],
                    "confidence": self._calculate_amount_confidence(df[amount_columns[0]])
                }
            }
        elif debit_columns and credit_columns:
            return {
                "debit": {
                    "source_column": debit_columns[0],
                    "confidence": self._calculate_amount_confidence(df[debit_columns[0]])
                },
                "credit": {
                    "source_column": credit_columns[0],
                    "confidence": self._calculate_amount_confidence(df[credit_columns[0]])
                },
                "detected_format": "debit_credit"
            }
        
        return {}

    def _analyze_amount_column(self, series: pd.Series) -> Optional[str]:
        """Analyze if column is amount, debit, or credit"""
        non_null = series.dropna()
        if len(non_null) < 3:
            return None
        
        # Check for amount patterns
        amount_matches = 0
        for value in non_null.head(10):
            if self._looks_like_amount(str(value)):
                amount_matches += 1
        
        if amount_matches / len(non_null.head(10)) > 0.7:
            # Determine if it's debit or credit based on column name
            col_name = series.name.lower()
            if 'debit' in col_name or 'withdraw' in col_name:
                return "debit"
            elif 'credit' in col_name or 'deposit' in col_name:
                return "credit"
            else:
                return "amount"
        
        return None

    def _looks_like_amount(self, value: str) -> bool:
        """Check if string looks like an amount"""
        value = value.strip().replace('$', '').replace(',', '')
        
        for pattern in self.amount_patterns:
            if re.match(pattern, value):
                return True
        
        return False

    def _calculate_date_confidence(self, series: pd.Series) -> float:
        """Calculate confidence score for date column"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0.0
        
        date_count = sum(1 for value in non_null.head(10) if self._looks_like_date(str(value)))
        return date_count / len(non_null.head(10))

    def _calculate_description_confidence(self, series: pd.Series) -> float:
        """Calculate confidence score for description column"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0.0
        
        # Description should be text and relatively long
        text_count = 0
        for value in non_null.head(10):
            str_val = str(value)
            if len(str_val) > 5 and not self._looks_like_date(str_val) and not self._looks_like_amount(str_val):
                text_count += 1
        
        return text_count / len(non_null.head(10))

    def _calculate_amount_confidence(self, series: pd.DataFrame) -> float:
        """Calculate confidence score for amount column"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0.0
        
        amount_count = sum(1 for value in non_null.head(10) if self._looks_like_amount(str(value)))
        return amount_count / len(non_null.head(10))

    def _calculate_balance_confidence(self, series: pd.DataFrame) -> float:
        """Calculate confidence score for balance column"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0.0
        
        # Balance should be numeric and often positive
        balance_count = 0
        for value in non_null.head(10):
            str_val = str(value)
            if self._looks_like_amount(str_val):
                try:
                    num_val = float(str_val.replace('$', '').replace(',', '').replace('(', '').replace(')', ''))
                    if num_val >= 0:  # Balance is usually positive
                        balance_count += 1
                except:
                    pass
        
        return balance_count / len(non_null.head(10))

    def _detect_description_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect description column (longest text column)"""
        best_col = None
        max_avg_length = 0
        
        for col in df.columns:
            if self._is_text_column(df[col]):
                avg_length = df[col].astype(str).str.len().mean()
                if avg_length > max_avg_length and avg_length > 10:
                    max_avg_length = avg_length
                    best_col = col
        
        return best_col

    def _is_text_column(self, series: pd.Series) -> bool:
        """Check if series contains text data"""
        non_null = series.dropna()
        if len(non_null) < 3:
            return False
        
        # Not date or amount
        sample = str(non_null.iloc[0])
        return not self._looks_like_date(sample) and not self._looks_like_amount(sample)

    def _detect_balance_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect balance column"""
        for col in df.columns:
            if self._is_balance_column(df[col]):
                return col
        return None

    def _is_balance_column(self, series: pd.Series) -> bool:
        """Check if series contains balance data"""
        non_null = series.dropna()
        if len(non_null) < 3:
            return False
        
        # Balance should be numeric and often positive
        balance_count = 0
        for value in non_null.head(10):
            str_val = str(value)
            if self._looks_like_amount(str_val):
                try:
                    num_val = float(str_val.replace('$', '').replace(',', '').replace('(', '').replace(')', ''))
                    if num_val >= 0:
                        balance_count += 1
                except:
                    pass
        
        return balance_count / len(non_null.head(10)) > 0.6

    def normalize_amount(self, value: str, debit_value: str = None, credit_value: str = None) -> float:
        """Normalize amount to signed float"""
        if debit_value is not None and credit_value is not None:
            # Handle debit/credit columns
            debit = self._parse_amount(debit_value) if debit_value else 0
            credit = self._parse_amount(credit_value) if credit_value else 0
            return credit - debit  # Credit positive, debit negative
        else:
            # Handle single amount column
            return self._parse_amount(value)

    def _parse_amount(self, value: str) -> float:
        """Parse amount string to float"""
        if not value or value == '':
            return 0.0
        
        # Remove common formatting
        clean_value = str(value).strip().replace('$', '').replace(',', '')
        
        # Handle parentheses for negative numbers
        if clean_value.startswith('(') and clean_value.endswith(')'):
            clean_value = '-' + clean_value[1:-1]
        
        # Handle trailing minus
        if clean_value.endswith('-'):
            clean_value = '-' + clean_value[:-1]
        
        try:
            return float(clean_value)
        except ValueError:
            return 0.0

    def parse_date(self, date_str: str, date_format: str) -> datetime:
        """Parse date string based on detected format"""
        date_str = str(date_str).strip()
        
        if date_format == "MM/DD/YYYY":
            return datetime.strptime(date_str, "%m/%d/%Y")
        elif date_format == "MM-DD-YYYY":
            return datetime.strptime(date_str, "%m-%d-%Y")
        elif date_format == "YYYY-MM-DD":
            return datetime.strptime(date_str, "%Y-%m-%d")
        elif date_format == "DD.MM.YYYY":
            return datetime.strptime(date_str, "%d.%m.%Y")
        else:
            # Try common formats
            formats = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d.%m.%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            raise ValueError(f"Unable to parse date: {date_str}")

    def normalize_description(self, description: str) -> str:
        """Normalize description text"""
        if not description:
            return ""
        
        # Clean up whitespace and convert to title case
        desc = str(description).strip()
        desc = ' '.join(desc.split())  # Normalize whitespace
        
        return desc
