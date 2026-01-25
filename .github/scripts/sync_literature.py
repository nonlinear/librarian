import os

from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.readers.file.epub import EpubReader
from llama_index.readers.file.pymu_pdf import PyMuPDFReader


def sync_literature():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    literature_dir = os.path.join(project_root, 'literature', 'books')
    storage_dir = os.path.join(project_root, 'literature', 'storage')
    print(f"Indexando arquivos em {literature_dir} ...")
    docs = []
    epub_reader = EpubReader()
    pdf_reader = PyMuPDFReader()
    if not os.path.exists(literature_dir):
        print(f"Diretório não encontrado: {literature_dir}")
        return
    for fname in os.listdir(literature_dir):
        fpath = os.path.join(literature_dir, fname)
        if fname.lower().endswith(".epub"):
            print(f"Lendo EPUB: {fname}")
            docs.extend(epub_reader.load_data(fpath))
        elif fname.lower().endswith(".pdf"):
            print(f"Lendo PDF: {fname}")
            docs.extend(pdf_reader.load_data(fpath))
    print(f"{len(docs)} documentos carregados.")
    if docs:
        index = VectorStoreIndex.from_documents(docs)
        index.storage_context.persist(persist_dir=storage_dir)
        print(f"Index salvo em {storage_dir}.")
    else:
        print("Nenhum documento encontrado para indexar.")

if __name__ == "__main__":
    sync_literature()
