# -*- coding: utf-8 -*-
"""
Tests for umlaut and special-character support in the PDF/DOCX parser.

Covers:
  - _normalize_text: NFC Unicode normalization
  - read_pdf:  umlaut preservation, combining-char normalization, ocr_language passthrough
  - read_docx: umlaut preservation, ocr_language passthrough
"""

import sys
import inspect
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

from server import _normalize_text


# ---------------------------------------------------------------------------
# _normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText(unittest.TestCase):

    def test_nfc_composes_combining_a_umlaut(self):
        """NFD 'a' + combining diaeresis (U+0308) must compose to NFC U+00E4."""
        nfd = "\u0061\u0308"    # a + combining diaeresis
        self.assertEqual(_normalize_text(nfd), "\xe4")  # ae-umlaut NFC

    def test_nfc_composes_combining_u_umlaut(self):
        """NFD 'u' + combining diaeresis must compose to NFC U+00FC."""
        nfd = "\u0075\u0308"    # u + combining diaeresis
        self.assertEqual(_normalize_text(nfd), "\xfc")  # u-umlaut NFC

    def test_nfc_composes_combining_o_umlaut(self):
        """NFD 'o' + combining diaeresis must compose to NFC U+00F6."""
        nfd = "\u006f\u0308"    # o + combining diaeresis
        self.assertEqual(_normalize_text(nfd), "\xf6")  # o-umlaut NFC

    def test_nfc_composes_combining_capital_A_umlaut(self):
        """NFD 'A' + combining diaeresis must compose to NFC U+00C4."""
        nfd = "\u0041\u0308"    # A + combining diaeresis
        self.assertEqual(_normalize_text(nfd), "\xc4")  # Ae-umlaut NFC

    def test_nfc_preserves_already_composed_umlauts(self):
        """Text already in NFC (composed umlauts) is returned unchanged."""
        text = "Stra\xdfe \xf6ffnet \xdc\xe4u\xdfere \xdcbung"  # Strae... oe... Ueae...ue... Uebung
        self.assertEqual(_normalize_text(text), text)

    def test_nfc_preserves_eszett(self):
        """German sharp-s (U+00DF) passes through unchanged."""
        self.assertEqual(_normalize_text("Stra\xdfe"), "Stra\xdfe")

    def test_nfc_preserves_accented_latin(self):
        """French / Spanish accented characters pass through unchanged."""
        text = "Caf\xe9 na\xefve r\xe9sum\xe9 \xd1o\xf1o"
        self.assertEqual(_normalize_text(text), text)

    def test_nfc_preserves_currency_and_symbols(self):
        """Common symbols (euro, copyright, trademark, section) pass through."""
        text = "\u20ac100 \xa9 \u2122 \xa742"
        self.assertEqual(_normalize_text(text), text)

    def test_empty_string_returns_empty_string(self):
        self.assertEqual(_normalize_text(""), "")

    def test_none_returns_none(self):
        self.assertIsNone(_normalize_text(None))

    def test_plain_ascii_unchanged(self):
        text = "Hello, World! 123"
        self.assertEqual(_normalize_text(text), text)


# ---------------------------------------------------------------------------
# read_pdf
# ---------------------------------------------------------------------------

