#!/usr/bin/env python3
"""
Simple test script for the PDF Management API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_upload_pdf():
    """Test PDF upload endpoint"""
    print("\nTesting PDF upload endpoint...")
    
    data = {
        "filename": "test_document.pdf"
    }
    
    response = requests.post(f"{BASE_URL}/upload_pdf", json=data)
    print(f"Upload PDF: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Upload URL: {result['upload_url'][:50]}...")
        print(f"PDF ID: {result['pdf_id']}")
        print(f"S3 Key: {result['s3_key']}")
        return result['pdf_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_mark_uploaded(pdf_id):
    """Test mark uploaded endpoint"""
    print(f"\nTesting mark uploaded endpoint for ID {pdf_id}...")
    
    response = requests.post(f"{BASE_URL}/mark_uploaded/{pdf_id}")
    print(f"Mark uploaded: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Mark uploaded result: {result['message']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_list_pdfs():
    """Test list PDFs endpoint"""
    print("\nTesting list PDFs endpoint...")
    
    response = requests.get(f"{BASE_URL}/list_pdf")
    print(f"List PDFs: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total PDFs: {result['total_count']}")
        for pdf in result['pdfs']:
            print(f"  - ID: {pdf['id']}, Filename: {pdf['filename']}, Status: {pdf['status']}")
        return result['pdfs']
    else:
        print(f"Error: {response.text}")
        return []

def test_get_pdf(pdf_id):
    """Test get PDF endpoint"""
    print(f"\nTesting get PDF endpoint for ID {pdf_id}...")
    
    response = requests.get(f"{BASE_URL}/get_pdf/{pdf_id}")
    print(f"Get PDF: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"PDF Details: {result['filename']} (ID: {result['id']}, Status: {result['status']})")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_analyze_pdf(pdf_id):
    """Test analyze PDF endpoint"""
    print(f"\nTesting analyze PDF endpoint for ID {pdf_id}...")
    
    response = requests.post(f"{BASE_URL}/analyze_pdf/{pdf_id}")
    print(f"Analyze PDF: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Analysis result: {result['message']}")
        print(f"Vector Index ID: {result['vector_index_id']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_delete_pdf(pdf_id):
    """Test delete PDF endpoint"""
    print(f"\nTesting delete PDF endpoint for ID {pdf_id}...")
    
    response = requests.delete(f"{BASE_URL}/delete_pdf/{pdf_id}")
    print(f"Delete PDF: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Delete result: {result['message']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests"""
    print("PDF Management API Test Suite")
    print("=" * 40)
    
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(5)
    
    # Test health
    if not test_health():
        print("Health check failed. Make sure the API is running.")
        return
    
    # Test upload
    pdf_id = test_upload_pdf()
    if not pdf_id:
        print("Upload test failed.")
        return
    
    # Test list (should show PRE_SIGNED status)
    pdfs = test_list_pdfs()
    
    # Test get
    test_get_pdf(pdf_id)
    
    # Test mark uploaded (simulating successful S3 upload)
    test_mark_uploaded(pdf_id)
    
    # Test list again (should show UPLOADED status)
    test_list_pdfs()
    
    # Test analyze
    test_analyze_pdf(pdf_id)
    
    # Test list again to see PARSED status
    test_list_pdfs()
    
    # Test delete
    test_delete_pdf(pdf_id)
    
    # Test list again to confirm deletion
    test_list_pdfs()
    
    print("\n" + "=" * 40)
    print("Test suite completed!")

if __name__ == "__main__":
    main() 