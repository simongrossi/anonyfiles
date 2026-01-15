# anonyfiles_cli/anonymizer/file_processor_factory.py

from typing import Dict, Type  # Corrected: Added Dict import

from .base_processor import BaseProcessor
from .txt_processor import TxtProcessor
from .csv_processor import CsvProcessor
from .word_processor import DocxProcessor
from .excel_processor import ExcelProcessor
from .pdf_processor import PdfProcessor
from .json_processor import JsonProcessor

PROCESSOR_MAP: Dict[str, Type[BaseProcessor]] = {
    ".txt": TxtProcessor,
    ".csv": CsvProcessor,
    ".docx": DocxProcessor,
    ".xlsx": ExcelProcessor,
    ".pdf": PdfProcessor,
    ".json": JsonProcessor,
}


class FileProcessorFactory:
    """
    Fabrique pour obtenir le processeur de fichier approprié en fonction de l'extension.
    """

    @staticmethod
    def get_processor(file_extension: str) -> BaseProcessor:
        """
        Retourne une instance du processeur de fichier correspondant à l'extension.
        Lève une ValueError si l'extension n'est pas supportée.
        """
        processor_class = PROCESSOR_MAP.get(file_extension.lower())
        if not processor_class:
            raise ValueError(f"Type de fichier non supporté: {file_extension}")
        return processor_class()

    @staticmethod
    def is_extension_supported(file_extension: str) -> bool:
        """Vérifie si une extension de fichier est supportée."""
        return file_extension.lower() in PROCESSOR_MAP
