#!/usr/bin/env python3
"""
Test CSV paste functionality
"""

import requests
import io

BASE_URL = "http://localhost:8000/api/v1"

def test_pasted_csv():
    """Test CSV data pasted as text"""
    
    # Sample CSV data (same as in the file you showed)
    csv_data = """Date,Description,Amount,Balance,Type
01/01/2024,Salary Deposit,2500.00,2500.00,Revenue
01/02/2024,Grocery Store,-125.50,2374.50,Expense
01/03/2024,Gas Station,-45.00,2329.50,Expense
01/04/2024,Restaurant,-32.75,2296.75,Expense
01/05/2024,Freelance Project,500.00,2796.75,Revenue
01/06/2024,Electric Bill,-89.00,2707.75,Expense
01/07/2024,Coffee Shop,4.50,2712.25,Expense
01/08/2024,Online Course,-99.00,2613.25,Expense
01/09/2024,Client Payment,1200.00,3813.25,Revenue
01/10/2024,Internet Bill,-60.00,3753.25,Expense"""
    
    print("Testing CSV paste functionality...")
    print(f"CSV Data Length: {len(csv_data)} characters")
    
    try:
        # Create a file-like object from the CSV text
        csv_file = io.StringIO(csv_data)
        
        # Convert to bytes for the upload
        csv_bytes = csv_data.encode('utf-8')
        
        # Upload as if it were a file
        files = {'file': ('pasted_data.csv', io.BytesIO(csv_bytes), 'text/csv')}
        response = requests.post(f"{BASE_URL}/imports/upload", files=files)
        
        print(f"Upload Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Upload Response: {data}")
            
            import_id = data.get('id')
            if import_id:
                print(f"Import ID: {import_id}")
                
                # Get preview
                preview_response = requests.get(f"{BASE_URL}/imports/{import_id}/preview")
                print(f"Preview Status: {preview_response.status_code}")
                
                if preview_response.status_code == 200:
                    preview_data = preview_response.json()
                    print(f"Rows detected: {preview_data.get('total_rows', 0)}")
                    print(f"Detection confidence: {preview_data.get('detected_columns', {}).get('detection_confidence', 0):.2f}")
                    
                    detected_columns = preview_data.get('detected_columns', {}).get('columns', {})
                    if detected_columns:
                        print("Detected columns:")
                        for col_name, col_info in detected_columns.items():
                            print(f"  {col_name}: {col_info.get('source_column')} (confidence: {col_info.get('confidence', 0):.2f})")
                    
                    return True
                else:
                    print(f"Preview Error: {preview_response.text}")
            else:
                print("No import ID in response")
        else:
            print(f"Upload Error: {response.text}")
            
        return False
        
    except Exception as e:
        print(f"Test Error: {e}")
        return False

if __name__ == "__main__":
    print("CashFlow AI - CSV Paste Test")
    print("=" * 40)
    
    success = test_pasted_csv()
    
    if success:
        print("\nCSV paste functionality works!")
    else:
        print("\nCSV paste functionality failed!")
