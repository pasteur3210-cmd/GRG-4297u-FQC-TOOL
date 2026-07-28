from __future__ import annotations

import re
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Callable

from .client import RouterClient, RouterError
from .logging_utils import make_logger
from .models import DeviceStatus
from .reporting import save_excel, save_json


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "_", value.strip())
    return value[:80] or "UNKNOWN"


def make_run_folder(base: Path, identifier: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = base / f"{stamp}_{safe_name(identifier)}"
    suffix = 1
    candidate = folder
    while candidate.exists():
        candidate = Path(f"{folder}_{suffix}")
        suffix += 1
    (candidate / "raw").mkdir(parents=True)
    return candidate


def run_test(
    router_ip: str,
    protocol: str,
    username: str,
    password: str,
    timeout: float,
    output_base: Path,
    identifier: str,
    progress: Callable[[str], None] | None = None,
) -> tuple[Path, DeviceStatus]:
    progress = progress or (lambda _: None)
    run_dir = make_run_folder(output_base, identifier)
    execution_log = make_logger("execution", run_dir / "execution.log")
    test_log = make_logger("test", run_dir / "test.log")
    debug_log = make_logger("debug", run_dir / "debug.log")

    execution_rows: list[dict[str, str]] = []
    test_rows: list[dict[str, str]] = []

    def exec_step(step: str, result: str, message: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_rows.append({"Time": now, "Step": step, "Result": result, "Message": message})
        execution_log.info("%s | %s | %s", step, result, message)
        progress(f"{step}: {message}")

    def test_step(test_id: str, item: str, expected: str, actual: str,
                  result: str, fail_code: str, duration_ms: str) -> None:
        row = {
            "Test ID": test_id, "Item": item, "Expected": expected, "Actual": actual,
            "Result": result, "Fail Code": fail_code, "Duration ms": duration_ms,
        }
        test_rows.append(row)
        test_log.info("%s | %s | expected=%s | actual=%s | %s | %s | %sms",
                      test_id, item, expected, actual, result, fail_code, duration_ms)

    client = RouterClient(
        host=router_ip,
        protocol=protocol,
        timeout=timeout,
        verify_tls=False,
        debug=debug_log.debug,
    )

    metadata = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "router_ip": router_ip,
        "login_result": "FAIL",
        "status_result": "FAIL",
        "overall_result": "FAIL",
        "fail_code": "",
    }
    status = DeviceStatus()

    try:
        exec_step("Program Start", "PASS", "開始Router OQC Status測試")
        debug_log.info("Router=%s protocol=%s username=%s password_provided=%s password_length=%d",
                       router_ip, protocol, username, bool(password), len(password))

        start = perf_counter()
        client.login(username, password)
        elapsed = str(round((perf_counter() - start) * 1000))
        metadata["login_result"] = "PASS"
        test_step("T001", "Authentication", "登入成功", "登入成功", "PASS", "", elapsed)
        exec_step("Authentication", "PASS", "Router登入成功")

        start = perf_counter()
        status, raw_html = client.fetch_status()
        elapsed = str(round((perf_counter() - start) * 1000))
        (run_dir / "raw" / "status_page.html").write_text(raw_html, encoding="utf-8")
        metadata["status_result"] = "PASS"
        test_step("T002", "Status Page", "Device Status頁可取得", "取得成功", "PASS", "", elapsed)
        exec_step("Status Page", "PASS", "已取得並保存status.asp")

        required = [
            ("T003", "Device Name", status.system.get("Device Name", "")),
            ("T004", "Serial Number", status.system.get("Serial Number", "")),
            ("T005", "Firmware Version", status.system.get("Firmware Version", "")),
            ("T006", "LAN MAC", status.lan.get("MAC Address", "")),
        ]
        missing = []
        for test_id, item, value in required:
            result = "PASS" if value else "FAIL"
            fail_code = "" if value else "FIELD_NOT_FOUND"
            test_step(test_id, item, "非空白", value or "<EMPTY>", result, fail_code, "0")
            if not value:
                missing.append(item)

        if missing:
            metadata["fail_code"] = "REQUIRED_FIELD_MISSING"
            metadata["overall_result"] = "FAIL"
            exec_step("Field Validation", "FAIL", "缺少欄位：" + ", ".join(missing))
        else:
            metadata["overall_result"] = "PASS"
            exec_step("Field Validation", "PASS", "必要欄位皆已取得")

        result_payload = {
            "metadata": metadata,
            "status": status.to_dict(),
            "test_log": test_rows,
            "execution_log": execution_rows,
        }
        save_json(run_dir / "result.json", result_payload)
        save_excel(run_dir / "result.xlsx", status, metadata, test_rows, execution_rows)
        exec_step("Report Export", "PASS", "已產生result.json與result.xlsx")

        # Rewrite outputs once more so final execution row is included.
        result_payload["execution_log"] = execution_rows
        save_json(run_dir / "result.json", result_payload)
        save_excel(run_dir / "result.xlsx", status, metadata, test_rows, execution_rows)

        return run_dir, status

    except RouterError as exc:
        metadata["fail_code"] = exc.code
        test_step("T999", "Execution", "成功", str(exc), "FAIL", exc.code, "0")
        exec_step("Execution", "FAIL", f"{exc.code}: {exc}")
        debug_log.error("%s\n%s", exc, traceback.format_exc())
        save_json(run_dir / "result.json", {
            "metadata": metadata,
            "status": status.to_dict(),
            "test_log": test_rows,
            "execution_log": execution_rows,
        })
        save_excel(run_dir / "result.xlsx", status, metadata, test_rows, execution_rows)
        raise
    except Exception as exc:
        metadata["fail_code"] = "UNEXPECTED_ERROR"
        test_step("T999", "Execution", "成功", str(exc), "FAIL", "UNEXPECTED_ERROR", "0")
        exec_step("Execution", "FAIL", f"UNEXPECTED_ERROR: {exc}")
        debug_log.error("%s\n%s", exc, traceback.format_exc())
        save_json(run_dir / "result.json", {
            "metadata": metadata,
            "status": status.to_dict(),
            "test_log": test_rows,
            "execution_log": execution_rows,
        })
        save_excel(run_dir / "result.xlsx", status, metadata, test_rows, execution_rows)
        raise
    finally:
        try:
            client.logout()
        finally:
            client.close()
