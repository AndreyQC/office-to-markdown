import pandas as pd
from io import BytesIO
from tabulate import tabulate


def convert_xlsx(file_bytes: bytes, images_dir: str) -> str:
    markdown = []

    xlsx_data = pd.ExcelFile(BytesIO(file_bytes))

    for sheet_name in xlsx_data.sheet_names:
        df = pd.read_excel(xlsx_data, sheet_name=sheet_name, dtype=str)
        df = df.fillna("")

        markdown.append(f"## {sheet_name}\n")

        if not df.empty:
            table_str = tabulate(df, headers="keys", tablefmt="pipe", showindex=False)
            markdown.append(table_str)
            markdown.append("")

    return "\n".join(markdown)
