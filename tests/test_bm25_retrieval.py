import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.bm25_store import BM25Index

def test_bm25_exact_keyword_matching():
    index = BM25Index()
    chunks = [
        {
            "text": "System error code ERR_CONN_REFUSED encountered during socket handshake.",
            "metadata": {"document_id": 10, "chunk_id": "doc_10_chk_0", "page": 1, "source": "logs.txt"}
        },
        {
            "text": "User profile settings updated successfully in local SQLite storage.",
            "metadata": {"document_id": 10, "chunk_id": "doc_10_chk_1", "page": 2, "source": "logs.txt"}
        }
    ]
    index.add_chunks(chunks)

    results = index.search("ERR_CONN_REFUSED", top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "doc_10_chk_0"
    assert "ERR_CONN_REFUSED" in results[0].text
    assert results[0].retrieval_method == "bm25"
    assert results[0].score > 0.0

def test_bm25_serialization(tmp_path):
    index = BM25Index()
    index.add_chunks([{
        "text": "FastAPI REST API endpoints with Pydantic validation schemas.",
        "metadata": {"document_id": 5, "chunk_id": "doc_5_chk_0", "page": 1, "source": "api.txt"}
    }])

    save_file = os.path.join(tmp_path, "bm25_test.json")
    index.save_to_json(save_file)
    assert os.path.exists(save_file)

    loaded_index = BM25Index.load_from_json(save_file)
    assert loaded_index is not None
    assert loaded_index.doc_count == 1
    res = loaded_index.search("FastAPI", top_k=1)
    assert len(res) == 1
    assert res[0].chunk_id == "doc_5_chk_0"
