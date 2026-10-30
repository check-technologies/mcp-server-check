"""Tests for document tools."""

from __future__ import annotations

from io import BytesIO

import httpx
import pytest
from pypdf import PdfWriter

from mcp_server_check.helpers import DOWNLOAD_TEXT_LIMIT
from mcp_server_check.tools.documents import (
    create_company_provided_document,
    download_company_authorization_document,
    download_company_tax_document,
    download_contractor_tax_document,
    download_employee_tax_document,
    download_setup_document,
    get_company_tax_document,
    list_company_authorization_documents,
    list_company_provided_documents,
    list_company_tax_documents,
    list_contractor_tax_documents,
    list_employee_tax_documents,
    list_setup_documents,
)


@pytest.mark.anyio
async def test_list_company_tax_documents(mock_api, ctx):
    mock_api.get("/documents/company_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctd_001"}]},
        )
    )
    result = await list_company_tax_documents(ctx)
    assert result["results"] == [{"id": "ctd_001"}]


@pytest.mark.anyio
async def test_get_company_tax_document(mock_api, ctx):
    mock_api.get("/documents/company_tax_documents/ctd_001").mock(
        return_value=httpx.Response(200, json={"id": "ctd_001"})
    )
    result = await get_company_tax_document(ctx, document_id="ctd_001")
    assert result["id"] == "ctd_001"


@pytest.mark.anyio
async def test_list_employee_tax_documents(mock_api, ctx):
    mock_api.get("/documents/employee_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "etd_001"}]},
        )
    )
    result = await list_employee_tax_documents(ctx)
    assert result["results"] == [{"id": "etd_001"}]


@pytest.mark.anyio
async def test_list_setup_documents(mock_api, ctx):
    mock_api.get("/documents/setup_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sd_001"}]},
        )
    )
    result = await list_setup_documents(ctx)
    assert result["results"] == [{"id": "sd_001"}]


@pytest.mark.anyio
async def test_list_company_tax_documents_with_filters(mock_api, ctx):
    mock_api.get("/documents/company_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctd_001"}]},
        )
    )
    result = await list_company_tax_documents(
        ctx, company="com_123", year=2025, quarter="Q1"
    )
    assert result["results"] == [{"id": "ctd_001"}]
    req = mock_api.get("/documents/company_tax_documents").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["year"] == "2025"
    assert req.url.params["quarter"] == "Q1"


@pytest.mark.anyio
async def test_list_company_authorization_documents_with_filters(mock_api, ctx):
    mock_api.get("/documents/company_authorization_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cad_001"}]},
        )
    )
    result = await list_company_authorization_documents(
        ctx, company="com_123", year=2025
    )
    assert result["results"] == [{"id": "cad_001"}]
    req = mock_api.get("/documents/company_authorization_documents").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_list_employee_tax_documents_with_filters(mock_api, ctx):
    mock_api.get("/documents/employee_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "etd_001"}]},
        )
    )
    result = await list_employee_tax_documents(
        ctx, employee="emp_123", company="com_456", year=2025
    )
    assert result["results"] == [{"id": "etd_001"}]
    req = mock_api.get("/documents/employee_tax_documents").calls.last.request
    assert req.url.params["employee"] == "emp_123"
    assert req.url.params["company"] == "com_456"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_list_contractor_tax_documents_with_filters(mock_api, ctx):
    mock_api.get("/documents/contractor_tax_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctd_001"}]},
        )
    )
    result = await list_contractor_tax_documents(
        ctx, contractor="ctr_123", company="com_456", year=2025
    )
    assert result["results"] == [{"id": "ctd_001"}]
    req = mock_api.get("/documents/contractor_tax_documents").calls.last.request
    assert req.url.params["contractor"] == "ctr_123"
    assert req.url.params["company"] == "com_456"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_list_setup_documents_with_filters(mock_api, ctx):
    mock_api.get("/documents/setup_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sd_001"}]},
        )
    )
    result = await list_setup_documents(ctx, company="com_123")
    assert result["results"] == [{"id": "sd_001"}]
    req = mock_api.get("/documents/setup_documents").calls.last.request
    assert req.url.params["company"] == "com_123"


