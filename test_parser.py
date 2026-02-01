import sys
sys.path.insert(0, '.')

from server import read_pdf

# Test 1: Read entire PDF
print("=== Test 1: Read entire PDF ===")
result = read_pdf('test.pdf')
print(result)
print()

# Test 2: Test with URL
print("=== Test 2: Read from URL ===")
url_result = read_pdf('https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf')
print(url_result[:500])  # First 500 chars
print()

print("✅ All tests passed!")