class TestReadPdfUmlauts(unittest.TestCase):

    def _make_mock_reader(self, text):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = text
        mock_page.images = []

        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        return mock_reader

    def test_umlauts_preserved_in_output(self):
        """\xc4rger \xfcber \xf6ffentliche \xdcberg\xe4nge all survive extraction."""
        from server import read_pdf
        reader = self._make_mock_reader(
            "\xc4rger \xfcber \xf6ffentliche \xdcberg\xe4nge"
        )
        with patch("server.PdfReader", return_value=reader), \
             patch("os.path.exists", return_value=True):
            result = read_pdf("/fake/path.pdf", ocr=False)

        self.assertIn("\xc4rger", result)
        self.assertIn("\xf6ffentliche", result)
        self.assertIn("\xdcberg\xe4nge", result)

    def test_eszett_preserved(self):
        """German \xdf (sharp-s) passes through extraction unchanged."""
        from server import read_pdf
        reader = self._make_mock_reader("Stra\xdfe und Fu\xdfweg")
        with patch("server.PdfReader", return_value=reader), \
             patch("os.path.exists", return_value=True):
            result = read_pdf("/fake/path.pdf", ocr=False)

        self.assertIn("Stra\xdfe", result)
        self.assertIn("Fu\xdfweg", result)

    def test_accented_and_symbol_characters_preserved(self):
        """Accented Latin and common symbols survive the extraction pipeline."""
        from server import read_pdf
        reader = self._make_mock_reader(
            "Caf\xe9 na\xefve r\xe9sum\xe9 \u20ac100 \xa9"
        )
        with patch("server.PdfReader", return_value=reader), \
             patch("os.path.exists", return_value=True):
            result = read_pdf("/fake/path.pdf", ocr=False)

        for token in ["Caf\xe9", "na\xefve", "r\xe9sum\xe9", "\u20ac100", "\xa9"]:
            self.assertIn(token, result)

    def test_combining_characters_normalized_to_nfc(self):
        """NFD text returned by pypdf is normalized to NFC in the result."""
        from server import read_pdf
        nfd_u_umlaut = "\u0075\u0308"   # u + combining diaeresis
        reader = self._make_mock_reader(nfd_u_umlaut)
        with patch("server.PdfReader", return_value=reader), \
             patch("os.path.exists", return_value=True):
            result = read_pdf("/fake/path.pdf", ocr=False)

        self.assertIn("\xfc", result)   # NFC u-umlaut

    def test_ocr_language_passed_to_tesseract(self):
        """ocr_language is forwarded to pytesseract.image_to_string."""
        from server import read_pdf

        mock_img = MagicMock()
        mock_image_obj = MagicMock()
        mock_image_obj.data = b"\x89PNG\r\n\x1a\n"

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_page.images = [mock_image_obj]

        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]

        with patch("server.PdfReader", return_value=mock_reader), \
             patch("os.path.exists", return_value=True), \
             patch("server.Image.open", return_value=mock_img), \
             patch("server.pytesseract.image_to_string", return_value="\xc4rger") as mock_tess:
            result = read_pdf("/fake/path.pdf", ocr=True, ocr_language="deu+eng")

        mock_tess.assert_called_once_with(mock_img, lang="deu+eng")
        self.assertIn("\xc4rger", result)

    def test_default_ocr_language_is_deu_plus_eng(self):
        """Default value of ocr_language parameter must be 'deu+eng'."""
        from server import read_pdf
        sig = inspect.signature(read_pdf)
        self.assertEqual(sig.parameters["ocr_language"].default, "deu+eng")


# ---------------------------------------------------------------------------
# read_docx
# ---------------------------------------------------------------------------

class TestReadDocxUmlauts(unittest.TestCase):

    def _make_mock_doc(self, text):
        mock_para = MagicMock()
        mock_para.text = text
        mock_para.style.name = "Normal"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        mock_doc.part.rels = {}
        return mock_doc

    def test_umlauts_preserved_in_output(self):
        """M\xfcller, G\xfcnther und B\xe4rbel all appear in the result."""
        from server import read_docx
        doc = self._make_mock_doc("M\xfcller, G\xfcnther und B\xe4rbel")
        with patch("server.Document", return_value=doc), \
             patch("os.path.exists", return_value=True):
            result = read_docx("/fake/path.docx", ocr=False)

        self.assertIn("M\xfcller", result)
        self.assertIn("G\xfcnther", result)
        self.assertIn("B\xe4rbel", result)

    def test_special_characters_preserved(self):
        """Euro sign and accented characters survive DOCX extraction."""
        from server import read_docx
        doc = self._make_mock_doc("\u20ac1.000 \xb7 r\xe9sum\xe9 \xb7 na\xefve")
        with patch("server.Document", return_value=doc), \
             patch("os.path.exists", return_value=True):
            result = read_docx("/fake/path.docx", ocr=False)

        self.assertIn("\u20ac1.000", result)
        self.assertIn("r\xe9sum\xe9", result)
        self.assertIn("na\xefve", result)

    def test_ocr_language_passed_to_tesseract(self):
        """ocr_language is forwarded to pytesseract in the DOCX OCR path."""
        from server import read_docx

        mock_img = MagicMock()
        mock_rel = MagicMock()
        mock_rel.reltype = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        )
        mock_rel.target_part.blob = b"\x89PNG\r\n\x1a\n"

        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_doc.tables = []
        mock_doc.part.rels = {"rId1": mock_rel}

        with patch("server.Document", return_value=mock_doc), \
             patch("os.path.exists", return_value=True), \
             patch("server.Image.open", return_value=mock_img), \
             patch("server.pytesseract.image_to_string", return_value="\xc4rger") as mock_tess:
            read_docx("/fake/path.docx", ocr=True, ocr_language="deu")

        mock_tess.assert_called_once_with(mock_img, lang="deu")

    def test_default_ocr_language_is_deu_plus_eng(self):
        """Default value of ocr_language parameter must be 'deu+eng'."""
        from server import read_docx
        sig = inspect.signature(read_docx)
        self.assertEqual(sig.parameters["ocr_language"].default, "deu+eng")


if __name__ == "__main__":
    unittest.main(verbosity=2)
