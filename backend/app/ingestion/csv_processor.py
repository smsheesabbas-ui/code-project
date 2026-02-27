import pandas as pd
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal
from ..models.csv_import import ColumnMapping, PreviewRow, ImportStatus

class CSVProcessor:
    def __init__(self):
        self.date_patterns = [
            (r'^\d{4}-\d{2}-\d{2}$', '%Y-%m-%d'),  # YYYY-MM-DD
            (r'^\d{2}/\d{2}/\d{4}$', '%m/%d/%Y'),   # MM/DD/YYYY
            (r'^\d{2}-\d{2}-\d{4}$', '%m-%d-%Y'),   # MM-DD-YYYY
            (r'^\d{2}/\d{2}/\d{4}$', '%d/%m/%Y'),   # DD/MM/YYYY
            (r'^\d{2}-\d{2}-\d{4}$', '%d-%m-%Y'),   # DD-MM-YYYY
        ]
        
        self.amount_patterns = [
            r'^-?\$?\d{1,3}(,\d{3})*(\.\d{2})?$',  # Standard format
            r'^-?\$?\d+(\.\d{2})?$',                # Simple format
            r'^\(\$?\d{1,3}(,\d{3})*(\.\d{2})?\)$', # Parentheses for negative
        ]

    def detect_columns(self, df: pd.DataFrame, sample_size: int = 20) -> Tuple[ColumnMapping, float]:
        """Auto-detect column mappings with confidence score"""
        if len(df) > sample_size:
            sample_df = df.head(sample_size)
        else:
            sample_df = df
        
        mapping = ColumnMapping()
        confidence_scores = []
        
        # Detect date column
        date_col, date_confidence = self._detect_date_column(sample_df)
        if date_col:
            setattr(mapping, 'date', date_col)
            confidence_scores.append(date_confidence)
        
        # Detect description column (longest text column)
        desc_col, desc_confidence = self._detect_description_column(sample_df)
        if desc_col:
            setattr(mapping, 'description', desc_col)
            confidence_scores.append(desc_confidence)
        
        # Detect amount columns
        amount_result = self._detect_amount_columns(sample_df)
        if amount_result['type'] == 'single':
            setattr(mapping, 'amount', amount_result['column'])
            confidence_scores.append(amount_result['confidence'])
        elif amount_result['type'] == 'split':
            setattr(mapping, 'debit', amount_result['debit'])
            setattr(mapping, 'credit', amount_result['credit'])
            confidence_scores.append(amount_result['confidence'])
        
        # Detect balance column
        balance_col, balance_confidence = self._detect_balance_column(sample_df)
        if balance_col:
            setattr(mapping, 'balance', balance_col)
            confidence_scores.append(balance_confidence)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return mapping, overall_confidence

    def _detect_date_column(self, df: pd.DataFrame) -> Tuple[Optional[str], float]:
        """Detect date column and its confidence"""
        best_col = None
        best_confidence = 0.0
        
        for col in df.columns:
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().head(10).astype(str)
                matches = 0
                
                for value in sample_values:
                    for pattern, _ in self.date_patterns:
                        if re.match(pattern, value):
                            matches += 1
                            break
                
                confidence = matches / len(sample_values) if len(sample_values) > 0 else 0
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_col = col
        
        return best_col, best_confidence

    def _detect_description_column(self, df: pd.DataFrame) -> Tuple[Optional[str], float]:
        """Detect description column (longest text column)"""
        best_col = None
        best_avg_length = 0
        
        for col in df.columns:
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().head(10).astype(str)
                avg_length = sum(len(val) for val in sample_values) / len(sample_values) if len(sample_values) > 0 else 0
                
                # Skip if it looks like a date or amount column
                if avg_length > best_avg_length and avg_length > 10:
                    best_avg_length = avg_length
                    best_col = col
        
        confidence = min(best_avg_length / 50, 1.0) if best_col else 0.0
        return best_col, confidence

    def _detect_amount_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect amount columns (single or split debit/credit)"""
        numeric_cols = []
        
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64'] or self._is_amount_column(df[col]):
                numeric_cols.append(col)
        
        # Check for debit/credit split
        debit_col = credit_col = None
        for col in numeric_cols:
            col_lower = col.lower()
            if 'debit' in col_lower or 'withdraw' in col_lower:
                debit_col = col
            elif 'credit' in col_lower or 'deposit' in col_lower:
                credit_col = col
        
        if debit_col and credit_col:
            return {
                'type': 'split',
                'debit': debit_col,
                'credit': credit_col,
                'confidence': 0.9
            }
        
        # Single amount column
        if numeric_cols:
            best_col = numeric_cols[0]
            confidence = 0.85
            return {
                'type': 'single',
                'column': best_col,
                'confidence': confidence
            }
        
        return {'type': 'none', 'confidence': 0.0}

    def _detect_balance_column(self, df: pd.DataFrame) -> Tuple[Optional[str], float]:
        """Detect balance column"""
        for col in df.columns:
            col_lower = col.lower()
            if 'balance' in col_lower and df[col].dtype in ['float64', 'int64']:
                return col, 0.8
        return None, 0.0

    def _is_amount_column(self, series: pd.Series) -> bool:
        """Check if a series contains amount-like values"""
        sample_values = series.dropna().head(10).astype(str)
        matches = 0
        
        for value in sample_values:
            for pattern in self.amount_patterns:
                if re.match(pattern, value):
                    matches += 1
                    break
        
        return matches / len(sample_values) > 0.7 if len(sample_values) > 0 else False

    def parse_amount(self, value: Any) -> Optional[float]:
        """Parse amount value to float"""
        if pd.isna(value):
            return None
        
        str_value = str(value).strip()
        
        # Remove currency symbols and parentheses
        str_value = re.sub(r'[$,]', '', str_value)
        
        # Handle parentheses for negative numbers
        if str_value.startswith('(') and str_value.endswith(')'):
            str_value = '-' + str_value[1:-1]
        
        try:
            return float(str_value)
        except ValueError:
            return None

    def parse_date(self, value: Any, detected_format: Optional[str] = None) -> Optional[str]:
        """Parse date value to ISO format"""
        if pd.isna(value):
            return None
        
        str_value = str(value).strip()
        
        # Try detected format first
        if detected_format:
            try:
                dt = datetime.strptime(str_value, detected_format)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Try all patterns
        for pattern, format_str in self.date_patterns:
            if re.match(pattern, str_value):
                try:
                    dt = datetime.strptime(str_value, format_str)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None

    def generate_preview(self, df: pd.DataFrame, mapping: ColumnMapping, row_limit: int = 20) -> List[PreviewRow]:
        """Generate preview rows based on column mapping"""
        preview_rows = []
        
        for idx, row in df.head(row_limit).iterrows():
            preview_row = PreviewRow(row_number=idx + 1)
            
            # Parse date
            if mapping.date and mapping.date in df.columns:
                date_value = self.parse_date(row[mapping.date])
                preview_row.date = date_value
            
            # Parse description
            if mapping.description and mapping.description in df.columns:
                desc_value = str(row[mapping.description]) if pd.notna(row[mapping.description]) else ""
                preview_row.description = desc_value
            
            # Parse amount
            if mapping.amount and mapping.amount in df.columns:
                amount_value = self.parse_amount(row[mapping.amount])
                preview_row.amount = amount_value
            elif mapping.debit and mapping.credit and mapping.debit in df.columns and mapping.credit in df.columns:
                debit_value = self.parse_amount(row[mapping.debit]) or 0
                credit_value = self.parse_amount(row[mapping.credit]) or 0
                # Debit is negative, credit is positive
                preview_row.amount = credit_value - debit_value
            
            # Parse balance
            if mapping.balance and mapping.balance in df.columns:
                balance_value = self.parse_amount(row[mapping.balance])
                preview_row.balance = balance_value
            
            # Validate row
            validation_errors = []
            if not preview_row.date:
                validation_errors.append("Invalid or missing date")
            if preview_row.amount is None:
                validation_errors.append("Invalid or missing amount")
            if not preview_row.description:
                validation_errors.append("Missing description")
            
            preview_row.validation_errors = validation_errors
            preview_rows.append(preview_row)
        
        return preview_rows

    def normalize_dataframe(self, df: pd.DataFrame, mapping: ColumnMapping) -> pd.DataFrame:
        """Normalize DataFrame based on column mapping"""
        normalized_data = []
        
        for idx, row in df.iterrows():
            normalized_row = {}
            
            # Parse and normalize date
            if mapping.date and mapping.date in df.columns:
                date_value = self.parse_date(row[mapping.date])
                normalized_row['transaction_date'] = date_value
            
            # Parse description
            if mapping.description and mapping.description in df.columns:
                desc_value = str(row[mapping.description]) if pd.notna(row[mapping.description]) else ""
                normalized_row['description'] = desc_value
                normalized_row['normalized_description'] = desc_value.lower().strip()
            
            # Parse amount
            if mapping.amount and mapping.amount in df.columns:
                amount_value = self.parse_amount(row[mapping.amount])
                normalized_row['amount'] = amount_value
            elif mapping.debit and mapping.credit and mapping.debit in df.columns and mapping.credit in df.columns:
                debit_value = self.parse_amount(row[mapping.debit]) or 0
                credit_value = self.parse_amount(row[mapping.credit]) or 0
                normalized_row['amount'] = credit_value - debit_value
            
            # Parse balance
            if mapping.balance and mapping.balance in df.columns:
                balance_value = self.parse_amount(row[mapping.balance])
                normalized_row['balance'] = balance_value
            
            # Add original row number for reference
            normalized_row['row_number'] = idx + 1
            normalized_data.append(normalized_row)
        
        return pd.DataFrame(normalized_data)