@pytest.mark.anyio
async def test_list_company_provided_documents_with_filters(mock_api, ctx):
    mock_api.get("/company_provided_documents").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cpd_001"}]},
        )
    )
    result = await list_company_provided_documents(ctx, company="com_123")
    assert result["results"] == [{"id": "cpd_001"}]
    req = mock_api.get("/company_provided_documents").calls.last.request
    assert req.url.params["company"] == "com_123"


@pytest.mark.anyio
async def test_create_company_provided_document(mock_api, ctx):
    mock_api.post("/company_provided_documents").mock(
        return_value=httpx.Response(201, json={"id": "cpd_new"})
    )
    result = await create_company_provided_document(ctx, company="com_001")
    assert result["id"] == "cpd_new"


# --- Downloads ---


def _pdf_with_text(pages: list[str]) -> bytes:
    """A minimal PDF, one page per entry, each drawing its text in Helvetica."""
    objects: list[bytes] = []
    page_count = len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(page_count))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode())
    font_number = 3 + 2 * page_count
    for i, text in enumerate(pages):
        content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {4 + 2 * i} 0 R "
            f"/Resources << /Font << /F1 {font_number} 0 R >> >> >>".encode()
        )
        objects.append(
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


def _blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _setup_document(document_type: str) -> httpx.Response:
    return httpx.Response(
        200, json={"id": "sd_001", "document_type": document_type, "label": "x"}
    )


@pytest.mark.anyio
async def test_download_setup_document_reads_pdf_text(mock_api, ctx):
    mock_api.get("/documents/setup_documents/sd_001").mock(
        return_value=_setup_document("hld_report")
    )
    download = mock_api.get("/documents/setup_documents/sd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=_pdf_with_text(["Hello HLD report", "Second page"]),
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="hld_report.pdf"',
            },
        )
    )
    result = await download_setup_document(ctx, document_id="sd_001")
    assert not result.get("error")
    assert result["content_type"] == "application/pdf"
    assert result["filename"] == "hld_report.pdf"
    assert result["pages"] == 2
    assert result["truncated"] is False
    assert "--- page 1 ---" in result["text"]
    assert "Hello HLD report" in result["text"]
    assert "--- page 2 ---" in result["text"]
    assert "Second page" in result["text"]
    assert download.call_count == 1


@pytest.mark.anyio
async def test_download_setup_document_refuses_sensitive_types(mock_api, ctx):
    mock_api.get("/documents/setup_documents/sd_001").mock(
        return_value=_setup_document("sensitive_employee_setup")
    )
    download = mock_api.get("/documents/setup_documents/sd_001/download").mock(
        return_value=httpx.Response(
            200, content=b"ssn,account\n", headers={"content-type": "text/csv"}
        )
    )
    result = await download_setup_document(ctx, document_id="sd_001")
    assert result["error"] is True
    assert result["document_type"] == "sensitive_employee_setup"
    assert "unmasked SSNs" in result["detail"]
    assert "get_setup_document" in result["detail"]
    assert download.call_count == 0


@pytest.mark.anyio
async def test_download_setup_document_passes_metadata_errors_through(mock_api, ctx):
    mock_api.get("/documents/setup_documents/sd_404").mock(
        return_value=httpx.Response(404, json={"detail": "Not found."})
    )
    download = mock_api.get("/documents/setup_documents/sd_404/download")
    result = await download_setup_document(ctx, document_id="sd_404")
    assert result["error"] is True
    assert result["status_code"] == 404
    assert download.call_count == 0


@pytest.mark.anyio
async def test_download_csv_returns_text(mock_api, ctx):
    mock_api.get("/documents/company_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=b"tax,amount\nfed,100.00\n",
            headers={"content-type": "text/csv; charset=utf-8"},
        )
    )
    result = await download_company_tax_document(ctx, document_id="ctd_001")
    assert result == {
        "content_type": "text/csv",
        "filename": None,
        "text": "tax,amount\nfed,100.00\n",
        "truncated": False,
    }


@pytest.mark.anyio
async def test_download_json_body_is_passed_through(mock_api, ctx):
    mock_api.get("/documents/employee_tax_documents/etd_001/download").mock(
        return_value=httpx.Response(200, json={"url": "https://files.example/w2.pdf"})
    )
    result = await download_employee_tax_document(ctx, document_id="etd_001")
    assert result == {"url": "https://files.example/w2.pdf"}


