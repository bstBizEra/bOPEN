"""
Phase 3 Unit Acceptance Suite — Capability & Module Registry (BOPEN-MOD-001 / WP-P3-02 & WP-P3-03).

Verifies capability registration, module manifest validation, dependency resolution,
and global catalog vs tenant context lifecycle rules.
"""

import unittest
from pathlib import Path
import json

from kernel_core.types import ContextPayload

# Capability & Module Registry imports
from kernel_core.capability import (
    CapabilityRegistry,
    ModuleManifest,
    CapabilityStatus,
    ModuleStatus,
    InvalidModuleManifestError,
    CapabilityNotFoundError,
    DependencyResolutionError,
)

ROOT = Path(__file__).resolve().parents[2]


class CapabilityRegistryUnitTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.valid_manifest_data = {
            "module_id": "mod_practice_mgmt",
            "name": "Practice Management",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_invoice_create", "cap_invoice_read"],
            "resources": ["res_invoice"],
            "dependencies": []
        }
        self.valid_context = ContextPayload(
            context_id="ctx_123",
            principal_id="usr_alice",
            tenant_id="tnt_alpha",
            active_membership_id="mem_alice_alpha",
            roles=["member"]
        )

    def test_register_module_manifest_success(self):
        manifest = ModuleManifest.from_dict(self.valid_manifest_data)
        registered = self.registry.register_module(manifest)
        self.assertEqual(registered.status, ModuleStatus.REGISTERED)
        self.assertEqual(registered.module_id, "mod_practice_mgmt")

    def test_validate_and_approve_module(self):
        manifest = ModuleManifest.from_dict(self.valid_manifest_data)
        self.registry.register_module(manifest)
        validated = self.registry.validate_module("mod_practice_mgmt")
        self.assertEqual(validated.status, ModuleStatus.VALIDATED)
        
        approved = self.registry.approve_module("mod_practice_mgmt")
        self.assertEqual(approved.status, ModuleStatus.APPROVED)
        self.assertTrue(self.registry.is_available("mod_practice_mgmt"))

    def test_unregistered_capability_lookup_fails_closed(self):
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.resolve_capability("cap_unregistered")

    def test_missing_dependency_fails_resolution(self):
        dependent_manifest_data = {
            "module_id": "mod_analytics",
            "name": "Analytics",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_analytics_export"],
            "resources": ["res_analytics"],
            "dependencies": ["mod_nonexistent"]
        }
        manifest = ModuleManifest.from_dict(dependent_manifest_data)
        self.registry.register_module(manifest)
        with self.assertRaises(DependencyResolutionError):
            self.registry.validate_module("mod_analytics")

    def test_capability_lookup_requires_validated_context(self):
        manifest = ModuleManifest.from_dict(self.valid_manifest_data)
        self.registry.register_module(manifest)
        self.registry.validate_module("mod_practice_mgmt")
        self.registry.approve_module("mod_practice_mgmt")

        # Context missing tenant_id fails
        invalid_context = ContextPayload(
            context_id="ctx_invalid",
            principal_id="usr_alice",
            tenant_id="",
            active_membership_id="mem_alice",
            roles=[]
        )
        with self.assertRaises(ValueError):
            self.registry.get_tenant_capabilities(invalid_context, "mod_practice_mgmt")


if __name__ == "__main__":
    unittest.main()
