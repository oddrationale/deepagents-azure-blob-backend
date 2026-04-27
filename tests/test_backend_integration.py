"""Integration tests for AzureBlobBackend (requires Azurite)."""

from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.integration


class TestWrite:
    async def test_write_new_file(self, backend):
        result = await backend.awrite("/hello.txt", "Hello, World!")
        assert result.error is None
        assert result.path == "/hello.txt"
        assert result.files_update is None

    async def test_write_existing_file_errors(self, backend):
        await backend.awrite("/exists.txt", "content")
        result = await backend.awrite("/exists.txt", "new content")
        assert result.error is not None
        assert "already exists" in result.error

    async def test_concurrent_write_allows_only_one_success(self, backend):
        results = await asyncio.gather(
            backend.awrite("/race.txt", "first"),
            backend.awrite("/race.txt", "second"),
        )

        succeeded = [result for result in results if result.error is None]
        failed = [result for result in results if result.error is not None]

        assert len(succeeded) == 1
        assert len(failed) == 1
        assert "already exists" in failed[0].error


class TestRead:
    async def test_read_returns_numbered_lines(self, backend):
        await backend.awrite("/test.txt", "line one\nline two\nline three")
        result = await backend.aread("/test.txt")
        assert result.error is None
        assert result.file_data is not None
        content = result.file_data["content"]
        assert "1\tline one" in content
        assert "2\tline two" in content
        assert "3\tline three" in content

    async def test_read_with_offset_and_limit(self, backend):
        lines = "\n".join(f"line {i}" for i in range(1, 11))
        await backend.awrite("/lines.txt", lines)
        result = await backend.aread("/lines.txt", offset=2, limit=3)
        assert result.error is None
        assert result.file_data is not None
        content = result.file_data["content"]
        assert "3\tline 3" in content
        assert "4\tline 4" in content
        assert "5\tline 5" in content
        assert "1\tline 1" not in content

    async def test_read_nonexistent_file(self, backend):
        result = await backend.aread("/nope.txt")
        assert result.error is not None
        assert "not found" in result.error.lower()

    async def test_read_empty_file(self, backend):
        await backend.awrite("/empty.txt", "")
        result = await backend.aread("/empty.txt")
        assert result.error is None
        assert result.file_data is not None
        assert "empty" in result.file_data["content"].lower()


class TestEdit:
    async def test_edit_replaces_string(self, backend):
        await backend.awrite("/edit.txt", "Hello World")
        result = await backend.aedit("/edit.txt", "World", "Universe")
        assert result.error is None
        assert result.path == "/edit.txt"
        assert result.occurrences == 1
        assert result.files_update is None

        content = await backend.aread("/edit.txt")
        assert content.file_data is not None
        assert "Universe" in content.file_data["content"]

    async def test_edit_nonexistent_file(self, backend):
        result = await backend.aedit("/nope.txt", "old", "new")
        assert result.error is not None
        assert "not found" in result.error.lower()

    async def test_edit_string_not_found(self, backend):
        await backend.awrite("/edit2.txt", "Hello World")
        result = await backend.aedit("/edit2.txt", "Nonexistent", "Replacement")
        assert result.error is not None
        assert "not found" in result.error.lower()

    async def test_edit_multiple_occurrences_without_replace_all(self, backend):
        await backend.awrite("/multi.txt", "aaa bbb aaa")
        result = await backend.aedit("/multi.txt", "aaa", "ccc")
        assert result.error is not None
        assert "2 times" in result.error

    async def test_edit_replace_all(self, backend):
        await backend.awrite("/multi2.txt", "aaa bbb aaa")
        result = await backend.aedit("/multi2.txt", "aaa", "ccc", replace_all=True)
        assert result.error is None
        assert result.occurrences == 2

        content = await backend.aread("/multi2.txt")
        assert content.file_data is not None
        assert "ccc" in content.file_data["content"]
        assert "aaa" not in content.file_data["content"]


class TestLsInfo:
    async def test_ls_files_in_directory(self, backend):
        await backend.awrite("/src/main.py", "print('hello')")
        await backend.awrite("/src/utils.py", "# utils")
        infos = await backend.als_info("/src")
        paths = [i["path"] for i in infos]
        assert "/src/main.py" in paths
        assert "/src/utils.py" in paths

    async def test_ls_synthesizes_directories(self, backend):
        await backend.awrite("/project/src/main.py", "code")
        await backend.awrite("/project/README.md", "readme")
        infos = await backend.als_info("/project")
        paths = [i["path"] for i in infos]
        # Should have README.md as file and src/ as directory
        assert "/project/README.md" in paths
        dir_entries = [i for i in infos if i.get("is_dir")]
        dir_paths = [d["path"] for d in dir_entries]
        assert "/project/src/" in dir_paths

    async def test_ls_nonexistent_returns_empty(self, backend):
        infos = await backend.als_info("/nonexistent")
        assert infos == []


class TestGlobInfo:
    async def test_glob_star_pattern(self, backend):
        await backend.awrite("/src/main.py", "code")
        await backend.awrite("/src/utils.py", "utils")
        await backend.awrite("/src/readme.md", "docs")
        infos = await backend.aglob_info("*.py", "/src")
        paths = [i["path"] for i in infos]
        assert "/src/main.py" in paths
        assert "/src/utils.py" in paths
        assert "/src/readme.md" not in paths

    async def test_glob_recursive(self, backend):
        await backend.awrite("/project/src/main.py", "code")
        await backend.awrite("/project/src/lib/helpers.py", "helpers")
        await backend.awrite("/project/docs/guide.md", "guide")
        infos = await backend.aglob_info("**/*.py", "/project")
        paths = [i["path"] for i in infos]
        assert "/project/src/main.py" in paths
        assert "/project/src/lib/helpers.py" in paths
        assert "/project/docs/guide.md" not in paths