@pytest.mark.anyio
async def test_download_unreadable_content_type_is_an_error(mock_api, ctx):
    mock_api.get("/documents/contractor_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=b"PK\x03\x04" + b"0" * 60,
            headers={"content-type": "application/zip"},
        )
    )
    result = await download_contractor_tax_document(ctx, document_id="ctd_001")
    assert result["error"] is True
    assert result["content_type"] == "application/zip"
    assert result["size_bytes"] == 64
    assert "application/zip" in result["detail"]


@pytest.mark.anyio
async def test_download_long_text_is_truncated_with_a_note(mock_api, ctx):
    body = "row,value\n" * (DOWNLOAD_TEXT_LIMIT // 5)
    assert len(body) > DOWNLOAD_TEXT_LIMIT
    mock_api.get("/documents/company_authorization_documents/cad_001/download").mock(
        return_value=httpx.Response(
            200, content=body.encode(), headers={"content-type": "text/plain"}
        )
    )
    result = await download_company_authorization_document(ctx, document_id="cad_001")
    assert result["truncated"] is True
    assert len(result["text"]) == DOWNLOAD_TEXT_LIMIT
    assert f"{len(body):,}" in result["note"]
    assert "omitted" in result["note"]


@pytest.mark.anyio
async def test_download_pdf_is_truncated_by_whole_pages(mock_api, ctx):
    page = "x" * (DOWNLOAD_TEXT_LIMIT // 2)
    mock_api.get("/documents/company_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=_pdf_with_text([page, page, page]),
            headers={"content-type": "application/pdf"},
        )
    )
    result = await download_company_tax_document(ctx, document_id="ctd_001")
    assert result["pages"] == 3
    assert result["truncated"] is True
    assert "--- page 1 ---" in result["text"]
    assert "--- page 2 ---" not in result["text"]
    assert len(result["text"]) <= DOWNLOAD_TEXT_LIMIT
    assert "Showing 1 of 3 pages" in result["note"]


@pytest.mark.anyio
async def test_download_pdf_single_page_over_the_limit_is_flagged(mock_api, ctx):
    """A one-page PDF longer than the limit is cut, and must say so."""
    page = "y" * (DOWNLOAD_TEXT_LIMIT + 10)
    mock_api.get("/documents/company_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=_pdf_with_text([page]),
            headers={"content-type": "application/pdf"},
        )
    )
    result = await download_company_tax_document(ctx, document_id="ctd_001")
    assert result["pages"] == 1
    assert result["truncated"] is True
    assert len(result["text"]) == DOWNLOAD_TEXT_LIMIT
    assert "Page 1 alone is over" in result["note"]


@pytest.mark.anyio
async def test_download_pdf_without_text_layer_is_an_error(mock_api, ctx):
    mock_api.get("/documents/setup_documents/sd_001").mock(
        return_value=_setup_document("payroll_journal")
    )
    mock_api.get("/documents/setup_documents/sd_001/download").mock(
        return_value=httpx.Response(
            200, content=_blank_pdf(), headers={"content-type": "application/pdf"}
        )
    )
    result = await download_setup_document(ctx, document_id="sd_001")
    assert result["error"] is True
    assert result["pages"] == 1
    assert "no text layer" in result["detail"]


@pytest.mark.anyio
async def test_download_broken_pdf_is_an_error(mock_api, ctx):
    mock_api.get("/documents/company_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=b"%PDF-1.4 garbage",
            headers={"content-type": "application/pdf"},
        )
    )
    result = await download_company_tax_document(ctx, document_id="ctd_001")
    assert result["error"] is True
    assert "Could not parse the PDF" in result["detail"]


@pytest.mark.anyio
async def test_download_filename_from_rfc5987_disposition(mock_api, ctx):
    mock_api.get("/documents/company_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200,
            content=b"a,b\n",
            headers={
                "content-type": "text/csv",
                "content-disposition": "attachment; filename*=UTF-8''Q1%20941.csv",
            },
        )
    )
    result = await download_company_tax_document(ctx, document_id="ctd_001")
    assert result["filename"] == "Q1 941.csv"


@pytest.mark.anyio
async def test_download_does_not_demand_json(mock_api, ctx):
    route = mock_api.get("/documents/company_tax_documents/ctd_001/download").mock(
        return_value=httpx.Response(
            200, content=b"a,b\n", headers={"content-type": "text/csv"}
        )
    )
    await download_company_tax_document(ctx, document_id="ctd_001")
    accept = route.calls.last.request.headers.get("accept", "")
    assert "application/json" not in accept
