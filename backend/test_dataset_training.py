import os

from backend.app.database import SessionLocal, KnowledgeBase, import_csv_knowledge_base


CSV_PATH = r"c:\Users\ANANDA VARSHINI\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\ED8FD0A3ABA142AE333E7042A6636AB1F924DBF2\transfers\2026-43\CSE_QA_Dataset.csv"


def test_csv_dataset_imports_into_knowledge_base():
    assert os.path.exists(CSV_PATH), "CSV dataset was not found at the expected path"

    db = SessionLocal()
    try:
        before = db.query(KnowledgeBase).count()
        imported = import_csv_knowledge_base(db, CSV_PATH)
        after = db.query(KnowledgeBase).count()
        assert imported > 0, "No rows were imported from the dataset"
        assert after >= before + 1, "Knowledge base did not increase after import"
    finally:
        db.close()
