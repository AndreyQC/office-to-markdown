import os
import fitz
import pdfplumber
from io import BytesIO


def convert_pdf(file_bytes: bytes, images_dir: str) -> str:
    markdown = []

    os.makedirs(images_dir, exist_ok=True)
    image_counter = 1

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    has_text = False
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text().strip()
        if text:
            has_text = True
            break

    if not has_text:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_name = f"img_{image_counter}.{image_ext}"
                    image_path = os.path.join(images_dir, image_name)

                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

                    markdown.append(f"![image](images/{image_name})\n")
                    image_counter += 1
                except Exception:
                    pass

        return "\n".join(markdown)

    for page_num in range(doc.page_count):
        page = doc[page_num]
        markdown.append(f"## Страница {page_num + 1}\n")

        text = page.get_text().strip()
        if text:
            markdown.append(text)
            markdown.append("")

        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf_plumber:
                plumber_page = pdf_plumber.pages[page_num]
                tables = plumber_page.extract_tables()

                if tables:
                    for table in tables:
                        if table and len(table) > 0:
                            table_md = _convert_table(table)
                            if table_md:
                                markdown.append(table_md)
        except Exception:
            pass

        image_list = page.get_images()
        for img in image_list:
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_name = f"img_{image_counter}.{image_ext}"
                image_path = os.path.join(images_dir, image_name)

                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                markdown.append(f"\n![image](images/{image_name})\n")
                image_counter += 1
            except Exception:
                pass

        markdown.append("---\n")

    return "\n".join(markdown)


def _convert_table(table) -> str:
    if not table or len(table) == 0:
        return ""

    result = []

    header = table[0]
    if header:
        result.append(
            "| " + " | ".join([str(cell) if cell else "" for cell in header]) + " |"
        )
        result.append("| " + " | ".join(["---"] * len(header)) + " |")

    for row in table[1:]:
        if row:
            result.append(
                "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |"
            )

    return "\n".join(result) + "\n"
