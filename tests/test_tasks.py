from datetime import timezone, datetime
from pathlib import Path

import sys
from typing import List
from unittest import TestCase, mock

from boefjes.job_models import BoefjeMeta
from boefjes.job_handler import BoefjeHandler
from boefjes.katalogus.local_repository import LocalPluginRepository
from boefjes.katalogus.models import Boefje, Normalizer, Bit, PluginType

from boefjes.local import LocalBoefjeJobRunner

MOCKED_NOW = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


class TaskTest(TestCase):
    def setUp(self) -> None:
        self.boefjes = [
            Boefje(
                id="test-boefje-1",
                repository_id="",
                consumes={"SomeOOI"},
                produces=["test-boef-1", "test/text"],
            ),
            Boefje(
                id="test-boefje-2",
                repository_id="",
                consumes={"SomeOOI"},
                produces=["test-boef-2", "test/text"],
            ),
            Boefje(
                id="test-boefje-3",
                repository_id="",
                consumes={"SomeOOI"},
                produces=["test-boef-3", "test/plain"],
            ),
            Boefje(
                id="test-boefje-4",
                repository_id="",
                consumes={"SomeOOI"},
                produces=["test-boef-4", "test/and-simple"],
            ),
        ]
        self.normalizers = [
            Normalizer(
                id="test-normalizer-1",
                repository_id="",
                consumes=["test-boef-3", "test/text"],
                produces=["SomeOOI", "OtherOOI"],
            ),
            Normalizer(
                id="test-normalizer-2",
                repository_id="",
                consumes=["test/text"],
                produces=["SomeOtherOOI"],
            ),
        ]
        self.bits = [
            Bit(
                id="test-bit-1",
                repository_id="",
                consumes="SomeOOI",
                produces=["SomeOOI"],
                parameters=[],
            ),
            Bit(
                id="test-bit-2",
                repository_id="",
                consumes="SomeOOI",
                produces=["SomeOOI", "SomeOtherOOI"],
                parameters=[],
            ),
        ]
        self.plugins: List[PluginType] = self.boefjes + self.normalizers + self.bits
        sys.path.append(str(Path(__file__).parent))

    def _get_boefje_meta(self):
        return BoefjeMeta(
            id="c188ef6b-b756-4cb0-9cb2-0db776e3cce3",
            boefje={"id": "test-boefje-1", "version": "9"},
            input_ooi="Hostname|internet|example.com",
            arguments={},
            organization="_dev",
        ).copy()

    @mock.patch("boefjes.job_handler.now", return_value=MOCKED_NOW)
    @mock.patch("boefjes.job_handler.get_environment_settings", return_value={})
    @mock.patch("boefjes.job_handler.bytes_api_client")
    @mock.patch("boefjes.job_handler._find_ooi_in_past")
    def test_handle_boefje_with_exception(self, mock_find_ooi_in_past, mock_bytes_api_client, mock_get_env, mock_now):
        meta = BoefjeMeta(
            id="some-random-job-id",
            boefje={"id": "dummy_boefje_runtime_exception"},
            input_ooi="Network|internet",
            arguments={},
            organization="_dev",
        )

        local_repository = LocalPluginRepository(Path(__file__).parent / "modules")
        BoefjeHandler(LocalBoefjeJobRunner(local_repository), local_repository).handle(meta)

        expected_meta = meta.copy()
        expected_meta.ended_at = MOCKED_NOW

        mock_bytes_api_client.save_boefje_meta.assert_called_once_with(expected_meta)

        save_raw_call = mock_bytes_api_client.save_raw.call_args_list[0][0]

        self.assertEqual("some-random-job-id", save_raw_call[0])
        self.assertIn("Traceback", save_raw_call[1])
        self.assertEqual(
            {
                "error/boefje",
                "dummy_boefje_runtime_exception",
                "boefje/dummy_boefje_runtime_exception",
                f"boefje/dummy_boefje_runtime_exception-{meta.parameterized_arguments_hash}",
            },
            save_raw_call[2],
        )
