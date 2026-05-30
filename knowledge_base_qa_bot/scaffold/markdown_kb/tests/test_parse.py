import sys
from pathlib import Path

# Add the scaffold/markdown_kb directory to Python path so 'app' can be imported
# Path(__file__).resolve().parents[1] is 'scaffold/markdown_kb/'
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.indexer import parse_markdown

if __name__ == "__main__":
    # Path(__file__).resolve().parents[3] is the project root 'knowledge_base_qa_bot/'
    sample_file = Path(__file__).resolve().parents[3] / "docs" / "refund_policy.md"
    
    print(f"Testing parse_markdown on: {sample_file.resolve()}")
    
    if not sample_file.exists():
        print(f"Error: Could not find sample file at {sample_file.resolve()}")
        sys.exit(1)
        
    # This will invoke your function
    sections = parse_markdown(sample_file)
    
    print(f"\nSuccessfully parsed {len(sections)} sections:")
    for section in sections:
        print(f"- ID: {section.id}")
        print(f"  Path: {' > '.join(section.heading_path)}")
        print(f"  Content: {repr(section.content[:60])}...")

    print("\n--- Programmatic Validation ---")
    try:
        # 1. Validate total section count (including the added H3 section)
        assert len(sections) == 5, f"Expected 5 sections, but got {len(sections)}"
        print("✓ Section count matches exactly 5.")

        # 2. Validate H1 Root Section
        root_sec = next(s for s in sections if s.id == "refund_policy.md#refund-policy")
        assert root_sec.heading == "Refund Policy", f"Expected 'Refund Policy', got '{root_sec.heading}'"
        assert root_sec.heading_path == ["Refund Policy"], f"Expected ['Refund Policy'], got {root_sec.heading_path}"
        assert root_sec.content == "", f"Expected empty content for H1 section, got '{root_sec.content}'"
        print("✓ Root H1 section validated successfully.")

        # 3. Validate Nested H3 Section
        nested_sec = next(s for s in sections if s.id == "refund_policy.md#processing-exceptions")
        assert nested_sec.heading == "Processing Exceptions", f"Expected 'Processing Exceptions', got '{nested_sec.heading}'"
        assert nested_sec.heading_path == ["Refund Policy", "Refund Timeline", "Processing Exceptions"], f"Incorrect heading path: {nested_sec.heading_path}"
        assert "international" in nested_sec.tokens, "Expected 'international' token in H3 tokens"
        assert "are" not in nested_sec.tokens, "Expected stop words like 'are' to be filtered out of tokens"
        print("✓ Nested H3 section and tokenization validated successfully.")

        # 4. Validate Back-propagation H2 Reset Section
        reset_sec = next(s for s in sections if s.id == "refund_policy.md#non-refundable-items")
        assert reset_sec.heading_path == ["Refund Policy", "Non-Refundable Items"], f"Expected reset path, got {reset_sec.heading_path}"
        print("✓ Back-propagation hierarchy reset validated successfully.")

        # 5. Populate global state and run rebuild_stats()
        import app.indexer as indexer
        indexer.sections = sections
        indexer.rebuild_stats()

        # 6. Validate files_indexed (should be exactly 1: refund_policy.md)
        assert indexer.files_indexed == 1, f"Expected 1 file indexed, got {indexer.files_indexed}"
        print("✓ rebuild_stats: files_indexed is exactly 1.")

        # 7. Validate avg_doc_len (should be a reasonable average token length > 0)
        assert indexer.avg_doc_len > 0, "Expected positive average doc length"
        print(f"✓ rebuild_stats: avg_doc_len calculated as {indexer.avg_doc_len:.2f} tokens.")

        # 8. Validate doc_freq for unique rare words vs common terms
        # "gift" only appears in "Non-Refundable Items" section
        assert indexer.doc_freq["gift"] == 1, f"Expected 'gift' doc_freq to be 1, got {indexer.doc_freq['gift']}"
        # "refund" appears in multiple sections
        assert indexer.doc_freq["refund"] > 1, f"Expected 'refund' doc_freq to be > 1, got {indexer.doc_freq['refund']}"
        print("✓ rebuild_stats: doc_freq counts are verified for both rare and common words.")

        # 9. Test write_index_json() with a temporary index file path
        import json
        test_index_path = Path(__file__).resolve().parent / "test_index.json"
        
        # Write the index
        indexer.write_index_json(test_index_path)
        assert test_index_path.exists(), "Expected index.json to be created on disk"
        print("✓ write_index_json: index.json file created on disk.")

        # Read it back and validate the structure
        with test_index_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert "sections" in data, "Expected 'sections' key in index JSON"
        assert "stats" in data, "Expected 'stats' key in index JSON"
        assert len(data["sections"]) == 5, f"Expected 5 serialized sections, got {len(data['sections'])}"
        assert data["stats"]["files_indexed"] == 1, "Expected 1 file indexed in JSON stats"
        assert data["stats"]["sections_indexed"] == 5, "Expected 5 sections indexed in JSON stats"
        print("✓ write_index_json: successfully verified serialized JSON content and structure.")

        # 10. Test load_index_json()
        # Wipe in-memory states to verify loading is what restores them
        indexer.sections = []
        indexer.doc_freq = indexer.Counter()
        indexer.avg_doc_len = 0.0
        indexer.files_indexed = 0
        
        # Load the index back from disk
        loaded_files, loaded_sections = indexer.load_index_json(test_index_path)
        
        # Assert loaded totals match
        assert loaded_files == 1, f"Expected 1 loaded file, got {loaded_files}"
        assert loaded_sections == 5, f"Expected 5 loaded sections, got {loaded_sections}"
        assert len(indexer.sections) == 5, f"Expected 5 in-memory sections after load, got {len(indexer.sections)}"
        
        # Assert statistics were successfully recomputed after loading
        assert indexer.avg_doc_len == 16.60, f"Expected avg_doc_len of 16.60 after load, got {indexer.avg_doc_len}"
        assert indexer.doc_freq["gift"] == 1, "Expected 'gift' token frequency to be restored to 1"
        print("✓ load_index_json: successfully wiped in-memory states, loaded index from disk, and verified full statistics recovery.")

        # Clean up the test file
        test_index_path.unlink()
        print("✓ Cleanup: test_index.json unlinked.")

        # 11. Test build_index() on the real docs directory
        # Wipe state again
        indexer.sections = []
        indexer.doc_freq = indexer.Counter()
        indexer.avg_doc_len = 0.0
        indexer.files_indexed = 0
        
        # Build the entire search database from the real docs/ directory
        real_docs_dir = Path(__file__).resolve().parents[3] / "docs"
        files_count, sections_count = indexer.build_index(real_docs_dir)
        
        # Assert that all 4 documents were indexed
        assert files_count == 4, f"Expected 4 files indexed, got {files_count}"
        assert sections_count > 0, "Expected at least some sections to be indexed"
        
        # Assert that the real index was written to disk
        real_index_path = Path(__file__).resolve().parents[3] / ".kb" / "index.json"
        assert real_index_path.exists(), "Expected real .kb/index.json to be written"
        print(f"✓ build_index: successfully scanned docs/, indexed {files_count} files ({sections_count} sections), and generated the master index at .kb/index.json.")

        # 12. Test search() and bm25_score() ranking
        # Query: "cancellation within 24 hours"
        results = indexer.search("cancellation within 24 hours", k=3)
        assert len(results) > 0, "Expected search results for relevant query"
        
        # The top result must be the Cancellation Window section
        top_section, top_score = results[0]
        assert top_section.id == "refund_policy.md#cancellation-window", f"Expected top result to be 'cancellation-window', got '{top_section.id}'"
        assert top_score > 0, "Expected positive relevance score"
        print(f"✓ search/bm25_score: successfully ranked 'cancellation-window' as top result (score: {top_score:.3f}) for query 'cancellation within 24 hours'.")

        # Query: Out-of-scope query "restaurants nearby"
        out_of_scope_results = indexer.search("restaurants nearby")
        assert len(out_of_scope_results) == 0, f"Expected 0 results for out-of-scope query, got {len(out_of_scope_results)}"
        print("✓ search/bm25_score: successfully returned 0 results for out-of-scope query 'restaurants nearby'.")

        print("\n🎉 ALL PROGRAMMATIC VALIDATIONS PASSED SUCCESSFULLY! 🎉")
    except AssertionError as e:
        print(f"❌ VALIDATION FAILURE: {e}")
        sys.exit(1)
