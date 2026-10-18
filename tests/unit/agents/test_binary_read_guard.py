"""Tests for BinaryReadGuardMiddleware."""

from __future__ import annotations

from octop.infra.agents.middleware.binary_read_guard import read_file_block_reason


def test_blocks_inbound_pdf() -> None:
    reason = read_file_block_reason("inbound/01KWB9MG2Z570P7QB367KDJ75R.pdf")
    assert reason is not None
    assert "pdf" in reason.lower()
    assert "execute_shell_command" in reason


def test_allows_inbound_txt() -> None:
    assert read_file_block_reason("inbound/01JTEST.txt") is None


def test_blocks_pdf_anywhere() -> None:
    assert read_file_block_reason("docs/report.pdf") is not None


def test_allows_image_anywhere() -> None:
    """Images reach the model as multimodal blocks (deepagents handles capability)."""
    assert read_file_block_reason("generated/scene/frames/frame_0001.png") is None
    assert read_file_block_reason("notes/photo.jpeg") is None
    assert read_file_block_reason("a.webp") is None


def test_allows_inbound_image() -> None:
    assert read_file_block_reason("inbound/01KWB9MG2Z570P7QB367KDJ75R.png") is None


def test_blocks_non_image_binaries() -> None:
    assert read_file_block_reason("archive.zip") is not None
    assert read_file_block_reason("deck.pptx") is not None
    assert read_file_block_reason("inbound/blob.bin") is not None