class TestGrepRaw:
    async def test_grep_finds_pattern(self, backend):
        await backend.awrite("/search/file1.py", "import os\nimport sys")
        await backend.awrite("/search/file2.py", "print('hello')")
        matches = await backend.agrep_raw("import", "/search")
        assert isinstance(matches, list)
        assert len(matches) == 2
        paths = [m["path"] for m in matches]
        assert "/search/file1.py" in paths

    async def test_grep_with_glob_filter(self, backend):
        await backend.awrite("/mixed/code.py", "import os")
        await backend.awrite("/mixed/notes.md", "import notes")
        matches = await backend.agrep_raw("import", "/mixed", glob="*.py")
        assert isinstance(matches, list)
        paths = [m["path"] for m in matches]
        assert "/mixed/code.py" in paths
        assert "/mixed/notes.md" not in paths

    async def test_grep_with_recursive_path_glob_filter(self, backend):
        await backend.awrite("/src/top.py", "import os")
        await backend.awrite("/src/nested/deep.py", "import sys")
        matches = await backend.agrep_raw("import", "/", glob="src/*/*.py")

        assert isinstance(matches, list)
        paths = [m["path"] for m in matches]
        assert "/src/nested/deep.py" in paths
        assert "/src/top.py" not in paths

    async def test_grep_no_matches(self, backend):
        await backend.awrite("/grep_empty/file.txt", "nothing here")
        matches = await backend.agrep_raw("ZZZZZ", "/grep_empty")
        assert isinstance(matches, list)
        assert len(matches) == 0


class TestUploadDownload:
    async def test_roundtrip(self, backend):
        data = b"binary content \x00\x01\x02"
        upload_responses = await backend.aupload_files([("/bin/data.bin", data)])
        assert upload_responses[0].error is None

        download_responses = await backend.adownload_files(["/bin/data.bin"])
        assert download_responses[0].error is None
        assert download_responses[0].content == data

    async def test_download_nonexistent(self, backend):
        responses = await backend.adownload_files(["/nope/file.bin"])
        assert responses[0].error == "file_not_found"
        assert responses[0].content is None


class TestSyncWrappersFromAsync:
    """Sync wrappers must work when invoked from a worker thread spawned by
    `asyncio.to_thread` after the cached client has already been initialised
    in the main event loop. Regression test for issue #29.
    """

    async def test_sync_wrappers_after_async_init(self, backend):
        # Lazily initialise the cached ContainerClient inside this loop.
        await backend.awrite("/sync/hello.txt", "hello world TODO")

        # Each of these previously raised
        # "RuntimeError: got Future attached to a different loop" because
        # `_run_async` reused the cached client across event loops.
        # `read` returns "Error: ..." strings on failure, so check content.
        read_content = await asyncio.to_thread(backend.read, "/sync/hello.txt")
        assert read_content.error is None
        assert read_content.file_data is not None
        assert "hello world TODO" in read_content.file_data["content"]

        assert (await asyncio.to_thread(backend.write, "/sync/two.txt", "data")).error is None
        assert (await asyncio.to_thread(backend.edit, "/sync/hello.txt", "TODO", "DONE")).error is None

        infos = await asyncio.to_thread(backend.ls_info, "/sync")
        assert any(fi.get("path") == "/sync/hello.txt" for fi in infos)

        infos = await asyncio.to_thread(backend.glob_info, "**/*.txt", "/sync")
        assert {fi.get("path") for fi in infos} >= {"/sync/hello.txt", "/sync/two.txt"}

        matches = await asyncio.to_thread(backend.grep_raw, "DONE", "/sync", None)
        assert isinstance(matches, list)
        assert any(m.get("path") == "/sync/hello.txt" for m in matches)

        upload = await asyncio.to_thread(backend.upload_files, [("/sync/three.bin", b"payload")])
        assert upload[0].error is None  # Previously masked as "permission_denied".

        download = await asyncio.to_thread(backend.download_files, ["/sync/three.bin"])
        assert download[0].error is None
        assert download[0].content == b"payload"

        # Async path still works after the sync calls — cache survives.
        recovered = await backend.aread("/sync/hello.txt")
        assert recovered.error is None
        assert recovered.file_data is not None
        assert "hello world DONE" in recovered.file_data["content"]

    async def test_concurrent_sync_wrappers_after_async_init(self, backend):
        # Concurrent sync calls from multiple threads must not corrupt the
        # cached async client or close one another's temporary sync clients.
        await backend.awrite("/concurrent/a.txt", "alpha")
        await backend.awrite("/concurrent/b.txt", "bravo")
        await backend.awrite("/concurrent/c.txt", "charlie")

        results = await asyncio.gather(
            asyncio.to_thread(backend.read, "/concurrent/a.txt"),
            asyncio.to_thread(backend.read, "/concurrent/b.txt"),
            asyncio.to_thread(backend.read, "/concurrent/c.txt"),
        )
        for content, expected in zip(results, ("alpha", "bravo", "charlie"), strict=True):
            assert content.error is None
            assert content.file_data is not None
            assert expected in content.file_data["content"]

        # Cache must still be usable from the original loop afterwards.
        recovered = await backend.aread("/concurrent/a.txt")
        assert recovered.error is None
        assert recovered.file_data is not None
        assert "alpha" in recovered.file_data["content"]
