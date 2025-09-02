from PIL import Image
import docx2txt
import PyPDF2


def read_file_content(uploaded_file):
    """
    Read uploaded file and return (content, file_type).
    Supports images, text, docx, and pdf.
    """
    file_type = uploaded_file.name.split(".")[-1].lower()

    try:
        if file_type in ["jpg", "jpeg", "png"]:
            return Image.open(uploaded_file), file_type

        elif file_type == "txt":
            return uploaded_file.getvalue().decode("utf-8"), file_type

        elif file_type in ["doc", "docx"]:
            return docx2txt.process(uploaded_file), file_type

        elif file_type == "pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
            return text.strip(), file_type

        else:
            return "Unsupported file type", "unsupported"

    except Exception as e:
        return f"❌ Error reading file: {e}", "error"
